from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from src.config import Settings, ensure_directories
from src.utils.io import save_json

CACHE_FILES = [
    "kpis.json",
    "qualidade_dados.json",
    "monthly_counts.csv",
    "monthly_agg.csv",
    "hourly_profile.csv",
    "heatmap_hour_weekday.csv",
    "municipal_summary.csv",
    "crime_type_summary.csv",
    "spatial_summary.csv",
    "predictions_regression.csv",
    "metrics_regression.csv",
    "predictions_classification.csv",
    "metrics_classification.csv",
    "feature_importance_classification.csv",
]


def build_dashboard_cache(settings: Settings) -> dict[str, object]:
    ensure_directories(settings)
    manifest: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(settings.processed_dir),
        "cache_dir": str(settings.cache_dir),
        "files": [],
        "missing": [],
        "strategy": "Streamlit lê somente arquivos pré-computados em data/cache; modelos não são treinados na interface.",
    }
    for filename in CACHE_FILES:
        source = settings.processed_dir / filename
        target = settings.cache_dir / filename
        if source.exists():
            shutil.copy2(source, target)
            manifest["files"].append(filename)
        else:
            manifest["missing"].append(filename)
    save_json(manifest, settings.cache_dir / "manifest.json")
    return manifest
