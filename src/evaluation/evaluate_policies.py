
import numpy as np

def evaluar_politica(env, politica, semillas):
    resultados = []

    for semilla in semillas:
        obs, info = env.reset(seed=semilla)

        recompensa_total = 0.0
        pasos = 0
        eventos_adversos = 0
        excesos_capacidad = 0
        contactos = 0
        recursos_usados_mes=0

        while True:
            accion = politica(env)
            obs, reward, terminated, truncated, info = env.step(accion)

            recompensa_total += float(reward)
            pasos += 1

#Corrección contador
            if accion > 0:
                contactos += int(info["accion_aceptada"] and accion > 0)
#Fin de corrección contador

            eventos_adversos += int(info["evento_adverso"])
            excesos_capacidad += int(info["excede_capacidad"])

            if terminated or truncated:
                break

        resultados.append({
            "semilla": semilla,
            "recompensa_acumulada": recompensa_total,
            "pasos": pasos,
            "contactos": contactos,
            "eventos_adversos": eventos_adversos,
            "excesos_capacidad": excesos_capacidad,
            "recursos_usados_mes": recursos_usados_mes
        })

    return resultados
