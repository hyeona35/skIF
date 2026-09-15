#!/usr/bin/env bash
set -euo pipefail
python -m py_compile sev/*.py
pytest -q
python scripts/security_audit.py
python scripts/perf_benchmark.py --iterations 100
( cd go && go test ./... && go vet ./... && go build ./cmd/skif-gateway )
node ./node/test.js
