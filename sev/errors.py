from __future__ import annotations
import hashlib,json,time
from collections import Counter
from pathlib import Path

def fingerprint(skill,message,tool=''):
 return hashlib.sha256(f'{skill}|{tool}|{message}'.encode()).hexdigest()[:16]

def report_error(root_dir,skill,message,severity='medium',tool='',trajectory=None):
 p=Path(root_dir); p.mkdir(parents=True,exist_ok=True); fp=fingerprint(skill,message,tool)
 row={'ts':time.time(),'skill':skill,'fingerprint':fp,'message':message,'severity':severity,'tool':tool,'trajectory':trajectory or []}
 with (p/'errors.jsonl').open('a') as f: f.write(json.dumps(row,ensure_ascii=False)+'\n')
 return row

def recent_errors(root_dir,skill,window_minutes=60):
 p=Path(root_dir)/'errors.jsonl'; now=time.time(); out=[]
 if not p.exists(): return out
 for line in p.read_text().splitlines():
  try:
   x=json.loads(line)
   if x.get('skill')==skill and now-x.get('ts',0)<=window_minutes*60: out.append(x)
  except: pass
 return out

def review_signal(errors,absolute_threshold=5,delta_threshold=.5):
 count=len(errors)
 buckets=Counter(x.get('fingerprint') for x in errors)
 spikes=sum(1 for n in buckets.values() if n>=3)
 prev=Counter()
 midpoint=len(errors)//2
 for x in errors[:midpoint]: prev[x.get('fingerprint')]+=1
 now=Counter(x.get('fingerprint') for x in errors[midpoint:])
 delta=max(((now[k]-prev[k])/max(1,prev[k]) for k in now),default=0)
 return {'count':count,'spikes':spikes,'delta':delta,'review':count>=absolute_threshold or delta>=delta_threshold}
