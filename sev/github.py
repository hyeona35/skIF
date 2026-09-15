from __future__ import annotations
import json,urllib.request

def create_pr(owner_repo,token,head,base,title,body,draft=True):
    url=f'https://api.github.com/repos/{owner_repo}/pulls'
    payload={'title':title,'head':head,'base':base,'body':body,'draft':draft}
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json','Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=60) as r: return json.loads(r.read().decode())


def create_gist(token, files, description, public=False):
    import json, urllib.request
    body=json.dumps({'description':description,'public':public,'files':{name:{'content':content} for name,content in files.items()}}).encode()
    req=urllib.request.Request('https://api.github.com/gists',data=body,headers={'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json','Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read().decode())
