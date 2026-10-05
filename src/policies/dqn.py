"""DQN reproducible con NumPy para el entorno de seguimiento V2."""

from collections import deque

import numpy as np
import pandas as pd

from src.policies.q_learning import DESCUENTOS, factor_descuento


class ReplayBuffer:
    """Buffer circular preasignado para experiencias de aprendizaje."""

    def __init__(self, capacity, observation_dim=13):
        if int(capacity) < 1:
            raise ValueError("capacity debe ser al menos 1.")
        self.capacity = int(capacity)
        self.observation_dim = int(observation_dim)
        self.states = np.zeros((self.capacity, self.observation_dim), dtype=np.float32)
        self.actions = np.zeros(self.capacity, dtype=np.int64)
        self.rewards = np.zeros(self.capacity, dtype=np.float32)
        self.next_states = np.zeros_like(self.states)
        self.dones = np.zeros(self.capacity, dtype=np.float32)
        self.discounts = np.zeros(self.capacity, dtype=np.float32)
        self.size = 0
        self.position = 0

    def add(self, state, action, reward, next_state, done, discount=1.0):
        i = self.position
        self.states[i] = np.asarray(state, dtype=np.float32)
        self.actions[i] = int(action)
        self.rewards[i] = float(reward)
        self.next_states[i] = np.asarray(next_state, dtype=np.float32)
        self.dones[i] = float(bool(done))
        self.discounts[i] = float(discount)
        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size, rng):
        if self.size < int(batch_size):
            raise ValueError("No hay experiencias suficientes para el lote solicitado.")
        idx = rng.choice(self.size, size=int(batch_size), replace=False)
        return (
            self.states[idx], self.actions[idx], self.rewards[idx],
            self.next_states[idx], self.dones[idx], self.discounts[idx],
        )

    def __len__(self):
        return self.size


class DenseQNetwork:
    """MLP de dos capas ocultas con ReLU y optimizador Adam."""

    def __init__(self, input_dim=13, hidden_sizes=(64, 64), output_dim=4, seed=2026):
        h1, h2 = (int(x) for x in hidden_sizes)
        if min(int(input_dim), h1, h2, int(output_dim)) < 1:
            raise ValueError("Las dimensiones de la red deben ser positivas.")
        rng = np.random.default_rng(seed)
        self.params = {
            "w1": (rng.standard_normal((int(input_dim), h1)) * np.sqrt(2 / int(input_dim))).astype(np.float32),
            "b1": np.zeros(h1, dtype=np.float32),
            "w2": (rng.standard_normal((h1, h2)) * np.sqrt(2 / h1)).astype(np.float32),
            "b2": np.zeros(h2, dtype=np.float32),
            "w3": (rng.standard_normal((h2, int(output_dim))) * np.sqrt(2 / h2)).astype(np.float32),
            "b3": np.zeros(int(output_dim), dtype=np.float32),
        }
        self.m = {k: np.zeros_like(v) for k, v in self.params.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.params.items()}
        self.adam_step = 0
        self.input_dim = int(input_dim)
        self.hidden_sizes = (h1, h2)
        self.output_dim = int(output_dim)

    def _forward(self, x):
        x = np.asarray(x, dtype=np.float32)
        z1 = x @ self.params["w1"] + self.params["b1"]
        a1 = np.maximum(z1, 0)
        z2 = a1 @ self.params["w2"] + self.params["b2"]
        a2 = np.maximum(z2, 0)
        q = a2 @ self.params["w3"] + self.params["b3"]
        return q, (x, z1, a1, z2, a2)

    def predict(self, states):
        states = np.asarray(states, dtype=np.float32)
        if states.ndim == 1:
            states = states[None, :]
        return self._forward(states)[0]

    def train_batch(self, states, targets, learning_rate=1e-3, gradient_clip=10.0):
        q, cache = self._forward(states)
        targets = np.asarray(targets, dtype=np.float32)
        error = q - targets
        loss = float(np.mean(error ** 2))
        dq = (2.0 / error.size) * error
        x, z1, a1, z2, a2 = cache

        grads = {}
        grads["w3"] = a2.T @ dq
        grads["b3"] = dq.sum(axis=0)
        da2 = dq @ self.params["w3"].T
        dz2 = da2 * (z2 > 0)
        grads["w2"] = a1.T @ dz2
        grads["b2"] = dz2.sum(axis=0)
        da1 = dz2 @ self.params["w2"].T
        dz1 = da1 * (z1 > 0)
        grads["w1"] = x.T @ dz1
        grads["b1"] = dz1.sum(axis=0)

        norm = np.sqrt(sum(float(np.sum(g * g)) for g in grads.values()))
        if norm > float(gradient_clip):
            scale = float(gradient_clip) / (norm + 1e-8)
            grads = {k: g * scale for k, g in grads.items()}

        self.adam_step += 1
        beta1, beta2 = 0.9, 0.999
        for name, grad in grads.items():
            self.m[name] = beta1 * self.m[name] + (1 - beta1) * grad
            self.v[name] = beta2 * self.v[name] + (1 - beta2) * (grad * grad)
            m_hat = self.m[name] / (1 - beta1 ** self.adam_step)
            v_hat = self.v[name] / (1 - beta2 ** self.adam_step)
            self.params[name] -= float(learning_rate) * m_hat / (np.sqrt(v_hat) + 1e-8)
        return loss

    def copy_from(self, other):
        for name in self.params:
            self.params[name][...] = other.params[name]


class DQNAgent:
    """Agente DQN con replay, red objetivo y exploración epsilon-greedy."""

    def __init__(
        self, observation_dim=13, n_actions=4, hidden_sizes=(64, 64), gamma=0.95,
        learning_rate=1e-3, epsilon=1.0, epsilon_min=0.05,
        epsilon_decay=0.99995, replay_capacity=50000, warmup_steps=1000,
        target_update_frequency=500, seed=2026, descuento="mensual",
    ):
        if descuento not in DESCUENTOS:
            raise ValueError("descuento debe ser 'mensual' o 'decision'.")
        if int(observation_dim) != 13 or int(n_actions) != 4:
            raise ValueError("DQN V2 requiere 13 observaciones y cuatro acciones.")
        if not 0 <= gamma <= 1 or not 0 < learning_rate:
            raise ValueError("gamma o learning_rate inválidos.")
        if not 0 <= epsilon_min <= epsilon <= 1 or not 0 < epsilon_decay <= 1:
            raise ValueError("Configuración epsilon inválida.")
        if int(warmup_steps) < 0 or int(target_update_frequency) < 1:
            raise ValueError("warmup_steps o target_update_frequency inválidos.")
        self.observation_dim = 13
        self.n_actions = 4
        self.hidden_sizes = tuple(int(x) for x in hidden_sizes)
        self.gamma = float(gamma)
        self.descuento = descuento
        self.learning_rate = float(learning_rate)
        self.epsilon = float(epsilon)
        self.epsilon_min = float(epsilon_min)
        self.epsilon_decay = float(epsilon_decay)
        self.warmup_steps = int(warmup_steps)
        self.target_update_frequency = int(target_update_frequency)
        self.rng_action = np.random.default_rng(seed)
        self.rng_replay = np.random.default_rng(int(seed) + 1)
        self.online = DenseQNetwork(13, self.hidden_sizes, 4, seed)
        self.target = DenseQNetwork(13, self.hidden_sizes, 4, int(seed) + 2)
        self.target.copy_from(self.online)
        self.replay = ReplayBuffer(replay_capacity, 13)
        self.gradient_steps = 0

    def seleccionar_accion(self, observation, explorar=True):
        if explorar and self.rng_action.random() < self.epsilon:
            return int(self.rng_action.integers(self.n_actions))
        q = self.online.predict(observation)[0]
        mejores = np.flatnonzero(q == q.max())
        return int(self.rng_action.choice(mejores))

    def recordar(self, state, action, reward, next_state, done, fin_mes=True):
        g = factor_descuento(self.gamma, self.descuento, fin_mes)
        self.replay.add(state, action, reward, next_state, done, g)

    def aprender(self, batch_size=64):
        minimo = max(int(batch_size), self.warmup_steps)
        if len(self.replay) < minimo:
            return None
        states, actions, rewards, next_states, dones, discounts = self.replay.sample(batch_size, self.rng_replay)
        targets = self.online.predict(states).copy()
        futuros = self.target.predict(next_states).max(axis=1)
        objetivos = rewards + discounts * (1.0 - dones) * futuros
        targets[np.arange(len(actions)), actions] = objetivos
        loss = self.online.train_batch(states, targets, self.learning_rate)
        self.gradient_steps += 1
        if self.gradient_steps % self.target_update_frequency == 0:
            self.target.copy_from(self.online)
        return loss

    def reducir_exploracion(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def accion_greedy(self, observation):
        return self.seleccionar_accion(observation, explorar=False)

    def guardar(self, ruta):
        datos = {f"online_{k}": v for k, v in self.online.params.items()}
        datos.update({
            "hidden_sizes": np.asarray(self.hidden_sizes, dtype=np.int64),
            "gamma": np.asarray(self.gamma), "learning_rate": np.asarray(self.learning_rate),
            "epsilon": np.asarray(self.epsilon), "epsilon_min": np.asarray(self.epsilon_min),
            "epsilon_decay": np.asarray(self.epsilon_decay),
            "descuento": np.asarray(self.descuento),
        })
        np.savez_compressed(ruta, **datos)

    @classmethod
    def cargar(cls, ruta, seed=2026):
        with np.load(ruta, allow_pickle=False) as data:
            agent = cls(
                hidden_sizes=tuple(int(x) for x in data["hidden_sizes"]),
                gamma=float(data["gamma"]), learning_rate=float(data["learning_rate"]),
                epsilon=float(data["epsilon"]), epsilon_min=float(data["epsilon_min"]),
                epsilon_decay=float(data["epsilon_decay"]), seed=seed,
                descuento=str(data["descuento"]) if "descuento" in data.files else "decision",
            )
            for name in agent.online.params:
                agent.online.params[name][...] = data[f"online_{name}"]
            agent.target.copy_from(agent.online)
        return agent


def entrenar_dqn(
    env_factory, pasos_totales=100000, semilla=20000, hidden_sizes=(64, 64),
    gamma=0.95, learning_rate=1e-3, epsilon=1.0, epsilon_min=0.05,
    epsilon_decay=0.99995, replay_capacity=50000, warmup_steps=1000,
    batch_size=64, train_frequency=4, target_update_frequency=500,
    log_interval=1000, descuento="mensual",
):
    """Entrena por pasos y registra ventanas auditables sin fabricar datos."""
    if min(int(pasos_totales), int(batch_size), int(train_frequency), int(log_interval)) < 1:
        raise ValueError("pasos, batch, frecuencia y log_interval deben ser positivos.")
    agent = DQNAgent(
        hidden_sizes=hidden_sizes, gamma=gamma, learning_rate=learning_rate,
        epsilon=epsilon, epsilon_min=epsilon_min, epsilon_decay=epsilon_decay,
        replay_capacity=replay_capacity, warmup_steps=warmup_steps,
        target_update_frequency=target_update_frequency, seed=semilla,
        descuento=descuento,
    )
    env = env_factory()
    episode = 1
    observation, _ = env.reset(seed=int(semilla))
    losses = deque(maxlen=int(log_interval))
    window = {"reward": 0.0, "events": 0, "adjustments": 0, "resources": 0}
    history = []

    for step in range(1, int(pasos_totales) + 1):
        action = agent.seleccionar_accion(observation, explorar=True)
        next_observation, reward, terminated, truncated, info = env.step(action)
        done = bool(terminated or truncated)
        agent.recordar(observation, action, reward, next_observation, done, info.get("fin_mes", True))
        if step % int(train_frequency) == 0:
            loss = agent.aprender(batch_size)
            if loss is not None:
                losses.append(loss)
        agent.reducir_exploracion()
        window["reward"] += float(reward)
        window["events"] += int(info["evento_adverso"])
        window["adjustments"] += int(info["accion_ajustada"])
        window["resources"] += int(info["costo_real"])
        observation = next_observation

        if done:
            episode += 1
            observation, _ = env.reset(seed=int(semilla) + episode - 1)
        if step % int(log_interval) == 0 or step == int(pasos_totales):
            history.append({
                "paso": step, "episodio": episode,
                "recompensa_ventana": window["reward"],
                "eventos_adversos_ventana": window["events"],
                "ajustes_capacidad_ventana": window["adjustments"],
                "recursos_usados_ventana": window["resources"],
                "loss_promedio": float(np.mean(losses)) if losses else np.nan,
                "epsilon": agent.epsilon, "replay_size": len(agent.replay),
                "gradient_steps": agent.gradient_steps,
            })
            window = {"reward": 0.0, "events": 0, "adjustments": 0, "resources": 0}
    return agent, pd.DataFrame(history)


def crear_politica_dqn(agent):
    """Adapta DQN greedy a la interfaz común de evaluación."""
    def policy(env):
        return agent.accion_greedy(env._get_obs(env.idx_actual).copy())
    policy.__name__ = "politica_dqn"
    return policy
