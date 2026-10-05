"""Pruebas V2.16: orden de atención aleatorio por mes y descuento mensual."""

import numpy as np
import pandas as pd

from src.environment.diabetes_followup_env import DiabetesFollowUpEnv
from src.policies.dqn import DQNAgent
from src.policies.ppo import calcular_gae
from src.policies.q_learning import QLearningAgent, factor_descuento


def cohorte(n=6):
    return pd.DataFrame({
        "FOLIO_INT": [f"P{i:03d}" for i in range(n)],
        "edad": [50 + i for i in range(n)],
        "sexo": [1, 2] * (n // 2),
        "anios_con_diabetes": [5] * n,
        "insulina_diaria": [0] * n,
        "depresion": [0] * n,
        "consultas_control_12m": [2] * n,
        "num_hospitalizaciones": [0] * n,
        "num_complicaciones": [1] * n,
        "score_riesgo": [3 + i for i in range(n)],
        "categoria_riesgo": (["bajo", "medio", "alto"] * n)[:n],
    })


def recorrido(env, seed):
    env.reset(seed=seed)
    meses, fin = {}, []
    while True:
        _, _, terminado, _, info = env.step(0)
        meses.setdefault(info["mes"], []).append(info["indice_perfil"])
        fin.append(info["fin_mes"])
        if terminado:
            return meses, fin


def test_cada_mes_atiende_a_todos_una_sola_vez():
    meses, _ = recorrido(DiabetesFollowUpEnv(cohorte(), 3, horizonte=3), seed=7)
    assert sorted(meses) == [1, 2, 3]
    for indices in meses.values():
        assert sorted(indices) == list(range(6))


def test_orden_es_reproducible_y_cambia_entre_meses():
    a, _ = recorrido(DiabetesFollowUpEnv(cohorte(), 3, horizonte=4), seed=11)
    b, _ = recorrido(DiabetesFollowUpEnv(cohorte(), 3, horizonte=4), seed=11)
    assert a == b
    assert len({tuple(v) for v in a.values()}) > 1


def test_orden_fijo_disponible():
    meses, _ = recorrido(DiabetesFollowUpEnv(cohorte(), 3, horizonte=2, orden_aleatorio=False), seed=1)
    assert meses[1] == meses[2] == list(range(6))


def test_orden_no_altera_la_secuencia_de_eventos():
    """El orden usa su propio generador: los eventos de los perfiles siguen el mismo flujo aleatorio."""
    env = DiabetesFollowUpEnv(cohorte(), 3, horizonte=1)
    env.reset(seed=5)
    assert env._rng.random() == np.random.default_rng(5).random()


def test_fin_mes_marca_la_ultima_decision_de_cada_mes():
    _, fin = recorrido(DiabetesFollowUpEnv(cohorte(), 3, horizonte=3), seed=2)
    assert fin == ([False] * 5 + [True]) * 3


def test_factor_descuento():
    assert factor_descuento(0.95, "mensual", False) == 1.0
    assert factor_descuento(0.95, "mensual", True) == 0.95
    assert factor_descuento(0.95, "decision", False) == 0.95


def test_q_learning_mensual_no_descuenta_dentro_del_mes():
    agente = QLearningAgent(alpha=1.0, gamma=0.5, descuento="mensual")
    obs = np.zeros(13, dtype=np.float32)
    agente.q_table[agente.discretizar(obs)][:] = 10.0
    agente.actualizar(obs, 0, 1.0, obs, terminado=False, fin_mes=False)
    assert agente.q_table[agente.discretizar(obs)][0] == 11.0
    agente.actualizar(obs, 1, 1.0, obs, terminado=False, fin_mes=True)
    assert agente.q_table[agente.discretizar(obs)][1] == 1.0 + 0.5 * 11.0


def test_descuento_se_guarda_y_carga(tmp_path):
    q = QLearningAgent(descuento="mensual")
    q.guardar(tmp_path / "q.npz")
    assert QLearningAgent.cargar(tmp_path / "q.npz").descuento == "mensual"
    d = DQNAgent(descuento="mensual")
    d.guardar(tmp_path / "d.npz")
    assert DQNAgent.cargar(tmp_path / "d.npz").descuento == "mensual"


def test_gae_acepta_descuento_por_transicion():
    r = np.array([1.0, 1.0], dtype=np.float32)
    v = np.zeros(2, dtype=np.float32)
    nv = np.array([0.0, 2.0], dtype=np.float32)
    d = np.zeros(2, dtype=np.float32)
    adv, _ = calcular_gae(r, v, nv, d, gamma=np.array([1.0, 0.5]), gae_lambda=1.0)
    assert np.allclose(adv, [1.0 + 1.0 * (1.0 + 0.5 * 2.0), 1.0 + 0.5 * 2.0])
