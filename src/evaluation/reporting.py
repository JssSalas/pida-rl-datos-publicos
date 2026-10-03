"""Construcción y exportación de reportes de evaluación."""

from pathlib import Path

import pandas as pd

from src.config import ACTION_LABELS


def tabla_clasificaciones(detalle, tipo="ejecutada"):
    """Cuenta y calcula el porcentaje de cada clasificación por algoritmo."""
    if tipo not in {"propuesta", "ejecutada"}:
        raise ValueError("tipo debe ser 'propuesta' o 'ejecutada'.")
    columna = f"accion_{tipo}"
    base = (
        detalle.groupby(["algoritmo", columna])
        .size()
        .rename("n")
        .reset_index()
        .rename(columns={columna: "accion"})
    )
    algoritmos = detalle["algoritmo"].drop_duplicates().tolist()
    indice = pd.MultiIndex.from_product(
        [algoritmos, sorted(ACTION_LABELS)], names=["algoritmo", "accion"]
    )
    base = base.set_index(["algoritmo", "accion"]).reindex(indice, fill_value=0).reset_index()
    base["accion_nombre"] = base["accion"].map(ACTION_LABELS)
    totales = base.groupby("algoritmo")["n"].transform("sum")
    base["porcentaje"] = (base["n"] / totales.where(totales > 0, 1)) * 100
    base["tipo_clasificacion"] = tipo
    return base[
        ["algoritmo", "tipo_clasificacion", "accion", "accion_nombre", "n", "porcentaje"]
    ]


def resumen_algoritmos(episodios):
    """Resume resultados comparables usando medias y desviaciones entre semillas."""
    metricas = [
        "recompensa_acumulada",
        "contactos_propuestos",
        "contactos_ejecutados",
        "eventos_adversos",
        "ajustes_capacidad",
        "recursos_usados",
        "utilizacion_capacidad",
        "cobertura_alto_riesgo",
    ]
    resumen = episodios.groupby("algoritmo")[metricas].agg(["mean", "std"])
    resumen.columns = [f"{metrica}_{estadistico}" for metrica, estadistico in resumen.columns]
    return resumen.reset_index()


def construir_reporte(resultados):
    """Añade tablas derivadas al resultado de evaluación."""
    detalle = resultados["detalle"].copy()
    episodios = resultados["episodios"].copy()
    return {
        "detalle": detalle,
        "episodios": episodios,
        "resumen_algoritmos": resumen_algoritmos(episodios),
        "clasificaciones_propuestas": tabla_clasificaciones(detalle, "propuesta"),
        "clasificaciones_ejecutadas": tabla_clasificaciones(detalle, "ejecutada"),
    }


def exportar_reporte_csv(reporte, directorio):
    """Exporta todas las tablas y devuelve sus rutas."""
    destino = Path(directorio)
    destino.mkdir(parents=True, exist_ok=True)
    rutas = {}
    for nombre, tabla in reporte.items():
        ruta = destino / f"{nombre}.csv"
        tabla.to_csv(ruta, index=False)
        rutas[nombre] = ruta
    return rutas
