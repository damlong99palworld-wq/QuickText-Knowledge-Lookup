#!/usr/bin/env python3
"""Knowledge Lookup — local desktop knowledge base for UE5 / game-dev terms."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import run


if __name__ == "__main__":
    raise SystemExit(run())
