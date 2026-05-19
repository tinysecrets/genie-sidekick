"""
scripts/list_models.py
======================
Print the set of Ollama model tags listed in config/models.yaml,
one per line, suitable for `ollama pull` piping.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "models.yaml"

if not CFG.exists():
    print("config/models.yaml missing", file=sys.stderr)
    sys.exit(1)

data = yaml.safe_load(CFG.read_text())
seen = set()
for entry in data.get("ollama", {}).values():
    tag = entry.get("model")
    if tag and tag not in seen:
        seen.add(tag)
        print(tag)
