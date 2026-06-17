from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import Settings
from src.data.schema import normalize_text
from src.utils.io import read_csv_flexible, save_table


def add_centroids(summary: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    path = settings.external_dir / "municipios_gv_centroides.csv"
    if not path.exists():
        summary["latitude"] = np.nan
        summary["longitude"] = np.nan
        return summary
    centroids = read_csv_flexible(path)
    centroids["municipio"] = centroids["municipio"].map(normalize_text)
    return summary.merge(centroids, on="municipio", how="left")


def _load_manual_neighbors(summary: pd.DataFrame, settings: Settings) -> dict[str, set[str]]:
    path = settings.external_dir / "vizinhanca_municipios_gv.csv"
    municipalities = set(summary["municipio"].map(normalize_text))
    neighbors: dict[str, set[str]] = {municipality: set() for municipality in municipalities}

    if path.exists():
        df = read_csv_flexible(path)
        df.columns = [str(col).lower().strip() for col in df.columns]
        if {"municipio", "vizinho"}.issubset(df.columns):
            for _, row in df.iterrows():
                municipality = normalize_text(row["municipio"])
                neighbor = normalize_text(row["vizinho"])
                if municipality in municipalities and neighbor in municipalities:
                    neighbors.setdefault(municipality, set()).add(neighbor)
                    neighbors.setdefault(neighbor, set()).add(municipality)

    # Fallback conservador caso o CSV de vizinhança não tenha sido copiado.
    fallback = {
        "VITORIA": {"VILA VELHA", "SERRA", "CARIACICA"},
        "VILA VELHA": {"VITORIA", "CARIACICA", "VIANA", "GUARAPARI"},
        "SERRA": {"VITORIA", "CARIACICA", "FUNDAO"},
        "CARIACICA": {"VITORIA", "VILA VELHA", "SERRA", "VIANA"},
        "VIANA": {"CARIACICA", "VILA VELHA", "GUARAPARI"},
        "GUARAPARI": {"VILA VELHA", "VIANA"},
        "FUNDAO": {"SERRA"},
    }
    for municipality in municipalities:
        if not neighbors.get(municipality):
            neighbors[municipality] = fallback.get(municipality, set()) & municipalities
    return neighbors


def _manual_local_moran(summary: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    base = summary.copy()
    metric = "taxa_100k" if base["taxa_100k"].notna().any() else "ocorrencias"
    base = base.sort_values("municipio").reset_index(drop=True)
    municipalities = base["municipio"].map(normalize_text).tolist()
    values = pd.to_numeric(base[metric], errors="coerce").fillna(0).to_numpy(dtype=float)

    if len(base) < 4 or np.isclose(values.var(), 0):
        base["lisa_cluster"] = "não_calculado"
        base["lisa_p_value"] = np.nan
        base["lisa_i"] = np.nan
        base["lisa_status"] = "Municípios insuficientes ou métrica sem variação"
        return base

    neighbors = _load_manual_neighbors(base, settings)
    index = {municipality: pos for pos, municipality in enumerate(municipalities)}
    weights = np.zeros((len(base), len(base)), dtype=float)
    for municipality, municipality_neighbors in neighbors.items():
        i = index.get(municipality)
        if i is None:
            continue
        valid_neighbors = [index[n] for n in municipality_neighbors if n in index and n != municipality]
        if valid_neighbors:
            weights[i, valid_neighbors] = 1.0 / len(valid_neighbors)

    if np.isclose(weights.sum(), 0):
        base["lisa_cluster"] = "não_calculado"
        base["lisa_p_value"] = np.nan
        base["lisa_i"] = np.nan
        base["lisa_status"] = "Vizinhança municipal ausente"
        return base

    z = values - values.mean()
    m2 = np.mean(z**2)
    spatial_lag = weights @ z
    local_i = (z * spatial_lag) / m2

    labels = []
    for own, lag in zip(z, spatial_lag, strict=False):
        if own > 0 and lag > 0:
            labels.append("HH")
        elif own > 0 and lag < 0:
            labels.append("HL")
        elif own < 0 and lag > 0:
            labels.append("LH")
        elif own < 0 and lag < 0:
            labels.append("LL")
        else:
            labels.append("neutro")

    rng = np.random.default_rng(settings.random_state)
    permutations = 999
    simulated = np.zeros((permutations, len(base)), dtype=float)
    for p in range(permutations):
        shuffled = rng.permutation(z)
        simulated[p] = (z * (weights @ shuffled)) / m2
    p_values = ((np.abs(simulated) >= np.abs(local_i)).sum(axis=0) + 1) / (permutations + 1)

    base["lisa_cluster"] = labels
    base["lisa_p_value"] = np.round(p_values, 4)
    base["lisa_i"] = np.round(local_i, 4)
    base["lisa_status"] = f"calculado_por_vizinhança_manual_usando_{metric}"
    return base


def compute_lisa_if_available(summary: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    """Calcula LISA por GeoJSON/PySAL quando disponível; senão usa vizinhança manual.

    O fallback evita que o MVP fique com `GeoJSON municipal ausente` quando o objetivo
    é demonstrar a análise espacial no Streamlit sem instalar dependências pesadas.
    """
    geo_path = settings.external_dir / "municipios_gv.geojson"
    base = summary.copy()
    base["municipio"] = base["municipio"].map(normalize_text)

    if not geo_path.exists():
        return _manual_local_moran(base, settings)

    try:
        import geopandas as gpd
        from esda.moran import Moran_Local
        from libpysal.weights import Queen
    except Exception:
        return _manual_local_moran(base, settings)

    try:
        gdf = gpd.read_file(geo_path)
        gdf.columns = [str(col).lower() for col in gdf.columns]
        name_col = "municipio" if "municipio" in gdf.columns else "name"
        gdf["municipio"] = gdf[name_col].map(normalize_text)
        merged = gdf.merge(base, on="municipio", how="inner")
        if len(merged) < 4:
            return _manual_local_moran(base, settings)
        weights = Queen.from_dataframe(merged, use_index=False)
        weights.transform = "r"
        metric = "taxa_100k" if merged["taxa_100k"].notna().any() else "ocorrencias"
        lisa = Moran_Local(merged[metric].fillna(0), weights)
        labels = np.array(["HH", "LH", "LL", "HL"])
        merged["lisa_cluster"] = labels[lisa.q - 1]
        merged["lisa_p_value"] = np.round(lisa.p_sim, 4)
        merged["lisa_i"] = np.round(lisa.Is, 4)
        merged["lisa_status"] = f"calculado_com_geojson_pysal_usando_{metric}"
        return base.drop(
            columns=["lisa_cluster", "lisa_p_value", "lisa_i", "lisa_status"],
            errors="ignore",
        ).merge(
            merged[["municipio", "lisa_cluster", "lisa_p_value", "lisa_i", "lisa_status"]],
            on="municipio",
            how="left",
        )
    except Exception:
        return _manual_local_moran(base, settings)


def build_spatial_outputs(municipal_summary: pd.DataFrame, settings: Settings) -> dict[str, Path]:
    spatial = add_centroids(municipal_summary, settings)
    lisa = compute_lisa_if_available(spatial, settings)
    path = settings.processed_dir / "spatial_summary.csv"
    save_table(lisa, path)
    return {"spatial_summary": path}
