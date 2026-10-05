"""Q-learning tabular para el entorno de seguimiento con capacidad estricta."""

from collections import defaultdict

import numpy as np
import pandas as pd

DESCUENTOS = ("mensual", "decision")


def factor_descuento(gamma, descuento, fin_mes):
    """Descuento aplicado a una transición.

    ``mensual`` sigue la formulación del PIDA (γ^t con t = mes): las decisiones
    dentro de un mes no se descuentan entre sí y γ se aplica al pasar de mes.
    ``decision`` reproduce la versión anterior (γ en cada decisión).
    """
    if descuento == "decision":
        return float(gamma)
    return float(gamma) if fin_mes else 1.0


class QLearningAgent:
    """Agente tabular epsilon-greedy con una representación compacta del estado."""

    def __init__(
        self,
        n_actions=4,
        alpha=0.10,
        gamma=0.95,
        epsilon=1.0,
        epsilon_min=0.05,
        epsilon_decay=0.995,
        seed=2026,
        descuento="mensual",
    ):
        if descuento not in DESCUENTOS:
            raise ValueError("descuento debe ser 'mensual' o 'decision'.")
        if int(n_actions) != 4:
            raise ValueError("El proyecto requiere exactamente cuatro acciones (0-3).")
        if not 0 < alpha <= 1:
            raise ValueError("alpha debe estar en (0, 1].")
        if not 0 <= gamma <= 1:
            raise ValueError("gamma debe estar en [0, 1].")
        if not 0 <= epsilon_min <= epsilon <= 1:
            raise ValueError("Se requiere 0 <= epsilon_min <= epsilon <= 1.")
        if not 0 < epsilon_decay <= 1:
            raise ValueError("epsilon_decay debe estar en (0, 1].")

        self.n_actions = int(n_actions)
        self.alpha = float(alpha)
        self.gamma = float(gamma)
        self.descuento = descuento
        self.epsilon = float(epsilon)
        self.epsilon_min = float(epsilon_min)
        self.epsilon_decay = float(epsilon_decay)
        self.rng = np.random.default_rng(seed)
        self.q_table = defaultdict(lambda: np.zeros(self.n_actions, dtype=np.float64))

    @staticmethod
    def _bin_unit(valor, n_bins):
        valor = min(max(float(valor), 0.0), 1.0)
        return min(int(valor * n_bins), n_bins - 1)

    def discretizar(self, observacion):
        """Resume riesgo y contexto operativo sin crear otra categoría de riesgo.

        El estado tabular contiene: riesgo bajo/medio/alto, quintil del score,
        meses sin contacto, trimestre simulado y quintil de recursos restantes.
        """
        obs = np.asarray(observacion, dtype=float)
        if obs.shape != (13,):
            raise ValueError("La observación debe contener 13 elementos.")
        riesgo = min(max(int(round(float(obs[9]) * 2)), 0), 2)
        return (
            riesgo,
            self._bin_unit(obs[8], 5),
            self._bin_unit(obs[10], 4),
            self._bin_unit(obs[11], 4),
            self._bin_unit(obs[12], 5),
        )

    def seleccionar_accion(self, observacion, explorar=True):
        estado = self.discretizar(observacion)
        if explorar and self.rng.random() < self.epsilon:
            return int(self.rng.integers(self.n_actions))
        valores = self.q_table[estado]
        mejores = np.flatnonzero(valores == valores.max())
        return int(self.rng.choice(mejores))

    def actualizar(self, observacion, accion, recompensa, siguiente_observacion, terminado, fin_mes=True):
        estado = self.discretizar(observacion)
        siguiente = self.discretizar(siguiente_observacion)
        objetivo = float(recompensa)
        if not terminado:
            g = factor_descuento(self.gamma, self.descuento, fin_mes)
            objetivo += g * float(self.q_table[siguiente].max())
        error = objetivo - self.q_table[estado][int(accion)]
        self.q_table[estado][int(accion)] += self.alpha * error

    def reducir_exploracion(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def accion_greedy(self, observacion):
        return self.seleccionar_accion(observacion, explorar=False)

    def guardar(self, ruta):
        """Guarda tabla Q e hiperparámetros sin serialización ejecutable."""
        estados = np.array(list(self.q_table.keys()), dtype=np.int16)
        valores = np.array(list(self.q_table.values()), dtype=np.float64)
        if estados.size == 0:
            estados = np.empty((0, 5), dtype=np.int16)
            valores = np.empty((0, self.n_actions), dtype=np.float64)
        np.savez_compressed(
            ruta,
            estados=estados,
            valores=valores,
            n_actions=self.n_actions,
            alpha=self.alpha,
            gamma=self.gamma,
            descuento=self.descuento,
            epsilon=self.epsilon,
            epsilon_min=self.epsilon_min,
            epsilon_decay=self.epsilon_decay,
        )

    @classmethod
    def cargar(cls, ruta, seed=2026):
        """Reconstruye un agente desde un archivo NPZ generado por ``guardar``."""
        with np.load(ruta, allow_pickle=False) as datos:
            agente = cls(
                n_actions=int(datos["n_actions"]),
                alpha=float(datos["alpha"]),
                gamma=float(datos["gamma"]),
                epsilon=float(datos["epsilon"]),
                epsilon_min=float(datos["epsilon_min"]),
                epsilon_decay=float(datos["epsilon_decay"]),
                seed=seed,
                descuento=str(datos["descuento"]) if "descuento" in datos.files else "decision",
            )
            for estado, valores in zip(datos["estados"], datos["valores"]):
                agente.q_table[tuple(int(x) for x in estado)] = valores.astype(float)
        return agente

    def tabla_dataframe(self):
        filas = []
        for estado, valores in sorted(self.q_table.items()):
            for accion, valor in enumerate(valores):
                filas.append(
                    {
                        "riesgo_ordinal": estado[0],
                        "bin_score": estado[1],
                        "bin_sin_contacto": estado[2],
                        "bin_mes": estado[3],
                        "bin_recursos": estado[4],
                        "accion": accion,
                        "q_value": float(valor),
                    }
                )
        return pd.DataFrame(filas)


def entrenar_q_learning(
    env_factory,
    episodios=1500,
    semilla=10000,
    alpha=0.10,
    gamma=0.95,
    epsilon=1.0,
    epsilon_min=0.05,
    epsilon_decay=0.995,
    descuento="mensual",
):
    """Entrena Q-learning y devuelve el agente junto con su historial auditable."""
    if int(episodios) < 1:
        raise ValueError("episodios debe ser al menos 1.")
    agente = QLearningAgent(
        alpha=alpha,
        gamma=gamma,
        epsilon=epsilon,
        epsilon_min=epsilon_min,
        epsilon_decay=epsilon_decay,
        seed=semilla,
        descuento=descuento,
    )
    historial = []

    for episodio in range(int(episodios)):
        env = env_factory()
        observacion, _ = env.reset(seed=int(semilla) + episodio)
        recompensa_total = 0.0
        pasos = 0
        eventos = 0
        ajustes = 0
        recursos = 0

        while True:
            accion = agente.seleccionar_accion(observacion, explorar=True)
            siguiente, recompensa, terminado, truncado, info = env.step(accion)
            fin = bool(terminado or truncado)
            agente.actualizar(observacion, accion, recompensa, siguiente, fin, info.get("fin_mes", True))
            observacion = siguiente
            recompensa_total += float(recompensa)
            pasos += 1
            eventos += int(info["evento_adverso"])
            ajustes += int(info["accion_ajustada"])
            recursos += int(info["costo_real"])
            if fin:
                break

        historial.append(
            {
                "episodio": episodio + 1,
                "semilla": int(semilla) + episodio,
                "recompensa_acumulada": recompensa_total,
                "pasos": pasos,
                "eventos_adversos": eventos,
                "ajustes_capacidad": ajustes,
                "recursos_usados": recursos,
                "epsilon": agente.epsilon,
                "estados_visitados": len(agente.q_table),
            }
        )
        agente.reducir_exploracion()

    return agente, pd.DataFrame(historial)


def crear_politica_q_learning(agente):
    """Adapta el agente entrenado a la interfaz común de evaluación."""
    def politica(env):
        observacion = env._get_obs(env.idx_actual).copy()
        return agente.accion_greedy(observacion)

    politica.__name__ = "politica_q_learning"
    return politica
