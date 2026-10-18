"""A processed batch must keep abstention and errors separate from comparisons."""
import time
from types import SimpleNamespace

from fastapi.testclient import TestClient

from kat.api import create_app
from kat.config import Settings


def test_batch_reports_abstained_and_failed_pages_separately(tmp_path):
    settings=Settings(_env_file=None,data_dir=tmp_path,token_factory_api_key='offline-test-key',
                      retrieval_base_url='http://fake.invalid/v1')
    def compare(page):
        if page=='broken':raise ValueError('Fixture parse failure')
        if page=='empty':return {'run_id':'fixture-empty','status':'abstained','abstained':True}
        return {'run_id':'fixture-readable'}
    engine=SimpleNamespace(settings=settings,root=tmp_path,
                           pages=lambda:[{'page_id':p} for p in ['readable','empty','broken']],compare=compare)
    with TestClient(create_app(engine=engine)) as client:
        response=client.post('/api/jobs',json={'action':'batch'})
        assert response.status_code==202
        job_id=response.json()['job_id']
        for _ in range(100):
            job=client.get('/api/jobs/'+job_id).json()
            if job['status'] not in {'queued','running'}:break
            time.sleep(.01)
        assert job['status']=='complete'
        result=job['result']
        assert result['processed']==3 and result['completed']==1
        assert result['abstained']==1 and result['errors']==1
        assert [r['status'] for r in result['pages']]==['complete','abstained','error']
