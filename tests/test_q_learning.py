import numpy as np
import pandas as pd

from src.environment.diabetes_followup_env import DiabetesFollowUpEnv
from src.evaluation.evaluate_policies import evaluar_politica_detallada
from src.policies.q_learning import (
    QLearningAgent,
    crear_politica_q_learning,
    entrenar_q_learning,
)


def cohorte():
    return pd.DataFrame(
        {
            "FOLIO_INT": ["B1", "M1", "A1", "A2"],
            "edad": [40, 52, 65, 72],
            "sexo": [1, 2, 1, 2],
            "anios_con_diabetes": [3, 8, 15, 25],
            "insulina_diaria": [0, 0, 1, 1],
            "depresion": [0, 1, 0, 1],
            "consultas_control_12m": [1, 2, 4, 5],
            "num_hospitalizaciones": [0, 0, 1, 2],
            "num_complicaciones": [0, 1, 2, 3],
            "score_riesgo": [1, 3, 5, 7],
            "categoria_riesgo": ["bajo", "medio", "alto", "alto"],
        }
    )


def crear_entorno():
    return DiabetesFollowUpEnv(
        cohorte(), capacidad_mensual=6, horizonte=2, seed=123
    )


def test_discretizacion_conserva_tres_niveles_de_riesgo():
    agente = QLearningAgent(seed=1)
    estados = []
    env = crear_entorno()
    obs, _ = env.reset(seed=1)
    while True:
        estados.append(agente.discretizar(obs)[0])
        obs, _, terminado, truncado, _ = env.step(0)
        if terminado or truncado:
            break
    assert set(estados) == {0, 1, 2}


def test_actualizacion_q_learning_aplica_bellman():
    agente = QLearningAgent(
        alpha=0.5, gamma=0.9, epsilon=0.0, epsilon_min=0.0, seed=1
    )
    obs = np.zeros(13, dtype=np.float32)
    siguiente = np.zeros(13, dtype=np.float32)
    siguiente[12] = 1.0
    agente.q_table[agente.discretizar(siguiente)][2] = 4.0
    agente.actualizar(obs, 1, 2.0, siguiente, terminado=False)
    valor = agente.q_table[agente.discretizar(obs)][1]
    assert np.isclose(valor, 0.5 * (2.0 + 0.9 * 4.0))


def test_entrenamiento_es_reproducible_y_respeta_capacidad():
    agente_1, historial_1 = entrenar_q_learning(
        crear_entorno, episodios=8, semilla=2026, epsilon_decay=0.9
    )
    agente_2, historial_2 = entrenar_q_learning(
        crear_entorno, episodios=8, semilla=2026, epsilon_decay=0.9
    )
    pd.testing.assert_frame_equal(historial_1, historial_2)
    pd.testing.assert_frame_equal(
        agente_1.tabla_dataframe(), agente_2.tabla_dataframe()
    )

    evaluacion = evaluar_politica_detallada(
        crear_entorno(), crear_politica_q_learning(agente_1), "Q-learning", [42]
    )
    detalle = evaluacion["detalle"]
    assert (detalle["recursos_despues"] >= 0).all()
    assert (detalle["recursos_usados_mes"] <= detalle["capacidad_mensual"]).all()
    assert detalle["accion_propuesta"].isin([0, 1, 2, 3]).all()


def test_tabla_q_es_exportable():
    agente, _ = entrenar_q_learning(crear_entorno, episodios=2, semilla=7)
    tabla = agente.tabla_dataframe()
    assert set(tabla.columns) == {
        "riesgo_ordinal", "bin_score", "bin_sin_contacto", "bin_mes",
        "bin_recursos", "accion", "q_value",
    }
    assert not tabla.empty


def test_guardar_y_cargar_conserva_tabla_q(tmp_path):
    agente, _ = entrenar_q_learning(crear_entorno, episodios=3, semilla=11)
    ruta = tmp_path / "q_learning.npz"
    agente.guardar(ruta)
    recuperado = QLearningAgent.cargar(ruta, seed=11)
    pd.testing.assert_frame_equal(
        agente.tabla_dataframe(), recuperado.tabla_dataframe()
    )
