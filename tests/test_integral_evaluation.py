import pandas as pd
import pytest

from src.environment.diabetes_followup_env import DiabetesFollowUpEnv
from src.evaluation.evaluate_policies import evaluar_politicas
from src.evaluation.integral import (
    brechas_equidad, construir_reporte_integral, enriquecer_detalle_con_cohorte,
    exportar_reporte_integral, metricas_por_subgrupo, sensibilidad_capacidad,
)


def cohorte():
    return pd.DataFrame({
        "FOLIO_INT": ["100", "101", "102", "103"],
        "edad": [35, 55, 68, 72], "sexo": [1, 2, 1, 2],
        "anios_con_diabetes": [2, 8, 15, 20], "insulina_diaria": [0, 0, 1, 1],
        "depresion": [0, 1, 0, 1], "consultas_control_12m": [1, 3, 5, 6],
        "num_hospitalizaciones": [0, 0, 1, 2], "num_complicaciones": [0, 1, 2, 3],
        "score_riesgo": [1, 4, 8, 12],
        "categoria_riesgo": ["bajo", "medio", "alto", "alto"],
    })


def factory(capacidad=5):
    return DiabetesFollowUpEnv(cohorte(), capacidad_mensual=capacidad, horizonte=2)


def intensa(env):
    return 3


def nula(env):
    return 0


def resultados():
    return evaluar_politicas(lambda: factory(5), {"Intensa": intensa, "Nula": nula}, [42, 123])


def test_enriquecimiento_preserva_filas_y_agrega_grupos():
    detalle = resultados()["detalle"]
    enriquecido = enriquecer_detalle_con_cohorte(detalle, cohorte())
    assert len(enriquecido) == len(detalle)
    assert set(enriquecido["grupo_sexo"]) == {"sexo_1", "sexo_2"}
    assert set(enriquecido["grupo_edad"]) == {"18-44", "45-64", "65_y_mas"}
    assert set(enriquecido["categoria_riesgo"]) <= {"bajo", "medio", "alto"}


def test_metricas_y_brechas_son_acotadas():
    detalle = enriquecer_detalle_con_cohorte(resultados()["detalle"], cohorte())
    metricas = metricas_por_subgrupo(detalle)
    brechas = brechas_equidad(metricas)
    assert set(metricas["dimension"]) == {"grupo_sexo", "grupo_edad", "categoria_riesgo"}
    assert metricas["cobertura"].between(0, 1).all()
    assert metricas["tasa_ajuste"].between(0, 1).all()
    assert (brechas.filter(like="brecha_") >= 0).all().all()


def test_sensibilidad_usa_capacidades_y_semillas_comunes():
    salida = sensibilidad_capacidad(
        factory, {"Intensa": intensa, "Nula": nula}, [0, 5], [42, 123]
    )
    episodios = salida["sensibilidad_episodios"]
    assert set(episodios["capacidad_mensual"]) == {0, 5}
    assert set(episodios["semilla"]) == {42, 123}
    assert (episodios.query("capacidad_mensual == 0")["recursos_usados"] == 0).all()
    assert (episodios["recursos_usados"] <= episodios["capacidad_total"]).all()


def test_reporte_integral_exporta_manifest(tmp_path):
    base = resultados()
    sensibilidad = sensibilidad_capacidad(factory, {"Intensa": intensa}, [3, 5], [42])
    reporte = construir_reporte_integral(base, cohorte(), sensibilidad)
    rutas = exportar_reporte_integral(reporte, tmp_path)
    esperadas = {"estabilidad_semillas", "metricas_subgrupos", "brechas_equidad", "sensibilidad_resumen", "manifest"}
    assert esperadas <= set(rutas)
    assert all(ruta.exists() for ruta in rutas.values())


def test_folio_duplicado_se_rechaza():
    duplicada = cohorte()
    duplicada.loc[1, "FOLIO_INT"] = duplicada.loc[0, "FOLIO_INT"]
    with pytest.raises(ValueError, match="única"):
        enriquecer_detalle_con_cohorte(resultados()["detalle"], duplicada)
