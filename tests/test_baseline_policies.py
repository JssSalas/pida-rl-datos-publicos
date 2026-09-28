import pandas as pd

from src.environment.diabetes_followup_env import DiabetesFollowUpEnv
from src.evaluation.evaluate_policies import evaluar_politica_detallada
from src.policies.baselines import politica_aleatoria, politica_por_reglas


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
            "score_riesgo": [2, 8, 14],
            "categoria_riesgo": ["bajo", "medio", "alto"],
        }
    )


def test_reglas_asigna_clasificacion_por_riesgo():
    env = DiabetesFollowUpEnv(cohorte(), capacidad_mensual=20, horizonte=1)
    env.reset(seed=42)
    acciones = []
    for _ in range(3):
        acciones.append(politica_por_reglas(env))
        env.step(acciones[-1])
    assert acciones == [0, 1, 2]


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
