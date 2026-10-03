import numpy as np
import pandas as pd

from src.environment.diabetes_followup_env import DiabetesFollowUpEnv
from src.evaluation.evaluate_policies import evaluar_politica_detallada
from src.policies.dqn import DQNAgent, DenseQNetwork, ReplayBuffer, crear_politica_dqn, entrenar_dqn


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


def test_network_shape_and_learning_changes_predictions():
    net = DenseQNetwork(hidden_sizes=(8, 8), seed=1)
    x = np.ones((4, 13), dtype=np.float32)
    before = net.predict(x).copy()
    target = before.copy()
    target[:, 2] += 2
    for _ in range(10):
        net.train_batch(x, target, learning_rate=0.01)
    assert net.predict(x).shape == (4, 4)
    assert not np.allclose(before, net.predict(x))


def test_replay_buffer_is_circular():
    replay = ReplayBuffer(3)
    for i in range(5):
        replay.add(np.full(13, i), i % 4, i, np.full(13, i + 1), False)
    assert len(replay) == 3
    assert set(replay.rewards.tolist()) == {2.0, 3.0, 4.0}


def test_training_reproducible_and_capacity_safe():
    kwargs = dict(
        pasos_totales=80, semilla=91, hidden_sizes=(8, 8), replay_capacity=50,
        warmup_steps=8, batch_size=8, train_frequency=2,
        target_update_frequency=5, log_interval=20, epsilon_decay=0.97,
    )
    a1, h1 = entrenar_dqn(factory, **kwargs)
    a2, h2 = entrenar_dqn(factory, **kwargs)
    pd.testing.assert_frame_equal(h1, h2)
    for name in a1.online.params:
        np.testing.assert_allclose(a1.online.params[name], a2.online.params[name])
    result = evaluar_politica_detallada(factory(), crear_politica_dqn(a1), "DQN", [42])
    detail = result["detalle"]
    assert set(detail["categoria_riesgo"]) == {"bajo", "medio", "alto"}
    assert (detail["recursos_despues"] >= 0).all()
    assert (detail["recursos_usados_mes"] <= detail["capacidad_mensual"]).all()


def test_target_network_updates_on_schedule():
    agent = DQNAgent(hidden_sizes=(8, 8), warmup_steps=4, replay_capacity=20,
                     target_update_frequency=2, epsilon=0, epsilon_min=0, seed=5)
    s = np.zeros(13, dtype=np.float32)
    for i in range(8):
        agent.recordar(s, i % 4, 1, s, False)
    agent.aprender(4)
    assert any(not np.allclose(agent.online.params[k], agent.target.params[k]) for k in agent.online.params)
    agent.aprender(4)
    for name in agent.online.params:
        np.testing.assert_allclose(agent.online.params[name], agent.target.params[name])


def test_save_load_preserves_predictions(tmp_path):
    agent, _ = entrenar_dqn(
        factory, pasos_totales=30, semilla=8, hidden_sizes=(8, 8),
        replay_capacity=30, warmup_steps=4, batch_size=4, train_frequency=2,
        target_update_frequency=3, log_interval=10,
    )
    path = tmp_path / "dqn.npz"
    obs, _ = factory().reset(seed=2)
    expected = agent.online.predict(obs)
    agent.guardar(path)
    loaded = DQNAgent.cargar(path, seed=8)
    np.testing.assert_allclose(expected, loaded.online.predict(obs))
