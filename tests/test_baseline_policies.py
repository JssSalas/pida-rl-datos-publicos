import pandas as pd
import pytest

from src.environment.diabetes_followup_env import DiabetesFollowUpEnv
from src.evaluation.evaluate_policies import evaluar_politica_detallada
from src.policies.baselines import (
    crear_politica_reglas_escalonadas,
    politica_aleatoria,
    politica_por_reglas,
    politica_reglas_escalonadas,
)


def cohorte():
    return pd.DataFrame(
        {
            "FOLIO_INT": ["1", "2", "3"],
            "edad": [40, 55, 70],
            "sexo": [1, 2, 1],
            "anios_con_diabetes": [3, 10, 20],
            "insulina_diaria": [0, 0, 1],
            "depresion": [0, 1, 0],
            "consultas_control_12m": [1, 3, 5],
            "num_hospitalizaciones": [0, 0, 1],
            "num_complicaciones": [0, 1, 2],
            "score_riesgo": [1, 3, 6],
            "categoria_riesgo": ["bajo", "medio", "alto"],
        }
    )


def cohorte_escalonada():
    return pd.DataFrame(
        {
            "FOLIO_INT": ["B1", "M2", "M3", "A5", "A6"],
            "edad": [40, 50, 55, 65, 70],
            "sexo": [1, 2, 1, 2, 1],
            "anios_con_diabetes": [3, 8, 10, 15, 20],
            "insulina_diaria": [0, 0, 0, 1, 1],
            "depresion": [0, 0, 1, 0, 1],
            "consultas_control_12m": [1, 2, 3, 4, 5],
            "num_hospitalizaciones": [0, 0, 0, 1, 1],
            "num_complicaciones": [0, 0, 1, 1, 2],
            "score_riesgo": [1, 2, 3, 5, 6],
            "categoria_riesgo": ["bajo", "medio", "medio", "alto", "alto"],
        }
    )


def acciones_propuestas(env, politica):
    env.reset(seed=42)
    acciones = []
    while True:
        accion = politica(env)
        acciones.append(accion)
        _, _, terminado, truncado, _ = env.step(accion)
        if terminado or truncado:
            return acciones


def test_reglas_asigna_clasificacion_por_riesgo():
    env = DiabetesFollowUpEnv(cohorte(), capacidad_mensual=20, horizonte=1)
    assert acciones_propuestas(env, politica_por_reglas) == [0, 1, 2]


def test_reglas_escalonadas_no_crea_cuarta_categoria():
    datos = cohorte_escalonada()
    env = DiabetesFollowUpEnv(datos, capacidad_mensual=30, horizonte=1)
    assert set(datos["categoria_riesgo"]) == {"bajo", "medio", "alto"}
    assert acciones_propuestas(env, politica_reglas_escalonadas) == [0, 1, 2, 2, 3]


def test_umbral_teleorientacion_es_configurable():
    env = DiabetesFollowUpEnv(cohorte_escalonada(), capacidad_mensual=30, horizonte=1)
    politica_umbral_5 = crear_politica_reglas_escalonadas(5)
    assert acciones_propuestas(env, politica_umbral_5) == [0, 1, 2, 3, 3]


def test_umbral_invalido_se_rechaza():
    with pytest.raises(ValueError):
        crear_politica_reglas_escalonadas(3)


def test_aleatoria_es_reproducible_con_misma_semilla():
    def ejecutar():
        resultado = evaluar_politica_detallada(
            DiabetesFollowUpEnv(cohorte(), capacidad_mensual=20, horizonte=3),
            politica_aleatoria,
            "Aleatoria",
            [2026],
        )
        return resultado["detalle"]["accion_propuesta"].tolist()

    assert ejecutar() == ejecutar()
