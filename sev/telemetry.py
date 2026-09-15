from __future__ import annotations
from .production import scrub, fingerprint_request

def normalize_event(body: dict) -> dict:
    clean=scrub(body)
    clean['request_fingerprint']=fingerprint_request(body)
    return clean
