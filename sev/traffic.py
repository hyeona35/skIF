from __future__ import annotations
import time
from .production import fingerprint_request, route_percent, scrub

class TrafficMirror:
    def __init__(self, event_store, kill_switch, max_duplicates=1):
        self.events=event_store; self.kill_switch=kill_switch; self.seen={}; self.max_duplicates=max_duplicates
    def mirror(self, request, candidate_percent=100):
        if self.kill_switch.status().get('enabled'):
            return {'mirrored':False,'reason':'kill-switch'}
        clean=scrub(request); fp=fingerprint_request(clean); count=self.seen.get(fp,0)
        if count >= self.max_duplicates:
            return {'mirrored':False,'reason':'duplicate'}
        self.seen[fp]=count+1
        key=str(request.get('request_id') or fp)
        ok=route_percent(key,candidate_percent)
        row={'fingerprint':fp,'mirrored':ok,'candidate_percent':candidate_percent,'ts':time.time()}
        self.events.emit('traffic_mirror',actor=request.get('agent_id','production'),skill=request.get('skill',''),payload=row)
        return row
