"""Native plugin/profile contracts; fixture calls do not count as agent cases."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from kat.config import Settings
from kat.hermes_bridge import HERMES_COMMIT
from kat.hermes_native import dispatch_tool, prepare_native, tool_schemas
from kat.util import write_json


def test_profile_uses_environment_key_and_preserves_existing_configuration(tmp_path,monkeypatch):
    checkout=tmp_path/'hermes-source';checkout.mkdir();(checkout/'run_agent.py').write_text('# fixture')
    bin_dir=tmp_path/'venv/bin';bin_dir.mkdir(parents=True)
    for name in ['python','hermes']:(bin_dir/name).write_text('# fixture')
    monkeypatch.setattr('kat.hermes_native.subprocess.check_output',lambda *a,**k:HERMES_COMMIT+'\n')
    secret='FAKE-NATIVE-TEST-CREDENTIAL'
    settings=Settings(_env_file=None,data_dir=tmp_path/'data',hermes_repo_path=str(checkout),
                      hermes_python=str(bin_dir/'python'),token_factory_api_key=secret)
    binary,home,env=prepare_native(settings)
    assert binary==bin_dir/'hermes' and env['SUPER_API_KEY']==secret
    assert env['KAT_BRIDGE_PYTHON'] and env['KAT_DATA_DIR']==str(settings.data_dir.resolve())
    cfg=json.loads((home/'config.yaml').read_text())
    assert cfg['model']['default']==settings.nemotron_agent_model
    assert cfg['plugins']['enabled']==['kat-comparison']
    assert cfg['platform_toolsets']['cli']==['kat_corpus']
    for path in home.rglob('*'):
        if path.is_file():assert secret not in path.read_text()
    (home/'config.yaml').write_text('{"user_edited":true}')
    prepare_native(settings)
    assert json.loads((home/'config.yaml').read_text())=={'user_edited':True}
    unmanaged=tmp_path/'existing';unmanaged.mkdir();(unmanaged/'config.yaml').write_text('{}')
    with pytest.raises(ValueError,match='unmanaged'):prepare_native(settings,profile=unmanaged)


def test_native_plugin_registers_only_declared_corpus_tools(tmp_path,monkeypatch):
    from kat import native_plugin
    write_json(tmp_path/'tools.json',tool_schemas())
    monkeypatch.setattr(native_plugin,'__file__',str(tmp_path/'__init__.py'))
    registrations=[]
    native_plugin.register(SimpleNamespace(register_tool=lambda **kwargs:registrations.append(kwargs)))
    assert {r['name'] for r in registrations}=={'search_sources','read_source','compare_page','browse_corpus'}
    assert {r['toolset'] for r in registrations}=={'kat_corpus'}
    assert all(callable(r['handler']) for r in registrations)


def test_browse_corpus_filters_and_pages_without_model_calls(tmp_path):
    engine=SimpleNamespace(pages=lambda:[{'page_id':f'bri-{i}','row_index':i,'metadata':'Cloud volume','excerpt':'vapours'} for i in range(3)],
                           page_dir=lambda page:tmp_path/page)
    result=dispatch_tool(engine,'browse_corpus',{'filter':'vapours','limit':2})
    assert result['selected_pages']==3 and result['matching_pages']==3
    assert len(result['pages'])==2 and result['next_offset']==2
    assert dispatch_tool(engine,'browse_corpus',{'filter':'absent'})['pages']==[]
    write_json(tmp_path/'bri-1/parse.json',{'text':'A relevant passage near the end of the page.'})
    assert dispatch_tool(engine,'browse_corpus',{'filter':'relevant passage'})['pages'][0]['page_id']=='bri-1'
    with pytest.raises(ValueError):dispatch_tool(engine,'arbitrary_command',{})
    with pytest.raises(ValueError):dispatch_tool(engine,'search_sources',{'query':'x'*2001})


def test_native_handler_uses_fixed_worker_argv_and_returns_structured_errors(monkeypatch):
    from kat.native_plugin import handler_for
    monkeypatch.setenv('KAT_BRIDGE_PYTHON','/fixture/python')
    monkeypatch.setenv('KAT_PROJECT_ROOT','/fixture/project')
    calls=[]
    def run(args,**kwargs):
        calls.append((args,kwargs));return SimpleNamespace(returncode=0,stdout='{"count":100}')
    monkeypatch.setattr('kat.native_plugin.subprocess.run',run)
    assert json.loads(handler_for('browse_corpus')({'filter':'$(not-a-command)'}))=={'count':100}
    args,kwargs=calls[0]
    assert args==['/fixture/python','-m','kat.hermes_native','--tool']
    assert json.loads(kwargs['input'])['arguments']['filter']=='$(not-a-command)'
    assert 'shell' not in kwargs
    monkeypatch.setattr('kat.native_plugin.subprocess.run',lambda *a,**k:SimpleNamespace(returncode=1,stdout='',stderr='private error'))
    assert json.loads(handler_for('browse_corpus')({}))['exit_code']==1
