from __future__ import annotations

import math
from collections.abc import Iterable

import pandas as pd


def parse_hour(value: object) -> float:
    if pd.isna(value):
        return math.nan
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "indeterminado", "ignorado"}:
        return math.nan

    if ":" in text:
        part = text.split(":", maxsplit=1)[0]
    else:
        part = text.split(" ", maxsplit=1)[0]

    digits = "".join(ch for ch in part if ch.isdigit())
    if not digits:
        return math.nan

    hour = int(digits)
    if 0 <= hour <= 23:
        return float(hour)
    return math.nan


def hour_interval(start_hour: float, end_hour: float) -> list[int]:
    if math.isnan(start_hour) and math.isnan(end_hour):
        return list(range(24))
    if math.isnan(start_hour):
        return [int(end_hour)]
    if math.isnan(end_hour):
        return [int(start_hour)]

    start = int(start_hour)
    end = int(end_hour)
    if start == end:
        return [start]
    if start < end:
        return list(range(start, end + 1))
    return list(range(start, 24)) + list(range(0, end + 1))


def expand_aoristic_hours(
    df: pd.DataFrame,
    id_col: str = "id_evento",
    start_col: str = "hora_inicio",
    end_col: str = "hora_fim",
    observed_hour_col: str = "hora",
) -> pd.DataFrame:
    """Distribui cada ocorrência pelas horas possíveis e atribui pesos.

    Se houver uma hora exata, cada ocorrência fica com peso 1 naquela hora.
    Se houver intervalo início/fim, o peso é dividido igualmente pelas horas do intervalo.
    Se não houver nenhuma hora, a ocorrência é distribuída pelas 24 horas com peso 1/24.
    """
    rows: list[dict[str, object]] = []
    has_interval = start_col in df.columns or end_col in df.columns

    for row in df[[col for col in [id_col, observed_hour_col, start_col, end_col] if col in df.columns]].itertuples(index=False):
        values = row._asdict()
        event_id = values.get(id_col)
        observed = parse_hour(values.get(observed_hour_col))

        if not math.isnan(observed):
            hours = [int(observed)]
        elif has_interval:
            start = parse_hour(values.get(start_col))
            end = parse_hour(values.get(end_col))
            hours = hour_interval(start, end)
        else:
            hours = list(range(24))

        weight = 1 / len(hours)
        rows.extend({id_col: event_id, "hora_aoristica": hour, "peso_aoristico": weight} for hour in hours)

    return pd.DataFrame(rows)


def weighted_count(values: Iterable[float]) -> float:
    return float(sum(values))
