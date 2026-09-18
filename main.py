"""Desktop pet entry point.

Usage:
    python main.py                 # run normally
    python main.py --snapshot a.png  # render one frame to a.png and exit
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))

from app.main import main  # noqa: E402


if __name__ == "__main__":
    snapshot = None
    if "--snapshot" in sys.argv:
        idx = sys.argv.index("--snapshot")
        snapshot = (
            sys.argv[idx + 1] if idx + 1 < len(sys.argv) else str(ROOT / "snapshot.png")
        )
    main(snapshot)
