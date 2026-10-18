"""Launch the native interactive Hermes CLI with the project corpus plugin."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from .config import Settings
from .corpus import find_page
from .engine import Engine
from .hermes_bridge import HERMES_COMMIT, _SYSTEM, _TOOLS
from .util import digest, load_json, now, write_json

NATIVE_SYSTEM=_SYSTEM+'\nUse browse_corpus when asked what data is available. Use only the kat_corpus tools for source claims. Cite exact bri-/wiki- passage IDs, never generated compare- run IDs.\n'

def tool_schemas():
    schemas={name:{'name':name,**definition} for name,definition in _TOOLS.items()}
    schemas['browse_corpus']={
        'name':'browse_corpus','description':'List the saved historical pages and OCR excerpts, or inspect corpus counts. Use this to discover available topics and page IDs. This is not BERTopic clustering.',
        'parameters':{'type':'object','properties':{
            'filter':{'type':'string','maxLength':200},
            'offset':{'type':'integer','minimum':0,'maximum':10000},
            'limit':{'type':'integer','minimum':1,'maximum':100}},
            'additionalProperties':False}}
    return schemas


def dispatch_tool(engine, name, args):
    if name not in tool_schemas() or not isinstance(args,dict):raise ValueError('Unknown corpus tool or invalid arguments')
    if name=='search_sources':
        query=args.get('query','')
        if not isinstance(query,str) or not query.strip() or len(query)>2000:raise ValueError('Search query must contain 1–2000 characters')
        return engine.search(query,limit=max(1,min(12,int(args.get('limit',6)))))
    if name=='read_source':
        sid=args.get('source_id','')
        if not isinstance(sid,str) or not sid or len(sid)>500:raise ValueError('Invalid source ID')
        try:source=engine.store.source(sid)
        except KeyError:
            page=find_page(engine.root,sid);parsed=load_json(engine.page_dir(page['page_id'])/'parse.json')
            if not parsed:raise ValueError('This historical page has no completed parser output')
            source={'id':page['page_id'],'kind':'britannica','page_id':page['page_id'],
                    'title':page['metadata'],'text':parsed['text'],'url':page['source_url'],
                    'modality':'page_text','parse_model':parsed['parse_model'],'provenance':page}
            engine.store.put_sources([source])
        result={k:v for k,v in source.items() if k not in {'references','provenance'}}
        result.update(delivered_content='text_only',original_scan_pixels_included=False,
                      evidence_note='Historical text is unverified OCR. An :image ID is an image-vector record; no scan pixels are delivered by this tool.')
        return result
    if name=='compare_page':
        page=find_page(engine.root,str(args.get('page','')))
        return load_json(engine.page_dir(page['page_id'])/'comparison.json') or engine.compare(page['page_id'])
    offset=max(0,min(10000,int(args.get('offset',0))));limit=max(1,min(100,int(args.get('limit',20))))
    query=str(args.get('filter',''))[:200].casefold()
    pages=engine.pages()
    filtered=[]
    for page in pages:
        text=' '.join(str(page.get(k,'')) for k in ['metadata','excerpt','row_index','page_id'])
        if query and query not in text.casefold():
            parsed=load_json(engine.page_dir(page['page_id'])/'parse.json',{})
            text=parsed.get('text','')
        if query in text.casefold():filtered.append(page)
    return {'selected_pages':len(pages),'matching_pages':len(filtered),'offset':offset,'limit':limit,
            'pages':[{k:p.get(k) for k in ['page_id','row_index','metadata','excerpt','readable_text','compared','comparison_abstained']} for p in filtered[offset:offset+limit]],
            'next_offset':offset+limit if offset+limit<len(filtered) else None,
            'note':'Saved scans and machine-text excerpts, not a complete entry catalog or topic clusters.'}


def prepare_native(settings, profile=None):
    root=Path(__file__).resolve().parents[2]
    checkout=Path(settings.hermes_repo_path).expanduser().resolve()
    python=Path(settings.hermes_python).expanduser().resolve()
    if not settings.hermes_repo_path or not (checkout/'run_agent.py').is_file() or not python.is_file():
        raise ValueError('Configure HERMES_REPO_PATH and HERMES_PYTHON first; see docs/hermes.md')
    commit=subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
    if commit!=HERMES_COMMIT:raise ValueError('Hermes checkout differs from the pinned commit')
    executable=Path(settings.hermes_python).expanduser().absolute().parent/'hermes'
    if not executable.is_file():raise ValueError('Native hermes executable is missing beside HERMES_PYTHON')
    if not settings.token_factory_api_key.get_secret_value():raise ValueError('Configure SUPER_API_KEY in .env')
    home=Path(profile or settings.data_dir/'hermes-cli').resolve();home.mkdir(parents=True,exist_ok=True);home.chmod(0o700)
    config_path=home/'config.yaml';marker=home/'kat-profile.json';prior=load_json(marker,{})
    if config_path.exists() and not prior:raise ValueError('Existing Hermes profile is unmanaged; choose a new profile directory')
    config={
        'providers':{'tokenfactory-super':{'api':settings.token_factory_base_url,'key_env':'SUPER_API_KEY',
            'transport':'chat_completions','default_model':settings.nemotron_agent_model,
            'extra_body':{'chat_template_kwargs':{'enable_thinking':False},'max_tokens':4096}}},
        'model':{'provider':'custom:tokenfactory-super','default':settings.nemotron_agent_model,'supports_vision':True},
        'model_overrides':{'custom:tokenfactory-super':{settings.nemotron_agent_model:{'supports_tools':True,'supports_vision':True}}},
        'plugins':{'enabled':['kat-comparison']},'platform_toolsets':{'cli':['kat_corpus']},
        'tools':{'tool_search':{'enabled':'off'}},
        'agent':{'max_turns':12,'run_budget_seconds':180},
        'memory':{'memory_enabled':False,'user_profile_enabled':False},
        'auxiliary':{'title_generation':{'enabled':False}},'display':{'interface':'cli'}}
    if not config_path.exists():
        config_path.write_text(json.dumps(config,indent=2)+'\n');config_path.chmod(0o600)
        (home/'SOUL.md').write_text(NATIVE_SYSTEM)
    plugin=home/'plugins'/'kat-comparison';plugin.mkdir(parents=True,exist_ok=True)
    for name in ['__init__.py','plugin.yaml']:
        shutil.copyfile(Path(__file__).with_name('native_plugin')/name,plugin/name)
    write_json(plugin/'tools.json',tool_schemas())
    write_json(marker,{'hermes_commit':commit,'plugin':'kat-comparison','project_root':str(root),'created_at':prior.get('created_at',now())})
    env=dict(os.environ)
    env.update(HERMES_HOME=str(home),HERMES_RUNTIME_DIR=str(home/'runtime'),
               SUPER_API_KEY=settings.token_factory_api_key.get_secret_value(),
               TOKEN_FACTORY_API_KEY=settings.token_factory_api_key.get_secret_value(),
               KAT_BRIDGE_PYTHON=sys.executable,KAT_PROJECT_ROOT=str(root),KAT_DATA_DIR=str(settings.data_dir.resolve()))
    return executable,home,env


def launch_native(settings, query=None, oneshot=False, resume=None):
    executable,home,env=prepare_native(settings)
    args=[str(executable),'chat','--cli','--toolsets','kat_corpus','--max-turns','12','--run-budget','180']
    if query:args+=['--query',query]
    if oneshot:args+=['--oneshot']
    if resume:args+=['--resume',resume]
    os.chdir(Path(__file__).resolve().parents[2])
    os.execve(str(executable),args,env)


def worker():
    settings=Settings();event={'event_id':uuid.uuid4().hex,'started_at':now()};started=time.monotonic()
    try:
        request=json.load(sys.stdin);event.update(tool=request.get('tool'),arguments=request.get('arguments',{}))
        result=dispatch_tool(Engine(settings),event['tool'],event['arguments']);event.update(status='ok',result=result)
    except Exception as error:
        event.update(status='error',result={'error':str(error),'error_type':type(error).__name__})
    from .cli import _safe
    event=_safe(event,settings);event['seconds']=round(time.monotonic()-started,3)
    write_json(settings.data_dir/'native-hermes-tools'/(event['event_id']+'.json'),event)
    print(json.dumps(event['result'],ensure_ascii=False))


if __name__=='__main__':worker()
