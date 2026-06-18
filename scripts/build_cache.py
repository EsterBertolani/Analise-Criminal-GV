from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.cache.build_cache import build_dashboard_cache  # noqa: E402
from src.config import get_settings  # noqa: E402


if __name__ == "__main__":
    manifest = build_dashboard_cache(get_settings())
    print(f"Cache atualizado: {manifest}")
