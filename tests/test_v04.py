import json, tempfile, subprocess
from pathlib import Path
from sev.config import FrameworkConfig,ProviderConfig,RoleConfig,BudgetConfig
from sev.evals import append_case
from sev.provenance import snapshot_hash

def test_config_roundtrip(tmp_path,monkeypatch):
    from sev.config import CONFIG_PATH,save_config,load_config
    monkeypatch.setattr('sev.config.CONFIG_PATH',tmp_path/'config.json')
    c=FrameworkConfig(providers={'a':ProviderConfig('a','custom','m','', 'http://127.0.0.1')},roles={r:RoleConfig(['a']) for r in ('worker','critic','improver','judge')})
    save_config(c); d=load_config(); assert d.roles['judge'].providers==['a']

def test_corpus_growth(tmp_path):
    p=tmp_path/'suite.json'; p.write_text('{"cases":[]}'); append_case(p,{'id':'x','prompt':'p'}); assert json.loads(p.read_text())['cases'][0]['id']=='x'

def test_snapshot_hash_changes(tmp_path):
    (tmp_path/'SKILL.md').write_text('a'); a=snapshot_hash(tmp_path); (tmp_path/'SKILL.md').write_text('b'); assert a!=snapshot_hash(tmp_path)
