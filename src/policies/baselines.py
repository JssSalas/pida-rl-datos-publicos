"""Políticas de referencia para comparar agentes de aprendizaje por refuerzo."""


def politica_aleatoria(env):
    """Selecciona 0-3 con igual probabilidad y de forma reproducible por semilla."""
    return int(env._policy_rng.integers(0, env.action_space.n))


def politica_por_reglas(env):
    """Mapeo clínico-operativo simple usado como línea base, no como prescripción."""
    riesgo = str(env.cohorte.iloc[env.idx_actual]["categoria_riesgo"])
    return {"bajo": 0, "medio": 1, "alto": 2}[riesgo]


POLITICAS_BASE = {
    "Aleatoria": politica_aleatoria,
    "Reglas de riesgo": politica_por_reglas,
}
