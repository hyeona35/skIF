from __future__ import annotations
import os,hmac
from dataclasses import dataclass

@dataclass(frozen=True)
class Principal:
    kind: str
    subject: str
    local: bool = False

class Authenticator:
    """Distinct trust planes: host dashboard, agent console, and user/guest console."""
    def __init__(self, host_env='SKIF_HOST_TOKEN', agent_env='SKIF_AGENT_TOKEN', user_env='SKIF_USER_TOKEN'):
        self.tokens={'host':os.environ.get(host_env,''),'agent':os.environ.get(agent_env,''),'user':os.environ.get(user_env,'')}
    def authenticate(self, headers, required: str | None, client_host=''):
        token=headers.get('Authorization','')
        if not required:return Principal('public','anonymous',client_host in ('127.0.0.1','::1','localhost'))
        expected=self.tokens.get(required,'')
        if not expected:return None
        if hmac.compare_digest(token,f'Bearer {expected}'):return Principal(required,required,client_host in ('127.0.0.1','::1','localhost'))
        return None
    def token_configured(self,kind):return bool(self.tokens.get(kind,''))
