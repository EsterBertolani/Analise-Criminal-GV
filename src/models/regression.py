from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.config import Settings
from src.features.build_features import regression_features
from src.utils.io import save_table

FEATURE_COLS = [
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_6",
    "lag_12",
    "rolling_mean_3",
    "rolling_std_3",
    "rolling_mean_6",
    "rolling_std_6",
    "rolling_mean_12",
    "rolling_std_12",
    "mes_num",
    "ano",
    "mes_sin",
    "mes_cos",
]


def temporal_cutoff_months(data: pd.DataFrame, settings: Settings) -> pd.Timestamp | None:
    """Define o primeiro mês de teste sem quebrar quando há poucos dados.

    Modelos com validação temporal precisam de pelo menos alguns meses
    depois do ETL. Quando o CSV oficial vem filtrado demais, ou quando
    a coluna de data foi inferida incorretamente, o dataset pode ficar
    com 0 ou 1 mês. Nesse caso, retornamos None para o pipeline salvar
    saídas vazias em vez de parar com IndexError.
    """
    if data.empty or "data_mes" not in data.columns:
        return None
    months = sorted(pd.to_datetime(data["data_mes"], errors="coerce").dropna().unique())
    if len(months) < 3:
        return None
    if len(months) <= settings.minimum_test_months + 3:
        idx = max(1, len(months) - max(2, len(months) // 3))
        idx = min(idx, len(months) - 1)
        return months[idx]
    test_size = max(settings.minimum_test_months, int(round(len(months) * settings.test_fraction)))
    test_size = min(test_size, len(months) - 1)
    return months[-test_size]


def seasonal_naive_predictions(series: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    result = series.copy()
    result["pred_baseline_sazonal"] = result["ocorrencias"].shift(12)
    fallback = result["ocorrencias"].expanding().mean().shift(1)
    result["pred_baseline_sazonal"] = result["pred_baseline_sazonal"].fillna(fallback)
    return result[result["data_mes"] >= cutoff][["ano_mes", "data_mes", "ocorrencias", "pred_baseline_sazonal"]]


def sarimax_predictions(series: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
    except Exception:  # noqa: BLE001
        return pd.DataFrame()

    train = series[series["data_mes"] < cutoff].set_index("data_mes")["ocorrencias"].asfreq("MS")
    test = series[series["data_mes"] >= cutoff].set_index("data_mes")["ocorrencias"].asfreq("MS")
    if len(train) < 18 or len(test) == 0:
        return pd.DataFrame()
    try:
        model = SARIMAX(
            train,
            order=(1, 1, 1),
            seasonal_order=(0, 0, 0, 0),
            enforce_stationarity=False,
            enforce_invertibility=False,
            simple_differencing=True,
        ).fit(disp=False, maxiter=40)
        pred = model.forecast(steps=len(test))
        return pd.DataFrame(
            {
                "ano_mes": test.index.strftime("%Y-%m"),
                "data_mes": test.index,
                "ocorrencias": test.values,
                "pred_sarimax": np.maximum(pred.values, 0),
            }
        )
    except Exception:  # noqa: BLE001
        return pd.DataFrame()


def gradient_boosting_predictions(features: pd.DataFrame, cutoff: pd.Timestamp, settings: Settings) -> pd.DataFrame:
    model_data = features.dropna(subset=["lag_1"]).copy()
    for col in FEATURE_COLS:
        if col not in model_data.columns:
            model_data[col] = np.nan
    model_data[FEATURE_COLS] = model_data[FEATURE_COLS].fillna(0)
    train = model_data[model_data["data_mes"] < cutoff]
    test = model_data[model_data["data_mes"] >= cutoff]
    if len(train) < 12 or test.empty:
        return pd.DataFrame()
    model = GradientBoostingRegressor(random_state=settings.random_state, n_estimators=120, learning_rate=0.05, max_depth=2)
    model.fit(train[FEATURE_COLS], train["ocorrencias"])
    pred = model.predict(test[FEATURE_COLS])
    return pd.DataFrame(
        {
            "ano_mes": test["ano_mes"].values,
            "data_mes": test["data_mes"].values,
            "ocorrencias": test["ocorrencias"].values,
            "pred_gradient_boosting": np.maximum(pred, 0),
        }
    )


def metric_rows(predictions: pd.DataFrame) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for col in predictions.columns:
        if not col.startswith("pred_"):
            continue
        valid = predictions[["ocorrencias", col]].dropna()
        if valid.empty:
            continue
        mae = mean_absolute_error(valid["ocorrencias"], valid[col])
        rmse = mean_squared_error(valid["ocorrencias"], valid[col]) ** 0.5
        rows.append({"modelo": col.replace("pred_", ""), "MAE": round(mae, 3), "RMSE": round(rmse, 3)})
    return rows


def train_regression_models(df: pd.DataFrame, settings: Settings) -> dict[str, Path]:
    outputs = {
        "regression_predictions": settings.processed_dir / "predictions_regression.csv",
        "regression_metrics": settings.processed_dir / "metrics_regression.csv",
    }
    features = regression_features(df)
    cutoff = temporal_cutoff_months(features, settings)
    series = features[["ano_mes", "data_mes", "ocorrencias"]].drop_duplicates().sort_values("data_mes")

    if cutoff is None or series.empty:
        reason = "Dados insuficientes para validação temporal da regressão após ETL; verifique período filtrado e coluna de data."
        save_table(pd.DataFrame(columns=["ano_mes", "data_mes", "ocorrencias", "pred_baseline_sazonal", "cutoff_teste", "observacao"]), outputs["regression_predictions"])
        save_table(pd.DataFrame([{"modelo": "nao_treinado", "MAE": np.nan, "RMSE": np.nan, "cutoff_teste": None, "observacao": reason}]), outputs["regression_metrics"])
        print(f"[AVISO] {reason}")
        return outputs

    preds = seasonal_naive_predictions(series, cutoff)
    sarimax = sarimax_predictions(series, cutoff)
    gb = gradient_boosting_predictions(features, cutoff, settings)
    for extra in [sarimax, gb]:
        if not extra.empty:
            preds = preds.merge(extra, on=["ano_mes", "data_mes", "ocorrencias"], how="left")

    metrics = pd.DataFrame(metric_rows(preds))
    preds["cutoff_teste"] = cutoff
    metrics["cutoff_teste"] = cutoff

    save_table(preds, outputs["regression_predictions"])
    save_table(metrics, outputs["regression_metrics"])
    return outputs
