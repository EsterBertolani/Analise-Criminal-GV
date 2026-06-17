from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import Settings
from src.features.build_features import aggregate_monthly, monthly_counts
from src.utils.io import save_json, save_table


def build_kpis(df: pd.DataFrame) -> dict[str, object]:
    if df.empty:
        return {}
    total = int(len(df))
    by_crime = df["categoria_crime"].value_counts().to_dict()
    top_municipality = df["municipio"].value_counts().idxmax()
    top_hour = int(df["hora"].dropna().mode().iloc[0]) if df["hora"].notna().any() else None
    period_min = df["data_fato"].min()
    period_max = df["data_fato"].max()
    return {
        "total_ocorrencias": total,
        "furtos": int(by_crime.get("Furto", 0)),
        "roubos": int(by_crime.get("Roubo", 0)),
        "municipio_mais_registros": top_municipality,
        "hora_mais_frequente": top_hour,
        "periodo_inicio": str(period_min.date()) if pd.notna(period_min) else None,
        "periodo_fim": str(period_max.date()) if pd.notna(period_max) else None,
        "municipios_analisados": int(df["municipio"].nunique()),
        "bairros_analisados": int(df["bairro"].nunique()),
        "percentual_hora_informada": round(float(df["hora"].notna().mean() * 100), 2),
    }


def hourly_profile(df: pd.DataFrame, aoristic: pd.DataFrame | None = None) -> pd.DataFrame:
    if aoristic is not None and not aoristic.empty:
        base = aoristic.merge(
            df[["id_evento", "municipio", "categoria_crime", "dia_semana"]],
            on="id_evento",
            how="left",
        )
        profile = (
            base.groupby(["hora_aoristica", "categoria_crime"], as_index=False)["peso_aoristico"]
            .sum()
            .rename(columns={"hora_aoristica": "hora", "peso_aoristico": "ocorrencias_ponderadas"})
        )
        return profile.sort_values(["categoria_crime", "hora"])

    return (
        df.dropna(subset=["hora"])
        .groupby(["hora", "categoria_crime"], as_index=False)
        .agg(ocorrencias_ponderadas=("id_evento", "count"))
        .sort_values(["categoria_crime", "hora"])
    )


def heatmap_hour_weekday(df: pd.DataFrame) -> pd.DataFrame:
    valid = df.dropna(subset=["hora", "dia_semana_num"])
    heat = (
        valid.groupby(["dia_semana_num", "dia_semana", "hora"], as_index=False)
        .agg(ocorrencias=("id_evento", "count"))
        .sort_values(["dia_semana_num", "hora"])
    )
    return heat


def municipal_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("municipio", as_index=False)
        .agg(
            ocorrencias=("id_evento", "count"),
            populacao=("populacao", "max"),
            bairros=("bairro", "nunique"),
        )
        .sort_values("ocorrencias", ascending=False)
    )
    summary["taxa_100k"] = np.where(
        summary["populacao"].gt(0),
        summary["ocorrencias"] / summary["populacao"] * 100000,
        np.nan,
    )
    return summary


def crime_type_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["categoria_crime", "municipio"], as_index=False)
        .agg(ocorrencias=("id_evento", "count"))
        .sort_values("ocorrencias", ascending=False)
    )


def build_eda_outputs(df: pd.DataFrame, aoristic: pd.DataFrame, settings: Settings) -> dict[str, Path]:
    outputs = {
        "kpis": settings.processed_dir / "kpis.json",
        "monthly_counts": settings.processed_dir / "monthly_counts.csv",
        "monthly_agg": settings.processed_dir / "monthly_agg.csv",
        "hourly_profile": settings.processed_dir / "hourly_profile.csv",
        "heatmap_hour_weekday": settings.processed_dir / "heatmap_hour_weekday.csv",
        "municipal_summary": settings.processed_dir / "municipal_summary.csv",
        "crime_type_summary": settings.processed_dir / "crime_type_summary.csv",
    }
    save_json(build_kpis(df), outputs["kpis"])
    save_table(monthly_counts(df), outputs["monthly_counts"])
    save_table(aggregate_monthly(df), outputs["monthly_agg"])
    save_table(hourly_profile(df, aoristic), outputs["hourly_profile"])
    save_table(heatmap_hour_weekday(df), outputs["heatmap_hour_weekday"])
    save_table(municipal_summary(df), outputs["municipal_summary"])
    save_table(crime_type_summary(df), outputs["crime_type_summary"])
    return outputs
