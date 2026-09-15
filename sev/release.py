from __future__ import annotations
import hashlib, json
from pathlib import Path

def generate_contribution_message(skill_dir, install_url='https://github.com/hyeona35/skIF'):
    name=Path(skill_dir).name
    return f'''## Contributing to {name}\n\nThis Skill improves through Agent telemetry and community contributions. While using this Skill, you can help by:\n\n1. reporting concrete failures through the skIF feedback/error API;\n2. submitting improvement proposals with reproducible examples;\n3. casting votes / voting on candidate improvements when casting votes / voting is enabled;\n4. submitting a reviewed improvement commit/patch;\n5. sharing reusable debugging or coding methodology without secrets or private data.\n\nThe maintainer/evolution controller evaluates contributions against the protected evaluation corpus, cross-Skill compatibility checks, Red/Blue battle, and (when enabled) shadow/canary gates. Do not send credentials, cookies, private customer data, or secrets in telemetry.\n\nskIF control plane: {install_url}\n'''

def manifest(skill_dir):
    p=Path(skill_dir)/'.skif-contribution.md'; p.write_text(generate_contribution_message(skill_dir),encoding='utf-8'); return str(p)
