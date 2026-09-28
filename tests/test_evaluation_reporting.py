import pandas as pd
import pytest

from src.environment.diabetes_followup_env import DiabetesFollowUpEnv
from src.evaluation.evaluate_policies import evaluar_politica_detallada, evaluar_politicas
from src.evaluation.reporting import construir_reporte, exportar_reporte_csv


def cohorte():
    return pd.DataFrame(
        {
            "patient_id": [100, 101, 102, 103],
            "edad": [60, 55, 45, 70],
            "sexo": [0, 1, 0, 1],
            "anios_con_diabetes": [15, 8, 4, 20],
            "num_complicaciones": [2, 1, 0, 3],
            "num_comorbilidades": [1, 1, 0, 2],
            "categoria_riesgo": ["alto", "medio", "bajo", "alto"],
        }
    )


def env_factory():
    return DiabetesFollowUpEnv(cohorte(), capacidad_mensual=5, horizonte=2)


def siempre_teleorientacion(env):
    return 3


def sin_contacto(env):
    return 0


def test_detalle_tiene_una_fila_por_paciente_mes():
    resultado = evaluar_politica_detallada(
        env_factory(), siempre_teleorientacion, "Teleorientación", [42]
    )
    detalle = resultado["detalle"]
    assert len(detalle) == 8
    assert set(detalle["accion_propuesta"]) == {3}
    assert set(detalle["mes"]) == {1, 2}
    assert detalle["perfil_id"].nunique() == 4
    assert (detalle["recursos_despues"] >= 0).all()


def test_resumen_distingue_propuesta_y_ejecucion():
    resultado = evaluar_politica_detallada(
        env_factory(), siempre_teleorientacion, "Teleorientación", [42]
    )
    episodio = resultado["episodios"].iloc[0]
    assert episodio["contactos_propuestos"] == 8
    assert episodio["contactos_ejecutados"] == 2
    assert episodio["recursos_usados"] == 10
    assert episodio["utilizacion_capacidad"] == pytest.approx(1.0)
    assert episodio["ajustes_capacidad"] == 6


def test_comparacion_usa_mismas_semillas_y_clasificaciones_completas(tmp_path):
    resultados = evaluar_politicas(
        env_factory,
        {"Teleorientación": siempre_teleorientacion, "Sin contacto": sin_contacto},
        semillas=[42, 123],
    )
    assert set(resultados["episodios"]["semilla"]) == {42, 123}
    assert resultados["episodios"].groupby("algoritmo").size().to_dict() == {
        "Sin contacto": 2,
        "Teleorientación": 2,
    }

    reporte = construir_reporte(resultados)
    tabla = reporte["clasificaciones_ejecutadas"]
    assert tabla.groupby("algoritmo").size().eq(4).all()
    assert set(tabla["accion"]) == {0, 1, 2, 3}

    rutas = exportar_reporte_csv(reporte, tmp_path)
    assert set(rutas) == set(reporte)
    assert all(ruta.exists() for ruta in rutas.values())
