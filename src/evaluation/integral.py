"""Evaluación integral de desempeño, sensibilidad a capacidad y equidad operativa."""

from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.evaluate_policies import evaluar_politicas
from src.evaluation.reporting import construir_reporte


METRICAS_EPISODIO = [
    "recompensa_acumulada",
    "eventos_adversos",
    "recursos_usados",
    "utilizacion_capacidad",
    "cobertura_alto_riesgo",
    "ajustes_capacidad",
]


def enriquecer_detalle_con_cohorte(detalle, cohorte):
    """Añade atributos de subgrupo sin exponerlos al algoritmo durante la evaluación."""
    if "FOLIO_INT" not in cohorte.columns:
        raise KeyError("La cohorte debe contener FOLIO_INT para enlazar subgrupos.")
    duplicados = cohorte["FOLIO_INT"].astype(str).duplicated()
    if duplicados.any():
        raise ValueError("FOLIO_INT debe identificar perfiles de forma única.")
    columnas = [
        c for c in ("FOLIO_INT", "sexo", "edad", "categoria_riesgo")
        if c in cohorte.columns
    ]
    atributos = cohorte[columnas].copy()
    atributos["perfil_id"] = atributos.pop("FOLIO_INT").astype(str)
    base = detalle.copy()
    base["perfil_id"] = base["perfil_id"].astype(str)
    if "categoria_riesgo" in atributos:
        atributos = atributos.rename(columns={"categoria_riesgo": "categoria_riesgo_cohorte"})
    enriquecido = base.merge(atributos, on="perfil_id", how="left", validate="many_to_one")
    if enriquecido["sexo"].isna().any() if "sexo" in enriquecido else False:
        raise ValueError("No fue posible enlazar todos los perfiles con la cohorte.")
    if "sexo" in enriquecido:
        enriquecido["grupo_sexo"] = enriquecido["sexo"].map(
            {1: "sexo_1", 2: "sexo_2", "1": "sexo_1", "2": "sexo_2"}
        ).fillna("sexo_otro_no_especificado")
    if "edad" in enriquecido:
        enriquecido["grupo_edad"] = pd.cut(
            enriquecido["edad"], bins=[-np.inf, 44, 64, np.inf],
            labels=["18-44", "45-64", "65_y_mas"],
        ).astype(str)
    return enriquecido


def metricas_por_subgrupo(detalle, columnas_grupo=("grupo_sexo", "grupo_edad", "categoria_riesgo")):
    """Calcula cobertura, intensidad, ajustes, eventos y recompensa por subgrupo."""
    tablas = []
    for columna in columnas_grupo:
        if columna not in detalle.columns:
            continue
        agrupado = detalle.groupby(["algoritmo", "semilla", columna], dropna=False)
        tabla = agrupado.agg(
            decisiones=("accion_ejecutada", "size"),
            contactos_ejecutados=("accion_ejecutada", lambda s: int((s > 0).sum())),
            intensidad_media=("accion_ejecutada", "mean"),
            recursos_usados=("costo_real", "sum"),
            ajustes_capacidad=("accion_ajustada", "sum"),
            eventos_adversos=("evento_adverso", "sum"),
            recompensa_media=("recompensa", "mean"),
        ).reset_index().rename(columns={columna: "subgrupo"})
        tabla["dimension"] = columna
        tabla["cobertura"] = tabla["contactos_ejecutados"] / tabla["decisiones"]
        tabla["tasa_ajuste"] = tabla["ajustes_capacidad"] / tabla["decisiones"]
        tabla["tasa_eventos"] = tabla["eventos_adversos"] / tabla["decisiones"]
        tablas.append(tabla)
    if not tablas:
        return pd.DataFrame()
    columnas = [
        "algoritmo", "semilla", "dimension", "subgrupo", "decisiones",
        "contactos_ejecutados", "cobertura", "intensidad_media", "recursos_usados",
        "ajustes_capacidad", "tasa_ajuste", "eventos_adversos", "tasa_eventos",
        "recompensa_media",
    ]
    return pd.concat(tablas, ignore_index=True)[columnas]


def brechas_equidad(tabla_subgrupos):
    """Resume brechas max-min; son diagnósticos operativos, no pruebas de equidad clínica."""
    if tabla_subgrupos.empty:
        return pd.DataFrame()
    metricas = ["cobertura", "intensidad_media", "tasa_ajuste", "tasa_eventos", "recompensa_media"]
    filas = []
    for claves, grupo in tabla_subgrupos.groupby(["algoritmo", "semilla", "dimension"]):
        fila = dict(zip(("algoritmo", "semilla", "dimension"), claves))
        fila["n_subgrupos"] = int(grupo["subgrupo"].nunique())
        for metrica in metricas:
            minimo, maximo = float(grupo[metrica].min()), float(grupo[metrica].max())
            fila[f"{metrica}_min"] = minimo
            fila[f"{metrica}_max"] = maximo
            fila[f"brecha_{metrica}"] = maximo - minimo
        filas.append(fila)
    return pd.DataFrame(filas)


def estabilidad_semillas(episodios):
    """Calcula media, desviación y rango entre semillas para métricas centrales."""
    disponibles = [m for m in METRICAS_EPISODIO if m in episodios.columns]
    resumen = episodios.groupby("algoritmo")[disponibles].agg(["mean", "std", "min", "max"])
    resumen.columns = [f"{m}_{e}" for m, e in resumen.columns]
    resumen = resumen.reset_index()
    for metrica in disponibles:
        resumen[f"{metrica}_rango"] = resumen[f"{metrica}_max"] - resumen[f"{metrica}_min"]
    return resumen


def sensibilidad_capacidad(env_factory_por_capacidad, politicas, capacidades, semillas=(42, 123, 2026)):
    """Evalúa las políticas en escenarios explícitos de capacidad con semillas comunes."""
    episodios = []
    for capacidad in capacidades:
        capacidad = int(capacidad)
        if capacidad < 0:
            raise ValueError("Las capacidades deben ser enteros no negativos.")
        resultados = evaluar_politicas(
            lambda c=capacidad: env_factory_por_capacidad(c), politicas, semillas
        )
        tabla = resultados["episodios"].copy()
        tabla.insert(0, "capacidad_mensual", capacidad)
        episodios.append(tabla)
    detalle = pd.concat(episodios, ignore_index=True)
    metricas = [m for m in METRICAS_EPISODIO if m in detalle.columns]
    resumen = detalle.groupby(["capacidad_mensual", "algoritmo"])[metricas].agg(["mean", "std"])
    resumen.columns = [f"{m}_{e}" for m, e in resumen.columns]
    return {"sensibilidad_episodios": detalle, "sensibilidad_resumen": resumen.reset_index()}


def construir_reporte_integral(resultados, cohorte, sensibilidad=None):
    """Extiende el reporte común con estabilidad y diagnósticos de equidad operativa."""
    reporte = construir_reporte(resultados)
    detalle = enriquecer_detalle_con_cohorte(reporte["detalle"], cohorte)
    subgrupos = metricas_por_subgrupo(detalle)
    reporte["detalle"] = detalle
    reporte["estabilidad_semillas"] = estabilidad_semillas(reporte["episodios"])
    reporte["metricas_subgrupos"] = subgrupos
    reporte["brechas_equidad"] = brechas_equidad(subgrupos)
    if sensibilidad:
        reporte.update(sensibilidad)
    return reporte


def exportar_reporte_integral(reporte, directorio):
    """Exporta tablas CSV y un manifiesto que facilita auditoría y recuperación."""
    destino = Path(directorio)
    destino.mkdir(parents=True, exist_ok=True)
    rutas = {}
    for nombre, tabla in reporte.items():
        if isinstance(tabla, pd.DataFrame):
            ruta = destino / f"{nombre}.csv"
            tabla.to_csv(ruta, index=False)
            rutas[nombre] = ruta
    manifiesto = pd.DataFrame(
        [{"tabla": nombre, "archivo": ruta.name, "filas": len(pd.read_csv(ruta))}
         for nombre, ruta in rutas.items()]
    )
    ruta_manifiesto = destino / "manifest.csv"
    manifiesto.to_csv(ruta_manifiesto, index=False)
    rutas["manifest"] = ruta_manifiesto
    return rutas
