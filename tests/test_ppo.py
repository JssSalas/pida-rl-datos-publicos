import numpy as np
import pandas as pd

from src.environment.diabetes_followup_env import DiabetesFollowUpEnv
from src.evaluation.evaluate_policies import evaluar_politica_detallada
from src.policies.ppo import (
    ActorCriticNetwork, PPOAgent, calcular_gae, crear_politica_ppo, entrenar_ppo,
)


def cohort():
    return pd.DataFrame({
        "FOLIO_INT": ["B", "M", "A"], "edad": [40, 55, 70], "sexo": [1, 2, 1],
        "anios_con_diabetes": [2, 9, 20], "insulina_diaria": [0, 0, 1],
        "depresion": [0, 1, 0], "consultas_control_12m": [1, 2, 5],
        "num_hospitalizaciones": [0, 0, 2], "num_complicaciones": [0, 1, 3],
        "score_riesgo": [1, 3, 7], "categoria_riesgo": ["bajo", "medio", "alto"],
    })


def factory():
    return DiabetesFollowUpEnv(cohort(), capacidad_mensual=5, horizonte=2, seed=3)


def test_actor_critic_outputs_valid_probabilities_and_values():
    net = ActorCriticNetwork(hidden_sizes=(8, 8), seed=1)
    probs, values = net.predict(np.ones((4, 13), dtype=np.float32))
    assert probs.shape == (4, 4)
    assert values.shape == (4,)
    np.testing.assert_allclose(probs.sum(axis=1), 1.0)
    assert (probs >= 0).all()


def test_gae_respects_terminal_boundaries():
    advantages, returns = calcular_gae(
        rewards=[1, 1], values=[0, 0], next_values=[0, 100], dones=[0, 1],
        gamma=1.0, gae_lambda=1.0,
    )
    np.testing.assert_allclose(advantages, [2, 1])
    np.testing.assert_allclose(returns, [2, 1])


def test_training_reproducible_and_capacity_safe():
    kwargs = dict(
        pasos_totales=48, rollout_steps=12, semilla=91, hidden_sizes=(8, 8),
        update_epochs=2, minibatch_size=6, max_kl=0,
    )
    a1, h1 = entrenar_ppo(factory, **kwargs)
    a2, h2 = entrenar_ppo(factory, **kwargs)
    pd.testing.assert_frame_equal(h1, h2)
    for name in a1.network.params:
        np.testing.assert_allclose(a1.network.params[name], a2.network.params[name])
    result = evaluar_politica_detallada(factory(), crear_politica_ppo(a1), "PPO", [42])
    detail = result["detalle"]
    assert set(detail["categoria_riesgo"]) == {"bajo", "medio", "alto"}
    assert set(detail["accion_propuesta"]) <= {0, 1, 2, 3}
    assert (detail["recursos_despues"] >= 0).all()
    assert (detail["recursos_usados_mes"] <= detail["capacidad_mensual"]).all()


def test_ppo_update_changes_parameters_and_reports_metrics():
    agent = PPOAgent(hidden_sizes=(8, 8), update_epochs=2, minibatch_size=4, max_kl=0, seed=7)
    states = np.zeros((8, 13), dtype=np.float32)
    actions, logs, values = [], [], []
    for state in states:
        action, logp, value = agent.seleccionar_accion(state)
        actions.append(action)
        logs.append(logp)
        values.append(value)
    before = {k: v.copy() for k, v in agent.network.params.items()}
    metrics = agent.actualizar({
        "states": states, "actions": actions, "log_probs": logs,
        "rewards": np.ones(8), "values": values,
        "next_values": np.zeros(8), "dones": np.ones(8),
    })
    assert any(not np.allclose(before[k], agent.network.params[k]) for k in before)
    assert {"loss_total", "loss_politica", "loss_valor", "entropia", "kl_aproximada"} <= set(metrics)


def test_save_load_preserves_predictions(tmp_path):
    agent, _ = entrenar_ppo(
        factory, pasos_totales=24, rollout_steps=12, semilla=8,
        hidden_sizes=(8, 8), update_epochs=1, minibatch_size=6, max_kl=0,
    )
    path = tmp_path / "ppo.npz"
    obs, _ = factory().reset(seed=2)
    expected = agent.network.predict(obs)
    agent.guardar(path)
    loaded = PPOAgent.cargar(path, seed=8)
    actual = loaded.network.predict(obs)
    np.testing.assert_allclose(expected[0], actual[0])
    np.testing.assert_allclose(expected[1], actual[1])
