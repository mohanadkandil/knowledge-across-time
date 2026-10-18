"""Offline regressions: empty layout output cannot become fabricated evidence."""
from types import SimpleNamespace

import pytest

from kat.archive import build_archive, latex_document
from kat.config import Settings
from kat.engine import Engine, answer_source_ids
from kat.services import Models, parsed_content
from kat.util import load_json, write_json


@pytest.fixture
def empty_page_engine(tmp_path, monkeypatch):
    settings=Settings(_env_file=None,data_dir=tmp_path)
    engine=Engine(settings)
    page={"page_id":"bri-0015-fixture","row_index":15,"metadata":"Fixture scan, not visual evidence",
          "sha256":"a"*64,"revision":"b"*40,"image_file":str(tmp_path/'source.jpg'),
          "source_url":"https://example.invalid/source","label":1}
    (tmp_path/'source.jpg').write_bytes(b'offline fixture')
    # Preserve the selection denominator even when this one extraction is empty.
    pages=[page]+[{**page,"page_id":f"bri-{i:04d}-pending","row_index":i} for i in range(99)]
    write_json(tmp_path/'britannica/manifest.json',{"pages":pages,"selection_method":"synthetic 100-page test selection"})
    parsed=parsed_content('<x_0><y_0><x_0.998><y_0.9984><class_Picture>')
    parsed.update(parse_model=settings.parse_model,image_sha256=page['sha256'],page_id=page['page_id'])
    write_json(engine.page_dir(page['page_id'])/'parse.json',parsed)
    def forbidden(*args,**kwargs):
        raise AssertionError('Empty parsed text must not trigger a model, retrieval, or indexing request')
    for method in ['post','parse','chat','embed','rerank']:
        monkeypatch.setattr(Models,method,forbidden)
    engine.wiki=SimpleNamespace(search=forbidden,fetch=forbidden,stats=lambda:{'offline_fixture':True})
    return engine,page,parsed


def test_picture_only_layout_is_valid_but_empty_text_output_is_not():
    raw='<x_0><y_0><x_1><y_1><class_Picture>'
    parsed=parsed_content(raw)
    assert parsed['text']=='' and parsed['raw']==raw
    assert parsed['readable_text'] is False and parsed['extraction_status']=='layout_only'
    assert parsed['regions'][0]['bbox_raw']==[0.,0.,1.,1.]
    assert 'does not establish' in parsed['note']
    for malformed in ['', '<x_0><y_0><x_1><y_1><class_Text>', '<div></div>']:
        with pytest.raises(ValueError,match='readable text'):
            parsed_content(malformed)


def test_blank_match_and_compare_abstain_without_any_live_request(empty_page_engine):
    engine,page,parsed=empty_page_engine
    original=(engine.page_dir(page['page_id'])/'parse.json').read_bytes()
    # An explicit manual query must not turn missing historical evidence into a match.
    matched=engine.match(page['page_id'],queries=['electricity'])
    assert matched['status']=='unmatched' and matched['matches']==[]
    assert matched['retrieval_attempted'] is False and matched['queries']==[]
    assert matched['requested_queries']==['electricity']
    assert matched['historical_source']['sha256']==page['sha256']
    # A stale fabricated result must be replaced by a visible abstention.
    write_json(engine.page_dir(page['page_id'])/'comparison.json',{'comparison':{'summary':'stale'}})
    result=engine.compare(page['page_id'])
    assert result['abstained'] and result['model'] is None and result['source_ids']==[]
    assert result['comparison']['matches']==result['comparison']['differences']==[]
    run=load_json(engine.root/'runs'/result['run_id']/'run.json')
    assert run['status']=='abstained' and run['execution']=='deterministic_abstention'
    assert run['model_calls']==[] and engine.store.cases()['cases']==[]
    assert (engine.page_dir(page['page_id'])/'parse.json').read_bytes()==original
    status=engine.status()
    assert status['pages_selected']==100 and status['pages_parsed']==1
    assert status['pages_readable']==0 and status['pages_without_readable_text']==1
    assert status['pages_abstained']==1 and status['pages_compared']==0
    row=engine.pages()[0]
    assert row['parsed'] and not row['readable_text'] and row['comparison_abstained'] and not row['compared']


def test_blank_archive_distinguishes_output_from_readable_extraction(empty_page_engine, monkeypatch):
    engine,page,parsed=empty_page_engine
    monkeypatch.setattr('kat.archive.shutil.which',lambda name:None)
    report=build_archive(engine)
    assert report['selected']==100 and report['parsed']==1
    assert report['readable']==0 and report['no_readable_text']==1
    html=(engine.root/'site/pages'/(page['page_id']+'.html')).read_text()
    assert 'No readable text was extracted' in html and 'does not establish' in html
    assert '100 fixed source scans' in (engine.root/'site/index.html').read_text()
    assert 'layout-only parser output' in latex_document(page,parsed)


def test_bracket_citations_support_prefix_grouping_backticks_and_deduplication():
    old='bri-0057-abcdef123456:region-0:0';new='wiki-51420-1351882362-abcdef'
    answer=f'Observation [source_id: `{old}`]. Comparison [{old}, `{new}`]. Bare wiki-not-a-citation.'
    assert answer_source_ids(answer)==[old,new]
    assert answer_source_ids('An uncited answer. [1] [source_id]')==[]


@pytest.mark.parametrize('answer,expected_count,status',[
    ('Supported observation [source_id: `bri-0015-fixture:region-0:0`].',1,'source_ids_resolved'),
    ('Answer without citations.',0,'unverified'),
    ('Answer [wiki-unknown-article].',1,'unverified'),
])
def test_hermes_answer_citations_are_explicit_and_validated(empty_page_engine,monkeypatch,answer,expected_count,status):
    engine,_,_=empty_page_engine
    engine.store.put_sources([{'id':'bri-0015-fixture:region-0:0','kind':'britannica','text':'synthetic offline evidence'}])
    monkeypatch.setattr('kat.engine.run_hermes',lambda *args,**kwargs:{'answer':answer,'completed':True,'framework':'hermes'})
    run=engine.ask('Offline adapter test')
    assert run['citation_count']==expected_count and run['citation_status']==status
    assert 'reviewer inspection' in run['citation_note']
    if expected_count:assert run['citation_checks'][0]['exists']==(status=='source_ids_resolved')


def test_page_context_is_readable_without_claiming_scan_pixels(empty_page_engine,monkeypatch):
    engine,page,parsed=empty_page_engine
    parsed['text']='Synthetic page transcription, not an original-image reading.'
    write_json(engine.page_dir(page['page_id'])/'parse.json',parsed)
    def hermes(*args,**kwargs):
        source=kwargs['read'](page['page_id'])
        assert source['text']==parsed['text']
        assert source['delivered_content']=='text_only'
        assert source['original_scan_pixels_included'] is False
        return {'answer':f"Page evidence [{page['page_id']}].",'completed':True,'framework':'hermes'}
    monkeypatch.setattr('kat.engine.run_hermes',hermes)
    run=engine.ask('Offline page citation check',page_id=page['page_id'])
    assert run['citation_count']==1 and run['citation_status']=='source_ids_resolved'
    assert engine.store.source(page['page_id'])['modality']=='page_text'
    assert engine.store.stats()['embedding_identity'] is None
