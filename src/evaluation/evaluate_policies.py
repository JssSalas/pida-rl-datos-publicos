"""Evaluación reproducible de políticas y registro por decisión."""

import pandas as pd


COLUMNAS_DETALLE = [
    "algoritmo",
    "semilla",
    "paso",
    "mes",
    "perfil_id",
    "indice_perfil",
    "categoria_riesgo",
    "accion_propuesta",
    "accion_propuesta_nombre",
    "accion_ejecutada",
    "accion_ejecutada_nombre",
    "accion_ajustada",
    "motivo_ajuste",
    "costo_propuesto",
    "costo_real",
    "recursos_antes",
    "recursos_despues",
    "recursos_usados_mes",
    "capacidad_mensual",
    "evento_adverso",
    "prob_evento",
    "recompensa",
]


def evaluar_politica_detallada(env, politica, nombre_politica, semillas):
    """Evalúa una política y devuelve detalle y resumen por episodio.

    Parameters
    ----------
    env:
        Instancia de ``DiabetesFollowUpEnv``.
    politica:
        Callable que recibe el entorno y devuelve una acción entre 0 y 3.
    nombre_politica:
        Etiqueta que aparecerá en los reportes.
    semillas:
        Semillas usadas para repetir exactamente el protocolo de evaluación.
    """
    detalle = []
    episodios = []

    for semilla in semillas:
        env.reset(seed=int(semilla))
        paso = 0
        recompensa_total = 0.0
        eventos_adversos = 0
        ajustes_capacidad = 0
        contactos_propuestos = 0
        contactos_ejecutados = 0
        recursos_usados = 0
        decisiones_alto_riesgo = 0
        contactos_alto_riesgo = 0
        meses_observados = set()

        while True:
            accion = int(politica(env))
            _, reward, terminated, truncated, info = env.step(accion)
            paso += 1
            recompensa_total += float(reward)
            eventos_adversos += int(info["evento_adverso"])
            ajustes_capacidad += int(info["accion_ajustada"])
            contactos_propuestos += int(info["accion_propuesta"] > 0)
            contactos_ejecutados += int(info["accion_ejecutada"] > 0)
            recursos_usados += int(info["costo_real"])
            meses_observados.add(int(info["mes"]))

            if info["categoria_riesgo"] == "alto":
                decisiones_alto_riesgo += 1
                contactos_alto_riesgo += int(info["accion_ejecutada"] > 0)

            fila = {
                "algoritmo": nombre_politica,
                "semilla": int(semilla),
                "paso": paso,
                "recompensa": float(reward),
            }
            fila.update({col: info.get(col) for col in COLUMNAS_DETALLE if col not in fila})
            detalle.append(fila)

            if terminated or truncated:
                break

        capacidad_total = env.capacidad_mensual * len(meses_observados)
        episodios.append(
            {
                "algoritmo": nombre_politica,
                "semilla": int(semilla),
                "recompensa_acumulada": recompensa_total,
                "pasos": paso,
                "contactos_propuestos": contactos_propuestos,
                "contactos_ejecutados": contactos_ejecutados,
                "eventos_adversos": eventos_adversos,
                "ajustes_capacidad": ajustes_capacidad,
                "recursos_usados": recursos_usados,
                "capacidad_total": capacidad_total,
                "utilizacion_capacidad": (
                    recursos_usados / capacidad_total if capacidad_total > 0 else 0.0
                ),
                "cobertura_alto_riesgo": (
                    contactos_alto_riesgo / decisiones_alto_riesgo
                    if decisiones_alto_riesgo > 0
                    else 0.0
                ),
            }
        )

    return {
        "detalle": pd.DataFrame(detalle, columns=COLUMNAS_DETALLE),
        "episodios": pd.DataFrame(episodios),
    }


def evaluar_politicas(env_factory, politicas, semillas=(42, 123, 2026)):
    """Evalúa varias políticas bajo el mismo entorno y las mismas semillas."""
    detalles = []
    episodios = []
    for nombre, politica in politicas.items():
        resultado = evaluar_politica_detallada(
            env=env_factory(),
            politica=politica,
            nombre_politica=nombre,
            semillas=semillas,
        )
        detalles.append(resultado["detalle"])
        episodios.append(resultado["episodios"])
    return {
        "detalle": pd.concat(detalles, ignore_index=True),
        "episodios": pd.concat(episodios, ignore_index=True),
    }


def evaluar_politica(env, politica, semillas):
    """Mantiene la interfaz histórica y devuelve una lista por semilla."""
    resultado = evaluar_politica_detallada(
        env=env,
        politica=politica,
        nombre_politica=getattr(politica, "__name__", "politica"),
        semillas=semillas,
    )
    episodios = resultado["episodios"].copy()
    episodios["contactos"] = episodios["contactos_ejecutados"]
    episodios["excesos_capacidad"] = 0
    columnas_historicas = [
        "semilla",
        "recompensa_acumulada",
        "pasos",
        "contactos",
        "eventos_adversos",
        "excesos_capacidad",
    ]
    return episodios[columnas_historicas].to_dict(orient="records")
