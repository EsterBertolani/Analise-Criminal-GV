from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"

st.set_page_config(
    page_title="Furtos e Roubos — Grande Vitória",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
.metric-card {background: #F4F7F6; border-radius: 16px; padding: 18px; border: 1px solid #DDE7E3;}
.small-muted {color: #6B7280; font-size: 0.92rem;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_csv(name: str) -> pd.DataFrame:
    path = CACHE / name
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_json(name: str) -> dict:
    path = CACHE / name
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def check_cache() -> bool:
    required = ["kpis.json", "monthly_agg.csv", "hourly_profile.csv", "municipal_summary.csv"]
    missing = [name for name in required if not (CACHE / name).exists()]
    if missing:
        st.error("Cache do dashboard ainda não foi gerado.")
        st.code("python scripts/generate_demo_data.py\npython scripts/run_pipeline.py --csv data/raw/MICRODADOS_OCORRENCIAS_DEMO.csv")
        st.caption(f"Arquivos ausentes: {', '.join(missing)}")
        return False
    return True


def metric(label: str, value: object, help_text: str | None = None) -> None:
    st.metric(label=label, value=value, help=help_text)


def apply_sidebar_filters(monthly: pd.DataFrame, crime_summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[str]]:
    st.sidebar.title("Filtros")
    municipalities = sorted(crime_summary["municipio"].dropna().unique().tolist()) if not crime_summary.empty else []
    crimes = sorted(crime_summary["categoria_crime"].dropna().unique().tolist()) if not crime_summary.empty else []
    selected_municipalities = st.sidebar.multiselect("Municípios", municipalities, default=municipalities)
    selected_crimes = st.sidebar.multiselect("Tipo de crime", crimes, default=crimes)

    monthly_filtered = monthly.copy()
    crime_filtered = crime_summary.copy()
    if selected_municipalities:
        if "municipio" in monthly_filtered.columns:
            monthly_filtered = monthly_filtered[monthly_filtered["municipio"].isin(selected_municipalities)]
        crime_filtered = crime_filtered[crime_filtered["municipio"].isin(selected_municipalities)]
    if selected_crimes:
        if "categoria_crime" in monthly_filtered.columns:
            monthly_filtered = monthly_filtered[monthly_filtered["categoria_crime"].isin(selected_crimes)]
        crime_filtered = crime_filtered[crime_filtered["categoria_crime"].isin(selected_crimes)]
    return monthly_filtered, crime_filtered, selected_municipalities, selected_crimes


def render_overview(kpis: dict, monthly_agg: pd.DataFrame, municipal: pd.DataFrame) -> None:
    st.subheader("Visão geral")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric("Ocorrências", f"{int(kpis.get('total_ocorrencias', 0)):,}".replace(",", "."))
    with c2:
        metric("Furtos", f"{int(kpis.get('furtos', 0)):,}".replace(",", "."))
    with c3:
        metric("Roubos", f"{int(kpis.get('roubos', 0)):,}".replace(",", "."))
    with c4:
        metric("Município crítico", kpis.get("municipio_mais_registros", "—"))
    with c5:
        hour = kpis.get("hora_mais_frequente")
        metric("Hora mais frequente", "—" if hour is None else f"{int(hour):02d}h")

    st.caption(
        f"Período analisado: {kpis.get('periodo_inicio', '—')} a {kpis.get('periodo_fim', '—')} | "
        f"Hora informada em {kpis.get('percentual_hora_informada', '—')}% dos registros."
    )

    if not monthly_agg.empty:
        monthly_agg["data_mes"] = pd.to_datetime(monthly_agg["data_mes"])
        fig = px.line(monthly_agg, x="data_mes", y="ocorrencias", markers=True, title="Evolução mensal das ocorrências")
        fig.update_layout(xaxis_title="Mês", yaxis_title="Ocorrências")
        st.plotly_chart(fig, use_container_width=True)

    if not municipal.empty:
        fig = px.bar(municipal.sort_values("ocorrencias"), x="ocorrencias", y="municipio", orientation="h", title="Ranking municipal por ocorrências")
        fig.update_layout(xaxis_title="Ocorrências", yaxis_title="Município")
        st.plotly_chart(fig, use_container_width=True)


def render_temporal(hourly: pd.DataFrame, heatmap: pd.DataFrame) -> None:
    st.subheader("Padrões temporais")
    if not hourly.empty:
        fig = px.line(hourly, x="hora", y="ocorrencias_ponderadas", color="categoria_crime", markers=True, title="Perfil horário com peso aorístico")
        fig.update_layout(xaxis_title="Hora do dia", yaxis_title="Ocorrências ponderadas")
        st.plotly_chart(fig, use_container_width=True)

    if not heatmap.empty:
        pivot = heatmap.pivot_table(index="dia_semana", columns="hora", values="ocorrencias", aggfunc="sum", fill_value=0)
        order = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        pivot = pivot.reindex([day for day in order if day in pivot.index])
        fig = px.imshow(pivot, aspect="auto", title="Heatmap: hora × dia da semana")
        fig.update_layout(xaxis_title="Hora", yaxis_title="Dia da semana")
        st.plotly_chart(fig, use_container_width=True)


def render_spatial(spatial: pd.DataFrame) -> None:
    st.subheader("Distribuição espacial e taxas")
    if spatial.empty:
        st.info("Resumo espacial ainda não disponível.")
        return

    metric_col = "taxa_100k" if spatial["taxa_100k"].notna().any() else "ocorrencias"
    label = "Taxa por 100 mil hab." if metric_col == "taxa_100k" else "Ocorrências"
    fig = px.bar(spatial.sort_values(metric_col), x=metric_col, y="municipio", orientation="h", title=f"Municípios por {label.lower()}")
    st.plotly_chart(fig, use_container_width=True)

    if {"latitude", "longitude"}.issubset(spatial.columns) and spatial[["latitude", "longitude"]].notna().all(axis=None):
        map_fig = px.scatter_mapbox(
            spatial,
            lat="latitude",
            lon="longitude",
            size="ocorrencias",
            color=metric_col,
            hover_name="municipio",
            hover_data=["ocorrencias", "taxa_100k", "lisa_cluster", "lisa_status"],
            zoom=8,
            height=520,
            title="Mapa sintético por centroides municipais",
        )
        map_fig.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 45, "l": 0, "b": 0})
        st.plotly_chart(map_fig, use_container_width=True)

    st.markdown("**Autocorrelação espacial / LISA**")
    cols = [col for col in ["municipio", "ocorrencias", "taxa_100k", "lisa_cluster", "lisa_p_value", "lisa_status"] if col in spatial.columns]
    st.dataframe(spatial[cols], use_container_width=True, hide_index=True)


def render_models(reg_metrics: pd.DataFrame, reg_preds: pd.DataFrame, clf_metrics: pd.DataFrame, clf_preds: pd.DataFrame, importance: pd.DataFrame) -> None:
    st.subheader("Modelos preditivos")
    left, right = st.columns(2)
    with left:
        st.markdown("### Regressão — previsão mensal")
        if reg_metrics.empty:
            st.info("Métricas de regressão ainda não disponíveis.")
        else:
            st.dataframe(reg_metrics, use_container_width=True, hide_index=True)
        if not reg_preds.empty:
            reg_preds["data_mes"] = pd.to_datetime(reg_preds["data_mes"])
            melted = reg_preds.melt(id_vars=["data_mes", "ocorrencias"], value_vars=[c for c in reg_preds.columns if c.startswith("pred_")], var_name="modelo", value_name="previsao")
            fig = px.line(melted, x="data_mes", y="previsao", color="modelo", markers=True, title="Previsões no período de teste")
            fig.add_scatter(x=reg_preds["data_mes"], y=reg_preds["ocorrencias"], mode="lines+markers", name="Real")
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### Classificação — municípios de alto risco")
        if clf_metrics.empty:
            st.info("Métricas de classificação ainda não disponíveis.")
        else:
            st.dataframe(clf_metrics, use_container_width=True, hide_index=True)
        if not clf_preds.empty and "prob_alto_risco" in clf_preds.columns:
            latest = clf_preds.sort_values("ano_mes").groupby(["municipio", "categoria_crime"], as_index=False).tail(1)
            fig = px.bar(latest.sort_values("prob_alto_risco"), x="prob_alto_risco", y="municipio", color="categoria_crime", orientation="h", title="Probabilidade de alto risco — último mês de teste")
            st.plotly_chart(fig, use_container_width=True)

    if not importance.empty:
        st.markdown("### Importância de variáveis")
        st.dataframe(importance.head(20), use_container_width=True, hide_index=True)


def render_documentation(quality: dict, manifest: dict) -> None:
    st.subheader("Dados, cache e reprodutibilidade")
    st.markdown(
        "A interface não treina modelos nem roda ETL em tempo real. Ela consome somente arquivos pré-computados de `data/cache`, "
        "o que mantém o carregamento rápido e previsível."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Qualidade dos dados**")
        st.json(quality)
    with c2:
        st.markdown("**Manifesto do cache**")
        st.json(manifest)


def main() -> None:
    st.title("🛡️ Análise Preditiva de Furtos e Roubos na Grande Vitória")
    st.markdown(
        "Painel final do MVP com indicadores, padrões temporais, distribuição espacial e modelos preditivos."
    )
    if not check_cache():
        return

    kpis = load_json("kpis.json")
    quality = load_json("qualidade_dados.json")
    manifest = load_json("manifest.json")
    monthly_agg = load_csv("monthly_agg.csv")
    monthly_counts = load_csv("monthly_counts.csv")
    hourly = load_csv("hourly_profile.csv")
    heatmap = load_csv("heatmap_hour_weekday.csv")
    municipal = load_csv("municipal_summary.csv")
    crime_summary = load_csv("crime_type_summary.csv")
    spatial = load_csv("spatial_summary.csv")
    reg_metrics = load_csv("metrics_regression.csv")
    reg_preds = load_csv("predictions_regression.csv")
    clf_metrics = load_csv("metrics_classification.csv")
    clf_preds = load_csv("predictions_classification.csv")
    importance = load_csv("feature_importance_classification.csv")

    _, crime_summary_filtered, _, _ = apply_sidebar_filters(monthly_counts, crime_summary)

    tabs = st.tabs(["Visão geral", "Temporal", "Espacial", "Modelos", "Documentação"])
    with tabs[0]:
        render_overview(kpis, monthly_agg, municipal)
    with tabs[1]:
        render_temporal(hourly, heatmap)
    with tabs[2]:
        render_spatial(spatial)
    with tabs[3]:
        render_models(reg_metrics, reg_preds, clf_metrics, clf_preds, importance)
    with tabs[4]:
        render_documentation(quality, manifest)

    with st.expander("Tabela filtrada por tipo e município"):
        st.dataframe(crime_summary_filtered, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
