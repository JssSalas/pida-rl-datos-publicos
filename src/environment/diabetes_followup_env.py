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
    viable con los recursos restantes. Es un simulador metodológico, no un sistema
    de recomendación clínica individual.
    """

    metadata = {"render_modes": []}
    RIESGO_ORDINAL = {"bajo": 0, "medio": 1, "alto": 2}
    COLUMNAS_REQUERIDAS = [
        "edad",
        "sexo",
        "anios_con_diabetes",
        "insulina_diaria",
        "depresion",
        "consultas_control_12m",
        "num_hospitalizaciones",
        "num_complicaciones",
        "score_riesgo",
        "categoria_riesgo",
    ]
    COLUMNAS_NUMERICAS = [
        "edad",
        "sexo",
        "anios_con_diabetes",
        "insulina_diaria",
        "depresion",
        "consultas_control_12m",
        "num_hospitalizaciones",
        "num_complicaciones",
        "score_riesgo",
    ]

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
        faltantes = [c for c in self.COLUMNAS_REQUERIDAS if c not in cohorte_df.columns]
        if faltantes:
            raise KeyError("Faltan columnas en la cohorte: " + ", ".join(faltantes))

        self.cohorte_base = cohorte_df.reset_index(drop=True).copy()
        valores = self.cohorte_base[self.COLUMNAS_NUMERICAS].to_numpy(dtype=float)
        if not np.isfinite(valores).all():
            raise ValueError("La cohorte contiene valores numéricos faltantes o infinitos.")
        if not self.cohorte_base["categoria_riesgo"].isin({"bajo", "medio", "alto"}).all():
            raise ValueError("categoria_riesgo solo admite bajo, medio o alto.")

        self.n_perfiles = len(self.cohorte_base)
        # Copias NumPy de la cohorte: evitan accesos fila a fila con pandas en cada paso.
        # Los valores son los mismos; solo cambia la forma de leerlos.
        self._valores = {c: self.cohorte_base[c].to_numpy(dtype=float) for c in self.COLUMNAS_NUMERICAS}
        self._categoria = self.cohorte_base["categoria_riesgo"].astype(str).to_numpy()
        self._nivel = np.array([self.RIESGO_ORDINAL[c] for c in self._categoria], dtype=int)
        self._ids = None
        for columna_id in ("FOLIO_INT", "patient_id", "perfil_id"):
            if columna_id in self.cohorte_base.columns:
                self._ids = self.cohorte_base[columna_id].to_numpy(dtype=object)
                break
        self._meses_sin_contacto = np.zeros(self.n_perfiles, dtype=np.int64)
        self._cohorte_df = None
        self._cohorte_sincronizada = False
        self.capacidad_mensual = self._normalizar_capacidad(capacidad_mensual)
        self.horizonte = int(horizonte)
        self.costo_accion = self._validar_costos(costos_accion or DEFAULT_ACTION_COSTS)
        self._rng = np.random.default_rng(seed)
        self._policy_rng = np.random.default_rng(None if seed is None else int(seed) + 1)

        # Nueve variables de perfil, riesgo, historial, tiempo y recursos.
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(13,), dtype=np.float32
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

    @staticmethod
    def _norm(valor, denominador):
        # min/max en lugar de np.clip: mismo resultado para escalares y mucho más rápido.
        return min(max(float(valor) / max(float(denominador), 1.0), 0.0), 1.0)

    @property
    def cohorte(self):
        """Cohorte con ``meses_sin_contacto`` actualizado (compatible con las versiones previas)."""
        if self._cohorte_df is None:
            self._cohorte_df = self.cohorte_base.copy()
            self._cohorte_sincronizada = False
        if not self._cohorte_sincronizada:
            self._cohorte_df["meses_sin_contacto"] = self._meses_sin_contacto.copy()
            self._cohorte_sincronizada = True
        return self._cohorte_df

    @cohorte.setter
    def cohorte(self, frame):
        self._cohorte_df = frame
        if "meses_sin_contacto" in frame.columns:
            self._meses_sin_contacto = frame["meses_sin_contacto"].to_numpy(dtype=np.int64).copy()
        self._cohorte_sincronizada = True

    def perfil(self, idx):
        """Devuelve el perfil ``idx`` como diccionario, con el mismo contenido que una fila de ``cohorte``."""
        fila = {c: self._valores[c][idx] for c in self.COLUMNAS_NUMERICAS}
        fila["categoria_riesgo"] = self._categoria[idx]
        fila["meses_sin_contacto"] = int(self._meses_sin_contacto[idx])
        if self._ids is not None:
            fila["FOLIO_INT"] = self._ids[idx]
        return fila

    @property
    def recursos_restantes(self):
        return self.presupuesto_mensual - self.recursos_usados_mes

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._rng = np.random.default_rng(seed)
            self._policy_rng = np.random.default_rng(int(seed) + 1)

        self._meses_sin_contacto = np.zeros(self.n_perfiles, dtype=np.int64)
        self._cohorte_df = None
        self._cohorte_sincronizada = False
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
        row = self.perfil(idx)
        riesgo_ordinal = self.RIESGO_ORDINAL
        fraccion_recursos = (
            self.recursos_restantes / self.presupuesto_mensual
            if self.presupuesto_mensual > 0
            else 0.0
        )
        sexo_normalizado = 0.0 if float(row["sexo"]) == 1.0 else 1.0
        return np.array(
            [
                self._norm(row["edad"], 100),
                sexo_normalizado,
                self._norm(row["anios_con_diabetes"], 80),
                min(max(float(row["insulina_diaria"]), 0.0), 1.0),
                min(max(float(row["depresion"]), 0.0), 1.0),
                self._norm(row["consultas_control_12m"], 24),
                self._norm(row["num_hospitalizaciones"], 12),
                self._norm(row["num_complicaciones"], 5),
                self._norm(row["score_riesgo"], 16),
                riesgo_ordinal[str(row["categoria_riesgo"])] / 2.0,
                self._norm(row["meses_sin_contacto"], self.horizonte),
                self._norm(self.mes_actual, self.horizonte),
                min(max(float(fraccion_recursos), 0.0), 1.0),
            ],
            dtype=np.float32,
        )

    def _resolver_accion(self, accion_propuesta):
        """Reduce intensidad hasta encontrar una acción pagable."""
        for accion in range(int(accion_propuesta), -1, -1):
            if self.costo_accion[accion] <= self.recursos_restantes:
                return accion
        return 0

    def _probabilidad_evento(self, row, nivel_riesgo, accion_ejecutada):
        base = (
            0.01
            + 0.025 * nivel_riesgo
            + 0.010 * float(row["num_complicaciones"])
            + 0.020 * float(row["num_hospitalizaciones"] > 0)
            + 0.005 * min(float(row["meses_sin_contacto"]), 6)
        )
        reduccion = {0: 0.00, 1: 0.20, 2: 0.45, 3: 0.65}[accion_ejecutada]
        return min(max(float(base * (1 - reduccion)), 0.0), 0.80)

    @staticmethod
    def _calcular_recompensa(nivel_riesgo, accion_ejecutada, evento_adverso):
        recompensa = 0.0
        if accion_ejecutada > 0:
            recompensa += {1: 0.5, 2: 1.0, 3: 1.5}[accion_ejecutada] * (
                nivel_riesgo + 1
            )
        else:
            recompensa -= {0: 0.0, 1: 0.5, 2: 1.5}[nivel_riesgo]
        if evento_adverso:
            recompensa -= 5.0
        return float(recompensa)

    def step(self, action):
        if not self.action_space.contains(action):
            raise ValueError("La acción debe ser un entero entre 0 y 3.")

        accion_propuesta = int(action)
        mes_decision = self.mes_actual
        indice_decision = self.idx_actual
        row = self.perfil(indice_decision)
        recursos_antes = self.recursos_restantes

        accion_ejecutada = self._resolver_accion(accion_propuesta)
        costo_real = self.costo_accion[accion_ejecutada]
        self.recursos_usados_mes += costo_real
        recursos_despues = self.recursos_restantes

        nivel_riesgo = int(self._nivel[indice_decision])
        prob_evento = self._probabilidad_evento(row, nivel_riesgo, accion_ejecutada)
        evento_adverso = bool(self._rng.random() < prob_evento)
        reward = self._calcular_recompensa(
            nivel_riesgo, accion_ejecutada, evento_adverso
        )

        if accion_ejecutada == 0:
            self._meses_sin_contacto[indice_decision] += 1
        else:
            self._meses_sin_contacto[indice_decision] = 0
        self._cohorte_sincronizada = False

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
        perfil_id = self._ids[indice_decision] if self._ids is not None else indice_decision
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
            "prob_evento": prob_evento,
            "excede_capacidad": False,
        }
        return obs, reward, terminated, truncated, info
