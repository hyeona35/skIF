from pathlib import Path
import json,datetime

def now_id(): return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
def write_json(p,v): Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False,default=str))
