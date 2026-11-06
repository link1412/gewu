"""tools/tmm.py's closed-form checks.    python3 -I tests/yohen/tmm_check.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools"))
import tmm  # noqa: E402

sys.exit(0 if tmm.check() else 1)
