"""Políticas de referencia para comparar agentes de aprendizaje por refuerzo."""


def politica_aleatoria(env):
    """Selecciona 0-3 con igual probabilidad y de forma reproducible por semilla."""
    return int(env._policy_rng.integers(0, env.action_space.n))


def politica_por_reglas(env):
    """Mapeo operativo simple usado como línea base, no como prescripción clínica."""
    riesgo = str(env.cohorte.iloc[env.idx_actual]["categoria_riesgo"])
    return {"bajo": 0, "medio": 1, "alto": 2}[riesgo]


def crear_politica_reglas_escalonadas(umbral_teleorientacion=6):
    """Crea una regla de intensidad sin añadir una cuarta categoría de riesgo.

    La cohorte conserva exclusivamente las categorías bajo, medio y alto. El
    ``score_riesgo`` solo gradúa la acción propuesta dentro de medio y alto:

    - bajo: acción 0;
    - medio: acción 1 si score <= 2, en otro caso acción 2;
    - alto: acción 2 si score < umbral, en otro caso acción 3.

    El umbral es un supuesto operativo configurable del simulador y no un punto
    de corte clínico validado.
    """
    umbral = int(umbral_teleorientacion)
    if umbral < 4:
        raise ValueError("umbral_teleorientacion debe ser al menos 4.")

    def politica(env):
        row = env.cohorte.iloc[env.idx_actual]
        riesgo = str(row["categoria_riesgo"])
        score = float(row["score_riesgo"])
        if riesgo == "bajo":
            return 0
        if riesgo == "medio":
            return 1 if score <= 2 else 2
        if riesgo == "alto":
            return 2 if score < umbral else 3
        raise ValueError(f"Categoría de riesgo no reconocida: {riesgo}")

    politica.__name__ = f"politica_reglas_escalonadas_umbral_{umbral}"
    return politica


politica_reglas_escalonadas = crear_politica_reglas_escalonadas(6)


POLITICAS_BASE = {
    "Aleatoria": politica_aleatoria,
    "Reglas simples": politica_por_reglas,
    "Reglas escalonadas": politica_reglas_escalonadas,
}
