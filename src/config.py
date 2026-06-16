from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    project_root: Path
    raw_dir: Path
    processed_dir: Path
    cache_dir: Path
    external_dir: Path
    reports_dir: Path
    default_raw_file: Path
    demo_raw_file: Path
    start_date: str
    end_date: str
    municipalities: tuple[str, ...]
    crime_keywords: tuple[str, ...]
    minimum_test_months: int
    test_fraction: float
    high_risk_quantile: float
    random_state: int


def load_yaml(path: Path | None = None) -> dict[str, Any]:
    config_path = path or PROJECT_ROOT / "configs" / "settings.yaml"
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_settings(path: Path | None = None) -> Settings:
    cfg = load_yaml(path)
    root = PROJECT_ROOT
    paths = cfg["paths"]
    project = cfg["project"]
    scope = cfg["scope"]
    modeling = cfg["modeling"]
    return Settings(
        project_root=root,
        raw_dir=root / paths["raw_dir"],
        processed_dir=root / paths["processed_dir"],
        cache_dir=root / paths["cache_dir"],
        external_dir=root / paths["external_dir"],
        reports_dir=root / paths["reports_dir"],
        default_raw_file=root / project["default_raw_file"],
        demo_raw_file=root / project["demo_raw_file"],
        start_date=scope["start_date"],
        end_date=scope["end_date"],
        municipalities=tuple(scope["municipalities"]),
        crime_keywords=tuple(scope["crime_keywords"]),
        minimum_test_months=int(modeling["minimum_test_months"]),
        test_fraction=float(modeling["test_fraction"]),
        high_risk_quantile=float(modeling["high_risk_quantile"]),
        random_state=int(modeling["random_state"]),
    )


def ensure_directories(settings: Settings) -> None:
    for path in [settings.raw_dir, settings.processed_dir, settings.cache_dir, settings.external_dir]:
        path.mkdir(parents=True, exist_ok=True)
