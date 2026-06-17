from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from src.config import Settings
from src.features.build_features import classification_features
from src.models.regression import temporal_cutoff_months
from src.utils.io import save_table

NUMERIC_COLS = [
    "risco_base",
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
CATEGORICAL_COLS = ["municipio", "categoria_crime"]
IMPORTANCE_COLS = ["modelo", "variavel", "importancia"]


def empty_importance() -> pd.DataFrame:
    return pd.DataFrame(columns=IMPORTANCE_COLS)


def make_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                NUMERIC_COLS,
            ),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLS),
        ]
    )


def candidate_models(settings: Settings) -> dict[str, object]:
    return {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "decision_tree": DecisionTreeClassifier(max_depth=5, class_weight="balanced", random_state=settings.random_state),
        "random_forest": RandomForestClassifier(
            n_estimators=120,
            max_depth=8,
            min_samples_leaf=3,
            class_weight="balanced_subsample",
            random_state=settings.random_state,
            n_jobs=1,
        ),
        "gradient_boosting": GradientBoostingClassifier(random_state=settings.random_state, n_estimators=120, learning_rate=0.05, max_depth=2),
    }


def evaluate_classifier(name: str, y_true: pd.Series, y_pred: np.ndarray, y_score: np.ndarray | None) -> dict[str, float | str]:
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="binary",
        zero_division=0,
    )
    auc = np.nan
    if y_score is not None and len(set(y_true)) == 2:
        auc = roc_auc_score(y_true, y_score)
    return {
        "modelo": name,
        "precision": round(float(precision), 3),
        "recall": round(float(recall), 3),
        "f1_score": round(float(f1), 3),
        "auc": round(float(auc), 3) if pd.notna(auc) else np.nan,
    }


def train_classification_models(df: pd.DataFrame, settings: Settings) -> dict[str, Path]:
    features = classification_features(df, settings.high_risk_quantile)
    features = features.dropna(subset=["lag_1"]).copy()
    cutoff = temporal_cutoff_months(features, settings)

    outputs = {
        "classification_predictions": settings.processed_dir / "predictions_classification.csv",
        "classification_metrics": settings.processed_dir / "metrics_classification.csv",
        "feature_importance": settings.processed_dir / "feature_importance_classification.csv",
    }

    if cutoff is None:
        reason = "Dados insuficientes para validação temporal da classificação após ETL; verifique período filtrado e coluna de data."
        save_table(pd.DataFrame(columns=["ano_mes", "data_mes", "municipio", "categoria_crime", "alto_risco", "risco_base", "modelo", "pred_alto_risco", "prob_alto_risco"]), outputs["classification_predictions"])
        save_table(pd.DataFrame([{"modelo": "nao_treinado", "precision": np.nan, "recall": np.nan, "f1_score": np.nan, "auc": np.nan, "cutoff_teste": None, "observacao": reason}]), outputs["classification_metrics"])
        save_table(empty_importance(), outputs["feature_importance"])
        print(f"[AVISO] {reason}")
        return outputs

    train = features[features["data_mes"] < cutoff]
    test = features[features["data_mes"] >= cutoff]

    if train.empty or test.empty or train["alto_risco"].nunique() < 2:
        save_table(pd.DataFrame(), outputs["classification_predictions"])
        save_table(pd.DataFrame(), outputs["classification_metrics"])
        save_table(empty_importance(), outputs["feature_importance"])
        return outputs

    metrics = []
    prediction_frames = []
    best_model_name = None
    best_f1 = -1.0
    best_pipeline: Pipeline | None = None

    for name, estimator in candidate_models(settings).items():
        pipeline = Pipeline([("prep", make_preprocessor()), ("model", estimator)])
        pipeline.fit(train[NUMERIC_COLS + CATEGORICAL_COLS], train["alto_risco"])
        y_pred = pipeline.predict(test[NUMERIC_COLS + CATEGORICAL_COLS])
        y_score = None
        if hasattr(pipeline, "predict_proba"):
            y_score = pipeline.predict_proba(test[NUMERIC_COLS + CATEGORICAL_COLS])[:, 1]
        elif hasattr(pipeline.named_steps["model"], "decision_function"):
            y_score = pipeline.decision_function(test[NUMERIC_COLS + CATEGORICAL_COLS])
        row = evaluate_classifier(name, test["alto_risco"], y_pred, y_score)
        row["cutoff_teste"] = cutoff
        metrics.append(row)
        if row["f1_score"] > best_f1:
            best_f1 = float(row["f1_score"])
            best_model_name = name
            best_pipeline = pipeline
        prediction_frames.append(
            test[["ano_mes", "data_mes", "municipio", "categoria_crime", "alto_risco", "risco_base"]].assign(
                modelo=name,
                pred_alto_risco=y_pred,
                prob_alto_risco=y_score if y_score is not None else np.nan,
            )
        )

    predictions = pd.concat(prediction_frames, ignore_index=True)
    metrics_df = pd.DataFrame(metrics).sort_values("f1_score", ascending=False)
    importance = empty_importance()
    if best_pipeline is not None:
        names = best_pipeline.named_steps["prep"].get_feature_names_out()
        model = best_pipeline.named_steps["model"]
        values = None
        if hasattr(model, "feature_importances_"):
            values = model.feature_importances_
        elif hasattr(model, "coef_"):
            values = np.abs(model.coef_).ravel()

        if values is not None and len(values) == len(names):
            importance = pd.DataFrame(
                {
                    "modelo": best_model_name,
                    "variavel": names,
                    "importancia": values,
                }
            ).sort_values("importancia", ascending=False)

    save_table(predictions, outputs["classification_predictions"])
    save_table(metrics_df, outputs["classification_metrics"])
    save_table(importance, outputs["feature_importance"])
    return outputs
