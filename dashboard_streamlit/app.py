"""Dashboard V2 para explorar políticas de seguimiento bajo capacidad limitada."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import DashboardDataError, filter_algorithms, load_integral_report


st.set_page_config(
    page_title="PIDA-RL · Seguimiento en diabetes",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = os.getenv(
    "PIDA_DASHBOARD_DATA_DIR", str(ROOT / "dashboard_data" / "v2")
)

COLORS = {
    "0": "#8c918d",
    "1": "#2f7f79",
    "2": "#d18f2f",
    "3": "#a54242",
    "bajo": "#4f8a75",
    "medio": "#d09a32",
    "alto": "#b34b4b",
}

st.markdown(
    """
    <style>
    :root { --pida-accent:#176d68; --pida-surface:#f5f4ef; --pida-border:#d9d7cf; }
    .stApp { color: #28251d; }
    [data-testid="stSidebar"] { border-right: 1px solid var(--pida-border); }
    [data-testid="stMetric"] {
        background: var(--pida-surface); border: 1px solid var(--pida-border);
        border-radius: .65rem; padding: .8rem 1rem;
    }
    [data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
    .pida-note {
        padding: .85rem 1rem; border: 1px solid var(--pida-border);
        background: var(--pida-surface); border-radius: .65rem; margin-bottom: 1rem;
    }
    .pida-kicker { color: var(--pida-accent); font-weight: 700; letter-spacing:.04em; }
    @media (prefers-color-scheme: dark) {
        :root { --pida-surface:#242522; --pida-border:#40423e; }
        .stApp { color: #e4e2dc; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_cached(path: str):
    return load_integral_report(path)


def chart_layout(fig):
    fig.update_layout(
        margin=dict(l=8, r=8, t=48, b=8),
        legend_title_text="",
        hovermode="closest",
    )
    return fig


def available_algorithms(report):
    return sorted(report["episodios"]["algoritmo"].dropna().astype(str).unique().tolist())


def metric_value(frame, column, default=float("nan")):
    if column not in frame.columns or frame.empty:
        return default
    return float(frame[column].mean())


def render_header(fingerprint: str):
    st.markdown('<div class="pida-kicker">PIDA · APRENDIZAJE POR REFUERZO</div>', unsafe_allow_html=True)
    st.title("Priorización de seguimiento en diabetes")
    st.caption(f"Evaluación en entorno de simulación · Reporte {fingerprint}")
    st.markdown(
        """<div class="pida-note"><strong>Alcance:</strong> herramienta exploratoria con datos públicos y
        supuestos explícitos. No es un dispositivo médico ni debe utilizarse para decidir la atención de una
        persona. Las brechas son diagnósticos operativos descriptivos, no pruebas de equidad clínica.</div>""",
        unsafe_allow_html=True,
    )


def render_overview(report, algorithms):
    episodes = filter_algorithms(report["episodios"], algorithms)
    summary = filter_algorithms(report["resumen_algoritmos"], algorithms)
    st.header("Panorama operativo")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Políticas visibles", len(algorithms))
    c2.metric("Semillas", episodes["semilla"].nunique())
    c3.metric("Recompensa media", f"{metric_value(episodes, 'recompensa_acumulada'):.2f}")
    c4.metric("Recursos medios", f"{metric_value(episodes, 'recursos_usados'):.1f}")

    left, right = st.columns((3, 2))
    with left:
        reward_col = "recompensa_acumulada_mean"
        if reward_col in summary:
            fig = px.bar(
                summary.sort_values(reward_col), x=reward_col, y="algoritmo", orientation="h",
                color_discrete_sequence=["#176d68"],
                labels={reward_col: "Recompensa acumulada media", "algoritmo": "Política"},
                title="Desempeño medio entre semillas",
            )
            st.plotly_chart(chart_layout(fig), use_container_width=True)
    with right:
        cols = [
            "algoritmo", "recompensa_acumulada_mean", "cobertura_alto_riesgo_mean",
            "utilizacion_capacidad_mean", "eventos_adversos_mean",
        ]
        st.subheader("Métricas comparables")
        st.dataframe(summary[[c for c in cols if c in summary]], hide_index=True, use_container_width=True)


def render_classifications(report, algorithms):
    st.header("Clasificaciones 0–3")
    st.write(
        "La propuesta describe la decisión de la política; la ejecución incorpora la capacidad disponible. "
        "La acción 3 es teleorientación y no representa una cuarta categoría de riesgo."
    )
    proposed = filter_algorithms(report["clasificaciones_propuestas"], algorithms)
    executed = filter_algorithms(report["clasificaciones_ejecutadas"], algorithms)
    combined = pd.concat([proposed, executed], ignore_index=True)
    combined["etapa"] = combined["tipo_clasificacion"].map(
        {"propuesta": "Propuesta", "ejecutada": "Ejecutada"}
    )
    combined["accion_etiqueta"] = combined["accion"].astype(str) + " · " + combined["accion_nombre"]
    fig = px.bar(
        combined, x="algoritmo", y="porcentaje", color="accion_etiqueta", barmode="group",
        facet_row="etapa", category_orders={"accion": [0, 1, 2, 3]},
        labels={"algoritmo": "Política", "porcentaje": "Decisiones (%)", "accion_etiqueta": "Acción"},
        color_discrete_sequence=[COLORS[str(i)] for i in range(4)],
        title="Distribución propuesta y ejecutada",
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    st.plotly_chart(chart_layout(fig), use_container_width=True)
    st.dataframe(
        combined[["algoritmo", "etapa", "accion", "accion_nombre", "n", "porcentaje"]],
        hide_index=True, use_container_width=True,
    )


def render_capacity(report, algorithms):
    st.header("Capacidad y estabilidad")
    sensitivity = report.get("sensibilidad_resumen")
    if isinstance(sensitivity, pd.DataFrame) and not sensitivity.empty:
        sensitivity = filter_algorithms(sensitivity, algorithms)
        metrics = {
            "Recompensa": "recompensa_acumulada_mean",
            "Cobertura de alto riesgo": "cobertura_alto_riesgo_mean",
            "Utilización": "utilizacion_capacidad_mean",
            "Eventos adversos": "eventos_adversos_mean",
            "Ajustes por capacidad": "ajustes_capacidad_mean",
        }
        available = {label: col for label, col in metrics.items() if col in sensitivity.columns}
        label = st.selectbox("Métrica de sensibilidad", list(available))
        metric = available[label]
        fig = px.line(
            sensitivity, x="capacidad_mensual", y=metric, color="algoritmo", markers=True,
            labels={"capacidad_mensual": "Capacidad mensual", metric: label, "algoritmo": "Política"},
            title=f"{label} ante escenarios de capacidad",
        )
        st.plotly_chart(chart_layout(fig), use_container_width=True)
    else:
        st.info("El reporte no incluye tablas de sensibilidad. Ejecute esa sección del notebook 09.")

    stability = filter_algorithms(report["estabilidad_semillas"], algorithms)
    ranges = [c for c in stability.columns if c.endswith("_rango")]
    if ranges:
        selected = st.selectbox("Rango entre semillas", ranges, format_func=lambda x: x.replace("_", " "))
        fig = px.bar(
            stability.sort_values(selected), x="algoritmo", y=selected,
            color_discrete_sequence=["#9a6b2f"],
            labels={"algoritmo": "Política", selected: "Rango"},
            title="Variabilidad entre semillas de evaluación",
        )
        st.plotly_chart(chart_layout(fig), use_container_width=True)


def render_equity(report, algorithms):
    st.header("Equidad operativa")
    groups = filter_algorithms(report["metricas_subgrupos"], algorithms)
    gaps = filter_algorithms(report["brechas_equidad"], algorithms)
    dimensions = groups["dimension"].dropna().unique().tolist()
    dimension = st.selectbox("Dimensión de análisis", dimensions)
    metric_options = {
        "Cobertura": "cobertura",
        "Intensidad media": "intensidad_media",
        "Tasa de ajustes": "tasa_ajuste",
        "Tasa de eventos": "tasa_eventos",
        "Recompensa media": "recompensa_media",
    }
    metric_options = {k: v for k, v in metric_options.items() if v in groups.columns}
    label = st.selectbox("Métrica por subgrupo", list(metric_options))
    metric = metric_options[label]
    subset = groups.loc[groups["dimension"] == dimension]
    aggregate = subset.groupby(["algoritmo", "subgrupo"], as_index=False)[metric].mean()
    color_map = COLORS if dimension == "categoria_riesgo" else None
    fig = px.bar(
        aggregate, x="algoritmo", y=metric, color="subgrupo", barmode="group",
        color_discrete_map=color_map,
        labels={"algoritmo": "Política", metric: label, "subgrupo": "Subgrupo"},
        title=f"{label} por {dimension.replace('_', ' ')}",
    )
    st.plotly_chart(chart_layout(fig), use_container_width=True)

    gap_col = f"brecha_{metric}"
    gap_subset = gaps.loc[gaps["dimension"] == dimension]
    if gap_col in gap_subset.columns:
        gap_mean = gap_subset.groupby("algoritmo", as_index=False)[gap_col].mean()
        fig_gap = px.bar(
            gap_mean.sort_values(gap_col), x="algoritmo", y=gap_col,
            color_discrete_sequence=["#a54242"],
            labels={"algoritmo": "Política", gap_col: "Brecha max–min"},
            title="Brecha descriptiva entre subgrupos",
        )
        st.plotly_chart(chart_layout(fig_gap), use_container_width=True)


def render_audit(report, algorithms):
    st.header("Trazabilidad y descarga")
    st.write(
        "La huella identifica el conjunto de archivos cargado. Si cambia cualquier CSV, la huella también cambia."
    )
    st.code(str(report["fingerprint"]), language=None)
    manifest = report["manifest"]
    if isinstance(manifest, pd.DataFrame) and not manifest.empty:
        st.subheader("Manifiesto")
        st.dataframe(manifest, hide_index=True, use_container_width=True)
    else:
        st.warning("No se encontró manifest.csv; las tablas se validaron por esquema, pero no por conteo declarado.")

    st.subheader("Descargas")
    downloadable = [(name, table) for name, table in report.items() if isinstance(table, pd.DataFrame)]
    selected = st.selectbox("Tabla", [name for name, _ in downloadable])
    table = dict(downloadable)[selected]
    if "algoritmo" in table.columns:
        table = filter_algorithms(table, algorithms)
    st.download_button(
        "Descargar CSV filtrado", table.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected}_filtrado.csv", mime="text/csv", type="primary",
    )
    st.dataframe(table.head(500), hide_index=True, use_container_width=True)
    if len(table) > 500:
        st.caption(f"Vista limitada a 500 de {len(table):,} filas; la descarga contiene todas las filas filtradas.")


def main():
    st.sidebar.title("PIDA-RL")
    data_dir = st.sidebar.text_input("Directorio de resultados V2", value=DEFAULT_DATA_DIR)
    try:
        report = load_cached(data_dir)
    except DashboardDataError as exc:
        st.title("Dashboard PIDA-RL")
        st.error(str(exc))
        st.info(
            "Ejecute el notebook 09, copie los CSV exportados a dashboard_data/v2 o defina "
            "PIDA_DASHBOARD_DATA_DIR con la ruta correspondiente."
        )
        st.stop()

    algorithms = available_algorithms(report)
    selected = st.sidebar.multiselect("Políticas", algorithms, default=algorithms)
    if not selected:
        st.warning("Seleccione al menos una política.")
        st.stop()

    pages = {
        "Panorama": render_overview,
        "Clasificaciones": render_classifications,
        "Capacidad": render_capacity,
        "Equidad": render_equity,
        "Trazabilidad": render_audit,
    }
    page = st.sidebar.radio("Sección", list(pages))
    st.sidebar.caption("Riesgo: bajo · medio · alto")
    st.sidebar.caption("Acciones: 0 · 1 · 2 · 3")

    render_header(report["fingerprint"])
    pages[page](report, selected)


if __name__ == "__main__":
    main()
