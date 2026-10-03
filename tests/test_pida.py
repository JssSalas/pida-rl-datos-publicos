"""Pruebas del protocolo de cumplimiento de la Definición del PIDA."""

import numpy as np
import pandas as pd
import pytest
from gymnasium.utils.env_checker import check_env

from src.environment.diabetes_followup_env import DiabetesFollowUpEnv
from src.evaluation.pida import (
    EntornoSensibilidadTransicion, Escenario, brechas_subgrupos, comparar_robustez,
    escenarios_pida, evaluar_escenario, intervalo_confianza, resumen_con_ic, tabla_criterios,
)
from src.policies.baselines import POLITICAS_BASE


def cohorte():
    return pd.DataFrame({
        "FOLIO_INT": ["100", "101", "102", "103", "104", "105"],
        "edad": [35, 55, 68, 72, 41, 59], "sexo": [1, 2, 1, 2, 2, 1],
        "anios_con_diabetes": [2, 8, 15, 20, 4, 9], "insulina_diaria": [0, 0, 1, 1, 0, 1],
        "depresion": [0, 1, 0, 1, 0, 0], "consultas_control_12m": [1, 3, 5, 6, 2, 4],
        "num_hospitalizaciones": [0, 0, 1, 2, 0, 1], "num_complicaciones": [0, 1, 2, 3, 0, 2],
        "score_riesgo": [1, 4, 8, 12, 2, 7],
        "categoria_riesgo": ["bajo", "medio", "alto", "alto", "bajo", "medio"],
    })


def test_entorno_sensibilidad_es_gymnasium_y_neutro_con_factores_unitarios():
    env = EntornoSensibilidadTransicion(cohorte(), 5, horizonte=2)
    check_env(env, skip_render_check=True)
    base = DiabetesFollowUpEnv(cohorte(), 5, horizonte=2)
    variante = EntornoSensibilidadTransicion(cohorte(), 5, horizonte=2)
    base.reset(seed=7)
    variante.reset(seed=7)
    for _ in range(12):
        _, r1, *_ , i1 = base.step(2)
        _, r2, *_ , i2 = variante.step(2)
        assert r1 == r2
        assert i1["prob_evento"] == pytest.approx(i2["prob_evento"])


def test_factores_modifican_probabilidad_en_la_direccion_esperada():
    row = cohorte().assign(meses_sin_contacto=0).iloc[2]
    base = EntornoSensibilidadTransicion(cohorte(), 5)
    mayor = EntornoSensibilidadTransicion(cohorte(), 5, factor_riesgo_base=1.25)
    menor_efecto = EntornoSensibilidadTransicion(cohorte(), 5, factor_efecto_contacto=0.5)
    assert mayor._probabilidad_evento(row, 2, 0) > base._probabilidad_evento(row, 2, 0)
    assert menor_efecto._probabilidad_evento(row, 2, 3) > base._probabilidad_evento(row, 2, 3)
    assert menor_efecto._probabilidad_evento(row, 2, 0) == pytest.approx(base._probabilidad_evento(row, 2, 0))


def test_intervalo_confianza_contiene_la_media():
    x = np.random.default_rng(1).normal(10, 2, 200)
    ic = intervalo_confianza(x)
    assert ic["n_episodios"] == 200
    assert ic["ic95_inf"] < ic["media"] < ic["ic95_sup"]
    assert ic["ic95_boot_inf"] < ic["media"] < ic["ic95_boot_sup"]


def test_escenarios_cubren_capacidad_costos_y_transicion():
    tipos = {e.tipo for e in escenarios_pida()}
    assert tipos == {"base", "capacidad", "costos", "transicion"}


def test_protocolo_completo_sin_violaciones_y_con_tabla_de_criterios():
    politicas = dict(POLITICAS_BASE)
    politicas["Agente prueba"] = lambda env: 3
    semillas = range(5)
    escenarios = [Escenario("base", "base", 6), Escenario("capacidad_baja", "capacidad", 3)]
    eps, subs = [], []
    for esc in escenarios:
        e, s = evaluar_escenario(esc, cohorte(), politicas, semillas, horizonte=2)
        eps.append(e)
        subs.append(s)
    episodios, subgrupos = pd.concat(eps), pd.concat(subs)
    assert episodios["violaciones_capacidad"].sum() == 0
    assert set(subgrupos.loc[subgrupos["dimension"] == "categoria_riesgo", "subgrupo"]) == {"bajo", "medio", "alto"}
    resumen = resumen_con_ic(episodios)
    robustez = comparar_robustez(episodios, ["Agente prueba"], list(POLITICAS_BASE))
    brechas = brechas_subgrupos(subgrupos)
    criterios, clave = tabla_criterios(
        resumen[resumen["escenario"] == "base"], episodios[episodios["escenario"] == "base"],
        robustez, brechas[brechas["escenario"] == "base"], agentes=("Agente prueba",),
    )
    assert len(criterios) == 9
    assert criterios.loc[criterios["dimension"] == "Factibilidad operativa", "estado"].item() == "Cumple"
    assert clave["mejor_agente"] == "Agente prueba"
    assert (brechas["brecha_pp"] >= 0).all()
