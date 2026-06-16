from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import Settings, ensure_directories
from src.data.aoristic import expand_aoristic_hours, parse_hour
from src.data.schema import infer_columns, normalize_text, standardize_columns
from src.utils.io import file_sha256, read_csv_flexible, save_json, save_table

DAY_NAMES = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}


def classify_crime(value: object) -> str | None:
    text = normalize_text(value)
    if "ROUBO" in text:
        return "Roubo"
    if "FURTO" in text:
        return "Furto"
    return None


def time_period(hour: float | int | None) -> str:
    if pd.isna(hour):
        return "Indeterminado"
    hour_int = int(hour)
    if 0 <= hour_int <= 5:
        return "Madrugada"
    if 6 <= hour_int <= 11:
        return "Manhã"
    if 12 <= hour_int <= 17:
        return "Tarde"
    return "Noite"


def _canonicalize(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str | None]]:
    df = standardize_columns(df)
    colmap = infer_columns(df)
    out = pd.DataFrame()
    out["id_evento"] = (
        df[colmap.id_ocorrencia].astype(str)
        if colmap.id_ocorrencia
        else pd.Series(np.arange(len(df)), index=df.index).astype(str)
    )
    out["data_fato"] = pd.to_datetime(df[colmap.data], errors="coerce", dayfirst=True)
    out["hora"] = df[colmap.hora].map(parse_hour) if colmap.hora else np.nan
    out["municipio"] = df[colmap.municipio].map(normalize_text)
    out["bairro"] = df[colmap.bairro].map(normalize_text) if colmap.bairro else "NÃO INFORMADO"
    out["tipo_crime_original"] = df[colmap.crime].astype(str)
    out["categoria_crime"] = df[colmap.crime].map(classify_crime)
    out["tipo_local"] = df[colmap.tipo_local].map(normalize_text) if colmap.tipo_local else "NÃO INFORMADO"
    if colmap.hora_inicio:
        out["hora_inicio"] = df[colmap.hora_inicio].map(parse_hour)
    if colmap.hora_fim:
        out["hora_fim"] = df[colmap.hora_fim].map(parse_hour)
    return out, colmap.__dict__


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["ano"] = result["data_fato"].dt.year.astype("Int64")
    result["mes"] = result["data_fato"].dt.month.astype("Int64")
    result["dia"] = result["data_fato"].dt.day.astype("Int64")
    result["ano_mes"] = result["data_fato"].dt.to_period("M").astype(str)
    result["dia_semana_num"] = result["data_fato"].dt.weekday.astype("Int64")
    result["dia_semana"] = result["dia_semana_num"].map(DAY_NAMES)
    result["faixa_horaria"] = result["hora"].map(time_period)
    result["data_hora"] = result["data_fato"] + pd.to_timedelta(result["hora"].fillna(0), unit="h")
    return result


def filter_scope(df: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    start = pd.to_datetime(settings.start_date)
    end = pd.to_datetime(settings.end_date)
    municipalities = {normalize_text(m) for m in settings.municipalities}
    filtered = df[
        df["data_fato"].between(start, end, inclusive="both")
        & df["municipio"].isin(municipalities)
        & df["categoria_crime"].notna()
    ].copy()
    return filtered


def _expand_population_years(population: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    if population.empty:
        return population

    start_year = int(pd.to_datetime(settings.start_date).year)
    end_year = int(pd.to_datetime(settings.end_date).year)
    years = list(range(start_year, end_year + 1))
    municipalities = [normalize_text(m) for m in settings.municipalities]

    grid = pd.MultiIndex.from_product(
        [municipalities, years], names=["municipio", "ano"]
    ).to_frame(index=False)

    base = population.copy()
    base = base.dropna(subset=["municipio", "ano", "populacao"])
    if base.empty:
        return pd.DataFrame(columns=["municipio", "ano", "populacao"])

    base = base.sort_values(["municipio", "ano"]).drop_duplicates(
        subset=["municipio", "ano"], keep="last"
    )
    expanded = grid.merge(base, on=["municipio", "ano"], how="left")

    # Caso exista apenas 2025, ou alguns anos estejam faltando, preenche cada município
    # com o valor mais próximo disponível. Isso evita taxa_100k vazia no painel.
    expanded["populacao"] = expanded.groupby("municipio")["populacao"].transform(
        lambda series: series.ffill().bfill()
    )

    return expanded[["municipio", "ano", "populacao"]]


def load_population(settings: Settings) -> pd.DataFrame:
    candidates = [
        settings.external_dir / "populacao_municipios_gv.csv",
        settings.external_dir / "populacao_gv_template.csv",
    ]
    for path in candidates:
        if path.exists():
            pop = read_csv_flexible(path)
            pop = standardize_columns(pop)
            if {"municipio", "ano", "populacao"}.issubset(pop.columns):
                pop["municipio"] = pop["municipio"].map(normalize_text)
                pop["ano"] = pd.to_numeric(pop["ano"], errors="coerce").astype("Int64")
                pop["populacao"] = pd.to_numeric(pop["populacao"], errors="coerce")
                return _expand_population_years(pop[["municipio", "ano", "populacao"]], settings)
    return pd.DataFrame(columns=["municipio", "ano", "populacao"])


def run_etl(raw_path: Path, settings: Settings) -> dict[str, Path]:
    ensure_directories(settings)
    raw = read_csv_flexible(raw_path)
    canonical, column_map = _canonicalize(raw)
    scoped_before_dedup = filter_scope(canonical, settings)
    scoped = scoped_before_dedup.drop_duplicates(subset=["id_evento"], keep="first")
    scoped = add_temporal_features(scoped)

    population = load_population(settings)
    if not population.empty:
        scoped = scoped.merge(population, on=["municipio", "ano"], how="left")
    else:
        scoped["populacao"] = np.nan
    scoped["taxa_100k_evento"] = np.where(scoped["populacao"].gt(0), 100000 / scoped["populacao"], np.nan)

    aoristic = expand_aoristic_hours(scoped)

    quality = {
        "arquivo_origem": str(raw_path),
        "hash_sha256": file_sha256(raw_path),
        "linhas_brutas": int(len(raw)),
        "linhas_apos_filtro_antes_deduplicacao": int(len(scoped_before_dedup)),
        "linhas_apos_filtro": int(len(scoped)),
        "linhas_removidas_por_deduplicacao": int(len(scoped_before_dedup) - len(scoped)),
        "colunas_detectadas": column_map,
        "populacao_carregada": bool(not population.empty),
        "missing_percent": scoped.isna().mean().round(4).to_dict(),
        "periodo_min": str(scoped["data_fato"].min()),
        "periodo_max": str(scoped["data_fato"].max()),
    }

    paths = {
        "occurrences": settings.processed_dir / "ocorrencias_tratadas.csv",
        "aoristic": settings.processed_dir / "pesos_aoristicos.csv",
        "quality": settings.processed_dir / "qualidade_dados.json",
    }
    save_table(scoped, paths["occurrences"])
    save_table(aoristic, paths["aoristic"])
    save_json(quality, paths["quality"])
    return paths
