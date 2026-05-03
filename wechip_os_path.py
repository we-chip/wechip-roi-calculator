"""Register WECHIP-OS shared services on sys.path (import shim)."""
import sys
from pathlib import Path

_SHARED = Path(__file__).resolve().parent.parent / "WECHIP-OS" / "shared" / "services"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))
