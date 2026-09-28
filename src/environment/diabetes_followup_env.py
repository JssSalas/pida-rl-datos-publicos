"""Entorno Gymnasium para priorización mensual de seguimiento en diabetes."""

from collections.abc import Mapping

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from src.config import ACTION_LABELS, DEFAULT_ACTION_COSTS, DEFAULT_MONTHLY_CAPACITY


class DiabetesFollowUpEnv(gym.Env):
    """Simula decisiones mensuales con capacidad operativa estricta.

    Cada paso corresponde a un perfil. El algoritmo propone una acción de 0 a 3;
    el entorno ejecuta la acción más intensa que no supere la propuesta y que sea
    viable con los recursos restantes. El simulador es metodológico y no prescribe
    atención clínica individual.
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        cohorte_df,
        capacidad_mensual=DEFAULT_MONTHLY_CAPACITY,
        costos_accion=None,
        horizonte=12,
        seed=None,
    ):
        super().__init__()
        if len(cohorte_df) == 0:
            raise ValueError("La cohorte no puede estar vacía.")
        if int(horizonte) < 1:
            raise ValueError("El horizonte debe ser al menos un mes.")

        self.cohorte_base = cohorte_df.reset_index(drop=True).copy()
        self.n_perfiles = len(self.cohorte_base)
        self.capacidad_mensual = self._normalizar_capacidad(capacidad_mensual)
        self.horizonte = int(horizonte)
        self.costo_accion = self._validar_costos(costos_accion or DEFAULT_ACTION_COSTS)
        self._rng = np.random.default_rng(seed)

        # Ocho variables originales más la fracción de recursos disponibles.
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(9,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(4)

    def _normalizar_capacidad(self, capacidad):
        """Acepta unidades enteras o una proporción heredada entre 0 y 1."""
        if isinstance(capacidad, (float, np.floating)) and 0 < capacidad <= 1:
            return max(1, int(round(self.n_perfiles * float(capacidad))))
        if isinstance(capacidad, (int, np.integer)) and int(capacidad) >= 0:
            return int(capacidad)
        raise ValueError(
            "capacidad_mensual debe ser un entero no negativo o una proporción en (0, 1]."
        )

    @staticmethod
    def _validar_costos(costos):
        if not isinstance(costos, Mapping) or set(costos) != set(ACTION_LABELS):
            raise ValueError("costos_accion debe definir exactamente las acciones 0, 1, 2 y 3.")
        normalizados = {int(a): int(c) for a, c in costos.items()}
        if normalizados[0] != 0 or any(c < 0 for c in normalizados.values()):
            raise ValueError("La acción 0 debe costar 0 y ningún costo puede ser negativo.")
        if any(normalizados[a] > normalizados[a + 1] for a in range(3)):
            raise ValueError("Los costos deben ser no decrecientes con la intensidad.")
        return normalizados

    @property
    def recursos_restantes(self):
        return self.presupuesto_mensual - self.recursos_usados_mes

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._rng = np.random.default_rng(seed)

        self.cohorte = self.cohorte_base.copy()
        self.cohorte["meses_sin_contacto"] = 0
        self.mes_actual = 1
        self.presupuesto_mensual = self.capacidad_mensual
        self.recursos_usados_mes = 0
        self.idx_actual = 0

        return self._get_obs(self.idx_actual), {
            "mes": self.mes_actual,
            "n_perfiles": self.n_perfiles,
            "capacidad_mensual": self.presupuesto_mensual,
            "recursos_restantes": self.recursos_restantes,
        }

    def _get_obs(self, idx):
        row = self.cohorte.iloc[idx]
        riesgo_map = {"bajo": 0.0, "medio": 0.5, "alto": 1.0}
        fraccion_recursos = (
            self.recursos_restantes / self.presupuesto_mensual
            if self.presupuesto_mensual > 0
            else 0.0
        )
        return np.array(
            [
                np.clip(float(row["edad"]) / 100.0, 0.0, 1.0),
                np.clip(float(row["sexo"]), 0.0, 1.0),
                np.clip(float(row["anios_con_diabetes"]) / 50.0, 0.0, 1.0),
                np.clip(float(row["num_complicaciones"]) / 9.0, 0.0, 1.0),
                np.clip(float(row["num_comorbilidades"]) / 2.0, 0.0, 1.0),
                riesgo_map.get(row["categoria_riesgo"], 0.0),
                np.clip(float(row["meses_sin_contacto"]) / 12.0, 0.0, 1.0),
                np.clip(float(self.mes_actual) / self.horizonte, 0.0, 1.0),
                np.clip(fraccion_recursos, 0.0, 1.0),
            ],
            dtype=np.float32,
        )

    def _resolver_accion(self, accion_propuesta):
        """Reduce intensidad hasta encontrar una acción pagable."""
        for accion in range(int(accion_propuesta), -1, -1):
            if self.costo_accion[accion] <= self.recursos_restantes:
                return accion
        return 0

    def _calcular_recompensa(self, nivel_riesgo, accion_ejecutada, evento_adverso):
        recompensa = 0.0
        if accion_ejecutada > 0:
            recompensa += {0: 0.10, 1: 1.0, 2: 3.0}[nivel_riesgo]
        else:
            recompensa -= {0: 0.0, 1: 0.5, 2: 1.5}[nivel_riesgo]
        if evento_adverso:
            recompensa -= 5.0
        return recompensa

    def step(self, action):
        if not self.action_space.contains(action):
            raise ValueError("La acción debe ser un entero entre 0 y 3.")

        accion_propuesta = int(action)
        mes_decision = self.mes_actual
        indice_decision = self.idx_actual
        row = self.cohorte.iloc[indice_decision]
        recursos_antes = self.recursos_restantes

        accion_ejecutada = self._resolver_accion(accion_propuesta)
        costo_real = self.costo_accion[accion_ejecutada]
        self.recursos_usados_mes += costo_real
        recursos_despues = self.recursos_restantes

        riesgo_map = {"bajo": 0, "medio": 1, "alto": 2}
        nivel_riesgo = riesgo_map.get(row["categoria_riesgo"], 0)
        meses_sin_contacto = float(row["meses_sin_contacto"])
        prob_evento_base = (
            0.02 + 0.03 * nivel_riesgo + min(0.005 * meses_sin_contacto, 0.05)
        )
        reduccion = {0: 0.0, 1: 0.30, 2: 0.60, 3: 0.85}[accion_ejecutada]
        prob_evento = np.clip(prob_evento_base * (1 - reduccion), 0.0, 1.0)
        evento_adverso = bool(self._rng.random() < prob_evento)
        reward = self._calcular_recompensa(
            nivel_riesgo, accion_ejecutada, evento_adverso
        )

        if accion_ejecutada == 0:
            self.cohorte.loc[indice_decision, "meses_sin_contacto"] += 1
        else:
            self.cohorte.loc[indice_decision, "meses_sin_contacto"] = 0

        self.idx_actual += 1
        terminated = False
        truncated = False
        if self.idx_actual >= self.n_perfiles:
            self.idx_actual = 0
            self.mes_actual += 1
            if self.mes_actual > self.horizonte:
                terminated = True
            else:
                self.recursos_usados_mes = 0

        obs = (
            self._get_obs(self.idx_actual)
            if not terminated
            else np.zeros(self.observation_space.shape, dtype=np.float32)
        )
        perfil_id = row.get("patient_id", row.get("perfil_id", indice_decision))
        info = {
            "perfil_id": perfil_id,
            "indice_perfil": indice_decision,
            "mes": mes_decision,
            "categoria_riesgo": row["categoria_riesgo"],
            "accion_propuesta": accion_propuesta,
            "accion_propuesta_nombre": ACTION_LABELS[accion_propuesta],
            "accion_ejecutada": accion_ejecutada,
            "accion_ejecutada_nombre": ACTION_LABELS[accion_ejecutada],
            "accion_ajustada": accion_propuesta != accion_ejecutada,
            "motivo_ajuste": (
                "capacidad_insuficiente"
                if accion_propuesta != accion_ejecutada
                else None
            ),
            "costo_propuesto": self.costo_accion[accion_propuesta],
            "costo_real": costo_real,
            "recursos_antes": recursos_antes,
            "recursos_despues": recursos_despues,
            "recursos_usados_mes": self.presupuesto_mensual - recursos_despues,
            "capacidad_mensual": self.presupuesto_mensual,
            "evento_adverso": evento_adverso,
            "prob_evento": float(prob_evento),
            "excede_capacidad": False,
        }
        return obs, reward, terminated, truncated, info
