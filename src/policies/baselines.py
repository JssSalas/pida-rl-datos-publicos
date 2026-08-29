
import numpy as np


def politica_aleatoria(env, seed=None):
    rng = np.random.default_rng(seed)
    return int(rng.integers(0, env.action_space.n))


def politica_por_reglas(env):
    row = env.cohorte.iloc[env.idx_actual]
    riesgo = row["categoria_riesgo"]

    if riesgo == "alto":
        return 2
    elif riesgo == "medio":
        return 1
    else:
        return 0
