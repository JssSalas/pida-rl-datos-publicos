
import numpy as np
import gymnasium as gym
from gymnasium import spaces


class DiabetesFollowUpEnv(gym.Env):
    """Entorno de simulación de seguimiento mensual a perfiles de diabetes.

    Basado en variables derivadas de ENSANUT Continua 2022.
    No representa datos clínicos reales ni recomendaciones individuales.
    """

    metadata = {"render_modes": []}

    def __init__(self, cohorte_df, capacidad_mensual=0.20, horizonte=12, seed=None):
        super().__init__()
        self.cohorte_base = cohorte_df.reset_index(drop=True)
        self.n_perfiles = len(self.cohorte_base)
        self.capacidad_mensual = capacidad_mensual
        self.horizonte = horizonte
        self._rng = np.random.default_rng(seed)

        # Espacio de observación: vector por perfil (simplificado, un perfil a la vez)
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(8,), dtype=np.float32
        )

        # Espacio de acción: 4 niveles de intensidad de seguimiento
        self.action_space = spaces.Discrete(4)

        self.costo_accion = {0: 0, 1: 1, 2: 2, 3: 3}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.cohorte = self.cohorte_base.copy()
        self.cohorte["meses_sin_contacto"] = 0
        self.mes_actual = 1
        self.presupuesto_mensual = int(self.n_perfiles * self.capacidad_mensual)
        self.recursos_usados_mes = 0
        self.idx_actual = 0

        obs = self._get_obs(self.idx_actual)
        info = {"mes": self.mes_actual, "n_perfiles": self.n_perfiles}
        return obs, info

    def _get_obs(self, idx):
        row = self.cohorte.iloc[idx]
        riesgo_map = {"bajo": 0.0, "medio": 0.5, "alto": 1.0}
        obs = np.array([
            row["edad"] / 100.0,
            row["sexo"],
            min(row["anios_con_diabetes"] / 50.0, 1.0),
            min(row["num_complicaciones"] / 9.0, 1.0),
            min(row["num_comorbilidades"] / 2.0, 1.0),
            riesgo_map.get(row["categoria_riesgo"], 0.0),
            min(row["meses_sin_contacto"] / 12.0, 1.0),
            self.mes_actual / self.horizonte,
        ], dtype=np.float32)
        return obs

    def step(self, action):
        costo = self.costo_accion[action]
        excede_capacidad = (self.recursos_usados_mes + costo) > self.presupuesto_mensual

        row = self.cohorte.iloc[self.idx_actual]
        riesgo_map_val = {"bajo": 0, "medio": 1, "alto": 2}
        nivel_riesgo = riesgo_map_val.get(row["categoria_riesgo"], 0)

        prob_evento_base = 0.02 + 0.03 * nivel_riesgo
        reduccion_por_accion = {0: 0.0, 1: 0.3, 2: 0.6, 3: 0.85}
        prob_evento = prob_evento_base * (1 - reduccion_por_accion[action])

        evento_adverso = self._rng.random() < prob_evento

        reward = 0.0
        if action >= 2 and nivel_riesgo == 2:
            reward += 2.0
        if evento_adverso:
            reward -= 5.0
        if excede_capacidad:
            reward -= 3.0
        else:
            self.recursos_usados_mes += costo

        if action == 0:
            self.cohorte.loc[self.idx_actual, "meses_sin_contacto"] += 1
        else:
            self.cohorte.loc[self.idx_actual, "meses_sin_contacto"] = 0

        self.idx_actual += 1
        terminated = False
        truncated = False

        if self.idx_actual >= self.n_perfiles:
            self.idx_actual = 0
            self.mes_actual += 1
            self.recursos_usados_mes = 0
            if self.mes_actual > self.horizonte:
                terminated = True

        obs = self._get_obs(self.idx_actual) if not terminated else np.zeros(8, dtype=np.float32)
        info = {
            "mes": self.mes_actual,
            "evento_adverso": evento_adverso,
            "excede_capacidad": excede_capacidad,
        }

        return obs, reward, terminated, truncated, info
