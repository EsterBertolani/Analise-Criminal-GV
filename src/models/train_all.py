from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import Settings
from src.models.classification import train_classification_models
from src.models.regression import train_regression_models
from src.utils.io import read_table


def train_all_models(settings: Settings) -> dict[str, Path]:
    occurrences_path = settings.processed_dir / "ocorrencias_tratadas.csv"
    df = read_table(occurrences_path)
    df["data_fato"] = pd.to_datetime(df["data_fato"])
    outputs: dict[str, Path] = {}
    outputs.update(train_regression_models(df, settings))
    outputs.update(train_classification_models(df, settings))
    return outputs
