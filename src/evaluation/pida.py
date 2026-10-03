"""Evaluación de cumplimiento de los criterios de éxito de la Definición del PIDA.

El módulo no modifica el entorno ni las políticas. Añade:

- una evaluación ligera por episodio, para al menos 100 episodios sin guardar la traza completa;
- intervalos de confianza al 95 % (aproximación normal y bootstrap percentil);
- escenarios de robustez de capacidad, costos y transición;
- brechas de cobertura por sexo y grupo de edad;
- una tabla de criterios con el umbral, el valor observado y si se cumple.

Los resultados comparan políticas dentro de un simulador. No demuestran efectividad clínica.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import NormalDist

import numpy as np
import pandas as pd

from src.config import DEFAULT_ACTION_COSTS, DEFAULT_MONTHLY_CAPACITY
from src.environment.diabetes_followup_env import DiabetesFollowUpEnv

GRUPOS_EDAD = ("18-44", "45-64", "65_y_mas")
UMBRAL_BRECHA_PP = 10.0
META_MEJORA_ASPIRACIONAL = 0.10
META_ROBUSTEZ = 0.80
EPISODIOS_MINIMOS = 100
SEMILLAS_BASE_PIDA = tuple(range(5000, 5100))       # 100 episodios en el escenario base
SEMILLAS_ROBUSTEZ_PIDA = tuple(range(5000, 5020))   # 20 episodios por escenario de robustez


class EntornoSensibilidadTransicion(DiabetesFollowUpEnv):
    """Variante del entorno V2 para el análisis de sensibilidad de la transición.

    ``factor_riesgo_base`` escala la probabilidad basal de evento adverso.
    ``factor_efecto_contacto`` escala la reducción relativa que produce cada acción.
    Con ambos factores en 1.0, el comportamiento es idéntico al entorno V2.
    """

    def __init__(self, *args, factor_riesgo_base=1.0, factor_efecto_contacto=1.0, **kwargs):
        if factor_riesgo_base <= 0 or factor_efecto_contacto < 0:
            raise ValueError("Los factores de sensibilidad deben ser positivos.")
        self.factor_riesgo_base = float(factor_riesgo_base)
        self.factor_efecto_contacto = float(factor_efecto_contacto)
        super().__init__(*args, **kwargs)

    def _probabilidad_evento(self, row, nivel_riesgo, accion_ejecutada):
        p_base = super()._probabilidad_evento(row, nivel_riesgo, 0)
        p_accion = super()._probabilidad_evento(row, nivel_riesgo, accion_ejecutada)
        reduccion = 0.0 if p_base <= 0 else 1.0 - p_accion / p_base
        reduccion = float(np.clip(reduccion * self.factor_efecto_contacto, 0.0, 0.95))
        return float(np.clip(p_base * self.factor_riesgo_base * (1.0 - reduccion), 0.0, 0.80))


@dataclass(frozen=True)
class Escenario:
    """Configuración común con la que se evalúan todas las políticas."""

    nombre: str
    tipo: str
    capacidad: int = DEFAULT_MONTHLY_CAPACITY
    costos: dict = field(default_factory=lambda: dict(DEFAULT_ACTION_COSTS))
    factor_riesgo_base: float = 1.0
    factor_efecto_contacto: float = 1.0

    def crear_entorno(self, cohorte, horizonte=12):
        return EntornoSensibilidadTransicion(
            cohorte, self.capacidad, self.costos, horizonte,
            factor_riesgo_base=self.factor_riesgo_base,
            factor_efecto_contacto=self.factor_efecto_contacto,
        )


def escenarios_pida(capacidad_base=DEFAULT_MONTHLY_CAPACITY):
    """Escenario base más dos variantes por cada dimensión: capacidad, costos y transición."""
    c = int(capacidad_base)
    return [
        Escenario("base", "base", c),
        Escenario("capacidad_baja", "capacidad", max(1, round(c * 0.5))),
        Escenario("capacidad_alta", "capacidad", max(1, round(c * 1.5))),
        Escenario("costos_bajos", "costos", c, {0: 0, 1: 1, 2: 2, 3: 3}),
        Escenario("costos_altos", "costos", c, {0: 0, 1: 1, 2: 4, 3: 7}),
        Escenario("riesgo_basal_menor", "transicion", c, factor_riesgo_base=0.75),
        Escenario("riesgo_basal_mayor", "transicion", c, factor_riesgo_base=1.25),
        Escenario("efecto_contacto_menor", "transicion", c, factor_efecto_contacto=0.5),
    ]


def grupos_por_perfil(cohorte):
    """Asigna a cada perfil su sexo codificado y su grupo de edad, con los mismos cortes de integral.py."""
    base = cohorte.reset_index(drop=True)
    sexo = base["sexo"].map({1: "sexo_1", 2: "sexo_2", "1": "sexo_1", "2": "sexo_2"})
    sexo = sexo.fillna("sexo_otro_no_especificado").astype(str).to_numpy()
    edad = pd.cut(base["edad"], bins=[-np.inf, 44, 64, np.inf], labels=list(GRUPOS_EDAD)).astype(str).to_numpy()
    riesgo = base["categoria_riesgo"].astype(str).to_numpy()
    return {"grupo_sexo": sexo, "grupo_edad": edad, "categoria_riesgo": riesgo}


def evaluar_episodios(env, politica, nombre, semillas, grupos, gamma=0.95):
    """Evalúa una política episodio por episodio y conserva solo acumulados.

    Devuelve dos tablas: una fila por episodio y una fila por episodio y subgrupo.
    """
    dims = {d: (np.unique(v), v) for d, v in grupos.items()}
    filas, filas_sub = [], []
    for semilla in semillas:
        env.reset(seed=int(semilla))
        acumulados = {d: {g: [0, 0] for g in valores} for d, (valores, _) in dims.items()}
        total = descontado = 0.0
        pasos = contactos = eventos = recursos = ajustes = violaciones = 0
        alto_dec = alto_cont = 0
        while True:
            accion = int(politica(env))
            _, recompensa, terminado, truncado, info = env.step(accion)
            mes = int(info["mes"]) - 1
            total += float(recompensa)
            descontado += (gamma ** mes) * float(recompensa)
            pasos += 1
            contacto = int(info["accion_ejecutada"] > 0)
            contactos += contacto
            eventos += int(info["evento_adverso"])
            recursos += int(info["costo_real"])
            ajustes += int(info["accion_ajustada"])
            violaciones += int(info["recursos_usados_mes"] > info["capacidad_mensual"] or info["recursos_despues"] < 0)
            idx = int(info["indice_perfil"])
            for d, (_, etiquetas) in dims.items():
                celda = acumulados[d][etiquetas[idx]]
                celda[0] += 1
                celda[1] += contacto
            if info["categoria_riesgo"] == "alto":
                alto_dec += 1
                alto_cont += contacto
            if terminado or truncado:
                break
        meses = env.horizonte
        filas.append({
            "algoritmo": nombre, "semilla": int(semilla), "pasos": pasos,
            "recompensa_acumulada": total, "recompensa_descontada": descontado,
            "contactos_ejecutados": contactos, "eventos_adversos": eventos,
            "recursos_usados": recursos, "ajustes_capacidad": ajustes,
            "violaciones_capacidad": violaciones,
            "utilizacion_capacidad": recursos / max(env.capacidad_mensual * meses, 1),
            "cobertura_alto_riesgo": alto_cont / alto_dec if alto_dec else 0.0,
        })
        for d, celdas in acumulados.items():
            for g, (n, c) in celdas.items():
                filas_sub.append({
                    "algoritmo": nombre, "semilla": int(semilla), "dimension": d,
                    "subgrupo": g, "decisiones": n, "contactos": c,
                    "cobertura": c / n if n else 0.0,
                })
    return pd.DataFrame(filas), pd.DataFrame(filas_sub)


def evaluar_escenario(escenario, cohorte, politicas, semillas, horizonte=12, gamma=0.95):
    """Evalúa todas las políticas con las mismas semillas y la misma configuración."""
    grupos = grupos_por_perfil(cohorte)
    episodios, subgrupos = [], []
    for nombre, politica in politicas.items():
        env = escenario.crear_entorno(cohorte, horizonte)
        ep, sub = evaluar_episodios(env, politica, nombre, semillas, grupos, gamma)
        episodios.append(ep.assign(escenario=escenario.nombre, tipo_escenario=escenario.tipo))
        subgrupos.append(sub.assign(escenario=escenario.nombre, tipo_escenario=escenario.tipo))
    return pd.concat(episodios, ignore_index=True), pd.concat(subgrupos, ignore_index=True)


def intervalo_confianza(valores, nivel=0.95, n_bootstrap=5000, semilla=2026):
    """Media, desviación estándar, IC normal e IC bootstrap percentil."""
    x = np.asarray(valores, dtype=float)
    n = len(x)
    media = float(x.mean()) if n else float("nan")
    de = float(x.std(ddof=1)) if n > 1 else 0.0
    z = NormalDist().inv_cdf(0.5 + nivel / 2)
    ee = de / np.sqrt(n) if n > 0 else float("nan")
    rng = np.random.default_rng(semilla)
    medias = rng.choice(x, size=(n_bootstrap, n), replace=True).mean(axis=1) if n > 1 else np.array([media])
    alfa = (1 - nivel) / 2
    return {
        "n_episodios": n, "media": media, "desviacion": de, "error_estandar": ee,
        "ic95_inf": media - z * ee, "ic95_sup": media + z * ee,
        "ic95_boot_inf": float(np.quantile(medias, alfa)), "ic95_boot_sup": float(np.quantile(medias, 1 - alfa)),
    }


def resumen_con_ic(episodios, metricas=("recompensa_acumulada", "cobertura_alto_riesgo", "utilizacion_capacidad", "eventos_adversos")):
    """Resume cada política, escenario y métrica con su intervalo de confianza."""
    filas = []
    claves = [c for c in ("escenario", "tipo_escenario", "algoritmo") if c in episodios.columns]
    for llave, grupo in episodios.groupby(claves, sort=False):
        llave = llave if isinstance(llave, tuple) else (llave,)
        for metrica in metricas:
            fila = dict(zip(claves, llave))
            fila["metrica"] = metrica
            fila.update(intervalo_confianza(grupo[metrica]))
            filas.append(fila)
    return pd.DataFrame(filas)


def brechas_subgrupos(subgrupos):
    """Brecha máxima menos mínima de cobertura, en puntos porcentuales, por política y dimensión."""
    agregados = (
        subgrupos.groupby(["escenario", "algoritmo", "dimension", "subgrupo"], as_index=False)[["decisiones", "contactos"]].sum()
    )
    agregados["cobertura_pct"] = 100 * agregados["contactos"] / agregados["decisiones"].clip(lower=1)
    filas = []
    for (esc, alg, dim), g in agregados.groupby(["escenario", "algoritmo", "dimension"]):
        filas.append({
            "escenario": esc, "algoritmo": alg, "dimension": dim,
            "subgrupo_min": g.loc[g["cobertura_pct"].idxmin(), "subgrupo"],
            "subgrupo_max": g.loc[g["cobertura_pct"].idxmax(), "subgrupo"],
            "cobertura_min_pct": g["cobertura_pct"].min(), "cobertura_max_pct": g["cobertura_pct"].max(),
            "brecha_pp": g["cobertura_pct"].max() - g["cobertura_pct"].min(),
        })
    tabla = pd.DataFrame(filas)
    tabla["cumple_meta_10pp"] = tabla["brecha_pp"] <= UMBRAL_BRECHA_PP
    return tabla


def comparar_robustez(episodios, agentes, referencias):
    """En cada escenario compara el mejor agente RL con la mejor referencia por recompensa media."""
    medias = episodios.groupby(["escenario", "tipo_escenario", "algoritmo"])["recompensa_acumulada"].mean().reset_index()
    filas = []
    for (esc, tipo), g in medias.groupby(["escenario", "tipo_escenario"], sort=False):
        g = g.set_index("algoritmo")["recompensa_acumulada"]
        rl, ref = g.reindex(agentes).dropna(), g.reindex(referencias).dropna()
        if rl.empty or ref.empty:
            continue
        mejor_rl, mejor_ref = rl.idxmax(), ref.idxmax()
        diferencia = rl.max() - ref.max()
        filas.append({
            "escenario": esc, "tipo_escenario": tipo,
            "mejor_agente_rl": mejor_rl, "recompensa_mejor_rl": rl.max(),
            "mejor_referencia": mejor_ref, "recompensa_mejor_referencia": ref.max(),
            "diferencia": diferencia,
            "mejora_relativa": diferencia / abs(ref.max()) if ref.max() != 0 else np.nan,
            "rl_mejora": bool(diferencia > 0),
        })
    return pd.DataFrame(filas)


def tabla_criterios(resumen_base, episodios_base, robustez, brechas_base, pruebas_aprobadas=None,
                    referencias=("Aleatoria", "Reglas simples", "Reglas escalonadas"),
                    agentes=("Q-learning", "DQN", "PPO"), regla_cobertura="Reglas simples"):
    """Construye la tabla de criterios de éxito de la sección 5 de la Definición del PIDA."""
    rec = resumen_base[resumen_base["metrica"] == "recompensa_acumulada"].set_index("algoritmo")
    cob = resumen_base[resumen_base["metrica"] == "cobertura_alto_riesgo"].set_index("algoritmo")
    refs = [r for r in referencias if r in rec.index]
    rls = [a for a in agentes if a in rec.index]
    mejor_ref = rec.loc[refs, "media"].idxmax()
    mejor_rl = rec.loc[rls, "media"].idxmax()
    mejora = (rec.loc[mejor_rl, "media"] - rec.loc[mejor_ref, "media"]) / abs(rec.loc[mejor_ref, "media"])
    ic_rl = (rec.loc[mejor_rl, "ic95_inf"], rec.loc[mejor_rl, "ic95_sup"])
    ic_ref = (rec.loc[mejor_ref, "ic95_inf"], rec.loc[mejor_ref, "ic95_sup"])
    n_min = int(rec["n_episodios"].min())
    violaciones = int(episodios_base["violaciones_capacidad"].sum())
    cob_regla = float(cob.loc[regla_cobertura, "media"]) if regla_cobertura in cob.index else np.nan
    cob_rl = float(cob.loc[mejor_rl, "media"])
    rob = robustez[robustez["escenario"] != "base"]
    frac_rob = float(rob["rl_mejora"].mean()) if len(rob) else np.nan
    tipos = set(rob["tipo_escenario"]) if len(rob) else set()
    b = brechas_base[brechas_base["dimension"].isin(["grupo_sexo", "grupo_edad"])]
    brecha_max = float(b["brecha_pp"].max()) if len(b) else np.nan
    brecha_rl = float(b[b["algoritmo"] == mejor_rl]["brecha_pp"].max()) if len(b) else np.nan

    def fila(dimension, indicador, umbral, valor, cumple, nota=""):
        estado = "Cumple" if cumple is True else ("No cumple" if cumple is False else "Reportado")
        return {"dimension": dimension, "indicador": indicador, "umbral": umbral,
                "resultado": valor, "estado": estado, "nota": nota}

    filas = [
        fila("Validez técnica", "Entorno Gymnasium y pruebas de invariantes", "100 % de pruebas aprobadas",
             "no evaluado aquí" if pruebas_aprobadas is None else pruebas_aprobadas,
             None if pruebas_aprobadas is None else True,
             "Se verifica con pytest en CI (Python 3.10–3.12)."),
        fila("Factibilidad operativa", "Violaciones de capacidad en evaluación", "Cero",
             f"{violaciones} en {len(episodios_base)} episodios", violaciones == 0),
        fila("Comparación", "Políticas evaluadas con semillas y escenarios comunes", "Al menos 3",
             f"{rec.shape[0]} políticas: {', '.join(rec.index)}", rec.shape[0] >= 3),
        fila("Rendimiento", f"Recompensa media con IC95 (n ≥ {EPISODIOS_MINIMOS})",
             "Reportada frente a la mejor referencia",
             f"{mejor_rl}: {rec.loc[mejor_rl, 'media']:.1f} [{ic_rl[0]:.1f}; {ic_rl[1]:.1f}] vs "
             f"{mejor_ref}: {rec.loc[mejor_ref, 'media']:.1f} [{ic_ref[0]:.1f}; {ic_ref[1]:.1f}]; n = {n_min}",
             n_min >= EPISODIOS_MINIMOS,
             "IC disjuntos" if ic_rl[0] > ic_ref[1] or ic_ref[0] > ic_rl[1] else "IC solapados"),
        fila("Rendimiento (aspiracional)", "Mejora del mejor agente frente a la mejor referencia", "≥ 10 %",
             f"{100 * mejora:+.1f} %", bool(mejora >= META_MEJORA_ASPIRACIONAL),
             "Si no se alcanza, se documenta la causa con el análisis de sensibilidad."),
        fila("Prioridad clínica simulada", f"Cobertura de riesgo alto del mejor agente frente a «{regla_cobertura}»",
             "No inferior a la política por reglas",
             f"{100 * cob_rl:.2f} % vs {100 * cob_regla:.2f} %", bool(cob_rl >= cob_regla)),
        fila("Robustez", "Escenarios de capacidad, costos y transición", "Resultados en todos; mejora en ≥ 80 % (meta)",
             f"{len(rob)} escenarios ({', '.join(sorted(tipos))}); el RL mejora en {100 * frac_rob:.0f} %",
             bool(frac_rob >= META_ROBUSTEZ) if len(rob) else None,
             "Reportados en todos los escenarios." if {"capacidad", "costos", "transicion"} <= tipos else "Faltan dimensiones."),
        fila("Equidad operativa", "Diferencia de cobertura entre subgrupos de sexo y edad", "Reportada; meta ≤ 10 pp",
             f"Máxima entre políticas: {brecha_max:.2f} pp; {mejor_rl}: {brecha_rl:.2f} pp",
             bool(brecha_max <= UMBRAL_BRECHA_PP)),
        fila("Reproducibilidad", "Código, semillas, configuración y resultados versionados", "Ejecutable desde cero en Colab",
             "Notebooks corregidos con PROJECT_ROOT; semillas y configuración en el manifiesto", None,
             "Se verifica al ejecutar los notebooks 00–10 en Colab."),
    ]
    return pd.DataFrame(filas), {"mejor_referencia": mejor_ref, "mejor_agente": mejor_rl, "mejora_relativa": float(mejora)}


def huella_configuracion(*partes):
    """Huella corta y reproducible de la configuración (escenario, semillas, cohorte, modelo)."""
    import hashlib
    import json

    digest = hashlib.sha256()
    for parte in partes:
        if isinstance(parte, (bytes, bytearray)):
            digest.update(parte)
        else:
            digest.update(json.dumps(parte, sort_keys=True, default=str).encode("utf-8"))
    return digest.hexdigest()[:12]


def evaluar_con_cache(escenario, cohorte, nombre, politica, semillas, directorio, huella_politica="",
                      horizonte=12, gamma=0.95):
    """Evalúa una política en un escenario y guarda el resultado con la huella de su configuración.

    Si existe un resultado con la misma huella (misma cohorte, escenario, semillas y modelo),
    se reutiliza; cualquier cambio en esos elementos produce una huella distinta.
    """
    from pathlib import Path

    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)
    semillas = [int(s) for s in semillas]
    huella = huella_configuracion(
        pd.util.hash_pandas_object(cohorte.reset_index(drop=True), index=False).to_numpy().tobytes(),
        escenario.__dict__, semillas, nombre, huella_politica, horizonte, gamma,
    )
    slug = "".join(ch if ch.isalnum() else "_" for ch in nombre.lower())
    ruta_ep = directorio / f"{escenario.nombre}__{slug}__{huella}_episodios.csv"
    ruta_sub = directorio / f"{escenario.nombre}__{slug}__{huella}_subgrupos.csv"
    if ruta_ep.is_file() and ruta_sub.is_file():
        return pd.read_csv(ruta_ep), pd.read_csv(ruta_sub), True
    env = escenario.crear_entorno(cohorte, horizonte)
    ep, sub = evaluar_episodios(env, politica, nombre, semillas, grupos_por_perfil(cohorte), gamma)
    ep = ep.assign(escenario=escenario.nombre, tipo_escenario=escenario.tipo, huella=huella)
    sub = sub.assign(escenario=escenario.nombre, tipo_escenario=escenario.tipo, huella=huella)
    ep.to_csv(ruta_ep, index=False)
    sub.to_csv(ruta_sub, index=False)
    return ep, sub, False
