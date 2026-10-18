"""Native Hermes tools; execute the corpus backend in its Python environment."""
import json
import os
from pathlib import Path
import subprocess


def handler_for(name):
    def handle(params, **kwargs):
        del kwargs
        try:
            result=subprocess.run(
                [os.environ['KAT_BRIDGE_PYTHON'],'-m','kat.hermes_native','--tool'],
                input=json.dumps({'tool':name,'arguments':params}),text=True,capture_output=True,
                cwd=os.environ['KAT_PROJECT_ROOT'],timeout=180)
            if result.returncode:
                return json.dumps({'error':'Corpus backend failed; inspect the local tool event.',
                                   'exit_code':result.returncode})
            return json.dumps(json.loads(result.stdout),ensure_ascii=False)
        except subprocess.TimeoutExpired:
            return json.dumps({'error':'Corpus backend exceeded its 180 second deadline.'})
        except Exception as error:
            return json.dumps({'error':'Corpus tool unavailable','error_type':type(error).__name__})
    return handle


def register(ctx):
    schemas=json.loads(Path(__file__).with_name('tools.json').read_text())
    for name,schema in schemas.items():
        ctx.register_tool(name=name,toolset='kat_corpus',schema=schema,handler=handler_for(name))
