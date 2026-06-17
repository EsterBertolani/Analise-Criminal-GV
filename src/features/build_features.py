from __future__ import annotations

import numpy as np
import pandas as pd


def monthly_counts(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.groupby(["ano_mes", "municipio", "categoria_crime"], as_index=False)
        .agg(
            ocorrencias=("id_evento", "count"),
            populacao=("populacao", "max"),
        )
        .sort_values(["municipio", "categoria_crime", "ano_mes"])
    )
    monthly["data_mes"] = pd.to_datetime(monthly["ano_mes"] + "-01")
    monthly["taxa_100k"] = np.where(
        monthly["populacao"].gt(0),
        monthly["ocorrencias"] / monthly["populacao"] * 100000,
        np.nan,
    )
    return monthly


def aggregate_monthly(df: pd.DataFrame) -> pd.DataFrame:
    agg = (
        df.groupby("ano_mes", as_index=False)
        .agg(ocorrencias=("id_evento", "count"))
        .sort_values("ano_mes")
    )
    agg["data_mes"] = pd.to_datetime(agg["ano_mes"] + "-01")
    return agg


def add_lag_features(
    df: pd.DataFrame,
    group_cols: list[str],
    target_col: str,
    lags: tuple[int, ...] = (1, 2, 3, 6, 12),
    windows: tuple[int, ...] = (3, 6, 12),
) -> pd.DataFrame:
    result = df.sort_values(group_cols + ["data_mes"]).copy()
    grouped = result.groupby(group_cols, dropna=False)[target_col]
    for lag in lags:
        result[f"lag_{lag}"] = grouped.shift(lag)
    for window in windows:
        result[f"rolling_mean_{window}"] = result.groupby(group_cols, dropna=False)[target_col].transform(
            lambda series: series.shift(1).rolling(window=window, min_periods=1).mean()
        )
        result[f"rolling_std_{window}"] = result.groupby(group_cols, dropna=False)[target_col].transform(
            lambda series: series.shift(1).rolling(window=window, min_periods=2).std()
        )
    result["mes_num"] = result["data_mes"].dt.month
    result["ano"] = result["data_mes"].dt.year
    result["mes_sin"] = np.sin(2 * np.pi * result["mes_num"] / 12)
    result["mes_cos"] = np.cos(2 * np.pi * result["mes_num"] / 12)
    return result


def regression_features(df: pd.DataFrame) -> pd.DataFrame:
    agg = aggregate_monthly(df)
    agg["serie"] = "Grande Vitória"
    return add_lag_features(agg, ["serie"], "ocorrencias")


def classification_features(df: pd.DataFrame, high_risk_quantile: float = 0.75) -> pd.DataFrame:
    monthly = monthly_counts(df)
    metric = "taxa_100k"
    if monthly[metric].isna().all():
        metric = "ocorrencias"
    monthly["risco_base"] = monthly[metric]
    thresholds = monthly.groupby("ano_mes")["risco_base"].transform(lambda x: x.quantile(high_risk_quantile))
    monthly["alto_risco"] = (monthly["risco_base"] >= thresholds).astype(int)
    features = add_lag_features(monthly, ["municipio", "categoria_crime"], "risco_base")
    return features
