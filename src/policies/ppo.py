"""PPO reproducible con actor-crítico NumPy para el entorno de seguimiento V2."""

import numpy as np
import pandas as pd

from src.policies.q_learning import DESCUENTOS, factor_descuento


class ActorCriticNetwork:
    """MLP compartida con cabezas de política categórica y valor, optimizada con Adam."""

    def __init__(self, input_dim=13, hidden_sizes=(64, 64), n_actions=4, seed=2026):
        h1, h2 = (int(x) for x in hidden_sizes)
        if int(input_dim) != 13 or int(n_actions) != 4 or min(h1, h2) < 1:
            raise ValueError("PPO V2 requiere 13 entradas, capas positivas y cuatro acciones.")
        rng = np.random.default_rng(seed)
        self.input_dim, self.hidden_sizes, self.n_actions = 13, (h1, h2), 4
        self.params = {
            "w1": (rng.standard_normal((13, h1)) * np.sqrt(2 / 13)).astype(np.float32),
            "b1": np.zeros(h1, dtype=np.float32),
            "w2": (rng.standard_normal((h1, h2)) * np.sqrt(2 / h1)).astype(np.float32),
            "b2": np.zeros(h2, dtype=np.float32),
            "wp": (rng.standard_normal((h2, 4)) * 0.01).astype(np.float32),
            "bp": np.zeros(4, dtype=np.float32),
            "wv": (rng.standard_normal((h2, 1)) * 1 / np.sqrt(h2)).astype(np.float32),
            "bv": np.zeros(1, dtype=np.float32),
        }
        self.m = {k: np.zeros_like(v) for k, v in self.params.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.params.items()}
        self.adam_step = 0

    @staticmethod
    def _softmax(logits):
        shifted = logits - logits.max(axis=1, keepdims=True)
        exp = np.exp(shifted)
        return exp / exp.sum(axis=1, keepdims=True)

    def _forward(self, states):
        x = np.asarray(states, dtype=np.float32)
        if x.ndim == 1:
            x = x[None, :]
        if x.shape[1] != 13:
            raise ValueError("Cada observación debe contener 13 variables.")
        z1 = x @ self.params["w1"] + self.params["b1"]
        a1 = np.maximum(z1, 0)
        z2 = a1 @ self.params["w2"] + self.params["b2"]
        a2 = np.maximum(z2, 0)
        logits = a2 @ self.params["wp"] + self.params["bp"]
        probs = self._softmax(logits)
        values = (a2 @ self.params["wv"] + self.params["bv"]).ravel()
        return probs, values, (x, z1, a1, z2, a2)

    def predict(self, states):
        probs, values, _ = self._forward(states)
        return probs, values

    def train_batch(
        self, states, actions, old_log_probs, advantages, returns,
        clip_ratio=0.2, value_coef=0.5, entropy_coef=0.01,
        learning_rate=3e-4, gradient_clip=0.5,
    ):
        probs, values, cache = self._forward(states)
        actions = np.asarray(actions, dtype=np.int64)
        old_log_probs = np.asarray(old_log_probs, dtype=np.float32)
        advantages = np.asarray(advantages, dtype=np.float32)
        returns = np.asarray(returns, dtype=np.float32)
        n = len(actions)
        selected = np.clip(probs[np.arange(n), actions], 1e-8, 1.0)
        log_probs = np.log(selected)
        ratios = np.exp(log_probs - old_log_probs)
        clipped = np.clip(ratios, 1 - float(clip_ratio), 1 + float(clip_ratio))
        surrogate = np.minimum(ratios * advantages, clipped * advantages)
        policy_loss = -float(np.mean(surrogate))
        value_error = values - returns
        value_loss = float(np.mean(value_error ** 2))
        log_all = np.log(np.clip(probs, 1e-8, 1.0))
        entropy_each = -np.sum(probs * log_all, axis=1)
        entropy = float(np.mean(entropy_each))
        total_loss = policy_loss + float(value_coef) * value_loss - float(entropy_coef) * entropy

        active = ((advantages >= 0) & (ratios <= 1 + float(clip_ratio))) | (
            (advantages < 0) & (ratios >= 1 - float(clip_ratio))
        )
        dlogp = -(advantages * ratios * active.astype(np.float32)) / n
        one_hot = np.zeros_like(probs)
        one_hot[np.arange(n), actions] = 1.0
        dlogits = dlogp[:, None] * (one_hot - probs)
        dlogits += (float(entropy_coef) / n) * probs * (log_all + entropy_each[:, None])
        dvalues = (2.0 * float(value_coef) / n) * value_error

        x, z1, a1, z2, a2 = cache
        grads = {
            "wp": a2.T @ dlogits,
            "bp": dlogits.sum(axis=0),
            "wv": a2.T @ dvalues[:, None],
            "bv": np.array([dvalues.sum()], dtype=np.float32),
        }
        da2 = dlogits @ self.params["wp"].T + dvalues[:, None] @ self.params["wv"].T
        dz2 = da2 * (z2 > 0)
        grads["w2"] = a1.T @ dz2
        grads["b2"] = dz2.sum(axis=0)
        da1 = dz2 @ self.params["w2"].T
        dz1 = da1 * (z1 > 0)
        grads["w1"] = x.T @ dz1
        grads["b1"] = dz1.sum(axis=0)

        grad_norm = np.sqrt(sum(float(np.sum(g * g)) for g in grads.values()))
        if grad_norm > float(gradient_clip):
            scale = float(gradient_clip) / (grad_norm + 1e-8)
            grads = {k: g * scale for k, g in grads.items()}

        self.adam_step += 1
        beta1, beta2 = 0.9, 0.999
        for name, grad in grads.items():
            self.m[name] = beta1 * self.m[name] + (1 - beta1) * grad
            self.v[name] = beta2 * self.v[name] + (1 - beta2) * (grad * grad)
            m_hat = self.m[name] / (1 - beta1 ** self.adam_step)
            v_hat = self.v[name] / (1 - beta2 ** self.adam_step)
            self.params[name] -= float(learning_rate) * m_hat / (np.sqrt(v_hat) + 1e-8)
        approx_kl = float(np.mean(old_log_probs - log_probs))
        clip_fraction = float(np.mean(np.abs(ratios - 1.0) > float(clip_ratio)))
        return {
            "loss_total": total_loss, "loss_politica": policy_loss,
            "loss_valor": value_loss, "entropia": entropy,
            "kl_aproximada": approx_kl, "fraccion_recortada": clip_fraction,
        }


def calcular_gae(rewards, values, next_values, dones, gamma=0.95, gae_lambda=0.95):
    """Calcula ventajas generalizadas y retornos respetando finales de episodio.

    ``gamma`` puede ser un escalar o un arreglo con el descuento de cada transición
    (descuento mensual: 1 dentro del mes y γ al cerrar el mes).
    """
    rewards = np.asarray(rewards, dtype=np.float32)
    values = np.asarray(values, dtype=np.float32)
    next_values = np.asarray(next_values, dtype=np.float32)
    dones = np.asarray(dones, dtype=np.float32)
    if not (rewards.shape == values.shape == next_values.shape == dones.shape):
        raise ValueError("Las series de GAE deben tener la misma forma.")
    gammas = np.broadcast_to(np.asarray(gamma, dtype=np.float32), rewards.shape)
    advantages = np.zeros_like(rewards)
    gae = 0.0
    for t in range(len(rewards) - 1, -1, -1):
        mask = 1.0 - dones[t]
        g = float(gammas[t])
        delta = rewards[t] + g * next_values[t] * mask - values[t]
        gae = delta + g * float(gae_lambda) * mask * gae
        advantages[t] = gae
    return advantages, advantages + values


class PPOAgent:
    """Agente PPO discreto con política actor-crítico compartida."""

    def __init__(
        self, observation_dim=13, n_actions=4, hidden_sizes=(64, 64), gamma=0.95,
        gae_lambda=0.95, clip_ratio=0.2, learning_rate=3e-4,
        value_coef=0.5, entropy_coef=0.01, update_epochs=10,
        minibatch_size=64, max_kl=0.03, seed=2026, descuento="mensual",
    ):
        if descuento not in DESCUENTOS:
            raise ValueError("descuento debe ser 'mensual' o 'decision'.")
        if int(observation_dim) != 13 or int(n_actions) != 4:
            raise ValueError("PPO V2 requiere 13 observaciones y cuatro acciones.")
        if not 0 <= gamma <= 1 or not 0 <= gae_lambda <= 1:
            raise ValueError("gamma y gae_lambda deben pertenecer a [0, 1].")
        if not 0 < clip_ratio < 1 or learning_rate <= 0:
            raise ValueError("clip_ratio o learning_rate inválidos.")
        if min(int(update_epochs), int(minibatch_size)) < 1:
            raise ValueError("update_epochs y minibatch_size deben ser positivos.")
        self.observation_dim, self.n_actions = 13, 4
        self.hidden_sizes = tuple(int(x) for x in hidden_sizes)
        self.gamma, self.gae_lambda = float(gamma), float(gae_lambda)
        self.descuento = descuento
        self.clip_ratio, self.learning_rate = float(clip_ratio), float(learning_rate)
        self.value_coef, self.entropy_coef = float(value_coef), float(entropy_coef)
        self.update_epochs, self.minibatch_size = int(update_epochs), int(minibatch_size)
        self.max_kl = float(max_kl)
        self.rng = np.random.default_rng(seed)
        self.network = ActorCriticNetwork(13, self.hidden_sizes, 4, seed)
        self.updates = 0

    def seleccionar_accion(self, observation, determinista=False):
        probs, values = self.network.predict(observation)
        p = probs[0]
        action = int(np.argmax(p)) if determinista else int(self.rng.choice(4, p=p))
        return action, float(np.log(max(p[action], 1e-8))), float(values[0])

    def valor(self, observation):
        return float(self.network.predict(observation)[1][0])

    def actualizar(self, rollout):
        states = np.asarray(rollout["states"], dtype=np.float32)
        actions = np.asarray(rollout["actions"], dtype=np.int64)
        old_log_probs = np.asarray(rollout["log_probs"], dtype=np.float32)
        advantages, returns = calcular_gae(
            rollout["rewards"], rollout["values"], rollout["next_values"],
            rollout["dones"], rollout.get("discounts", self.gamma), self.gae_lambda,
        )
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        metrics = []
        stopped_early = False
        n = len(states)
        for _ in range(self.update_epochs):
            permutation = self.rng.permutation(n)
            for start in range(0, n, self.minibatch_size):
                idx = permutation[start:start + self.minibatch_size]
                m = self.network.train_batch(
                    states[idx], actions[idx], old_log_probs[idx], advantages[idx], returns[idx],
                    self.clip_ratio, self.value_coef, self.entropy_coef, self.learning_rate,
                )
                metrics.append(m)
                if self.max_kl > 0 and m["kl_aproximada"] > self.max_kl:
                    stopped_early = True
                    break
            if stopped_early:
                break
        self.updates += 1
        summary = {k: float(np.mean([m[k] for m in metrics])) for k in metrics[0]}
        summary["actualizacion_temprana"] = stopped_early
        summary["ventaja_media"] = float(advantages.mean())
        summary["retorno_medio"] = float(returns.mean())
        return summary

    def accion_determinista(self, observation):
        return self.seleccionar_accion(observation, determinista=True)[0]

    def guardar(self, ruta):
        data = {f"param_{k}": v for k, v in self.network.params.items()}
        data.update({
            "hidden_sizes": np.asarray(self.hidden_sizes, dtype=np.int64),
            "gamma": np.asarray(self.gamma), "gae_lambda": np.asarray(self.gae_lambda),
            "clip_ratio": np.asarray(self.clip_ratio), "learning_rate": np.asarray(self.learning_rate),
            "value_coef": np.asarray(self.value_coef), "entropy_coef": np.asarray(self.entropy_coef),
            "update_epochs": np.asarray(self.update_epochs), "minibatch_size": np.asarray(self.minibatch_size),
            "max_kl": np.asarray(self.max_kl), "descuento": np.asarray(self.descuento),
        })
        np.savez_compressed(ruta, **data)

    @classmethod
    def cargar(cls, ruta, seed=2026):
        with np.load(ruta, allow_pickle=False) as data:
            agent = cls(
                hidden_sizes=tuple(int(x) for x in data["hidden_sizes"]),
                gamma=float(data["gamma"]), gae_lambda=float(data["gae_lambda"]),
                clip_ratio=float(data["clip_ratio"]), learning_rate=float(data["learning_rate"]),
                value_coef=float(data["value_coef"]), entropy_coef=float(data["entropy_coef"]),
                update_epochs=int(data["update_epochs"]), minibatch_size=int(data["minibatch_size"]),
                max_kl=float(data["max_kl"]), seed=seed,
                descuento=str(data["descuento"]) if "descuento" in data.files else "decision",
            )
            for name in agent.network.params:
                agent.network.params[name][...] = data[f"param_{name}"]
        return agent


def entrenar_ppo(
    env_factory, pasos_totales=100000, rollout_steps=2048, semilla=30000,
    hidden_sizes=(64, 64), gamma=0.95, gae_lambda=0.95, clip_ratio=0.2,
    learning_rate=3e-4, value_coef=0.5, entropy_coef=0.01,
    update_epochs=10, minibatch_size=64, max_kl=0.03, descuento="mensual",
):
    """Entrena PPO con rollouts on-policy y devuelve historial auditable por actualización."""
    if min(int(pasos_totales), int(rollout_steps)) < 1:
        raise ValueError("pasos_totales y rollout_steps deben ser positivos.")
    agent = PPOAgent(
        hidden_sizes=hidden_sizes, gamma=gamma, gae_lambda=gae_lambda,
        clip_ratio=clip_ratio, learning_rate=learning_rate, value_coef=value_coef,
        entropy_coef=entropy_coef, update_epochs=update_epochs,
        minibatch_size=minibatch_size, max_kl=max_kl, seed=semilla,
        descuento=descuento,
    )
    env = env_factory()
    episode = 1
    observation, _ = env.reset(seed=int(semilla))
    total_steps = 0
    history = []
    while total_steps < int(pasos_totales):
        size = min(int(rollout_steps), int(pasos_totales) - total_steps)
        rollout = {k: [] for k in (
            "states", "actions", "log_probs", "rewards", "values", "next_values", "dones",
            "discounts",
        )}
        window = {"reward": 0.0, "events": 0, "adjustments": 0, "resources": 0}
        for _ in range(size):
            action, log_prob, value = agent.seleccionar_accion(observation)
            next_observation, reward, terminated, truncated, info = env.step(action)
            done = bool(terminated or truncated)
            next_value = 0.0 if done else agent.valor(next_observation)
            rollout["states"].append(observation.copy())
            rollout["actions"].append(action)
            rollout["log_probs"].append(log_prob)
            rollout["rewards"].append(float(reward))
            rollout["values"].append(value)
            rollout["next_values"].append(next_value)
            rollout["dones"].append(float(done))
            rollout["discounts"].append(factor_descuento(agent.gamma, agent.descuento, info.get("fin_mes", True)))
            window["reward"] += float(reward)
            window["events"] += int(info["evento_adverso"])
            window["adjustments"] += int(info["accion_ajustada"])
            window["resources"] += int(info["costo_real"])
            total_steps += 1
            if done:
                episode += 1
                observation, _ = env.reset(seed=int(semilla) + episode - 1)
            else:
                observation = next_observation
        metrics = agent.actualizar(rollout)
        history.append({
            "paso": total_steps, "episodio": episode, "actualizacion": agent.updates,
            "recompensa_rollout": window["reward"],
            "eventos_adversos_rollout": window["events"],
            "ajustes_capacidad_rollout": window["adjustments"],
            "recursos_usados_rollout": window["resources"], **metrics,
        })
    return agent, pd.DataFrame(history)


def crear_politica_ppo(agent):
    """Adapta PPO determinista a la interfaz común de evaluación."""
    def policy(env):
        return agent.accion_determinista(env._get_obs(env.idx_actual).copy())
    policy.__name__ = "politica_ppo"
    return policy
