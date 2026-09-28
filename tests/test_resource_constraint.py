import pandas as pd
import pytest

from src.environment.diabetes_followup_env import DiabetesFollowUpEnv


def cohorte(n=4):
    base = pd.DataFrame(
        {
            "FOLIO_INT": [f"P{i:03d}" for i in range(4)],
            "edad": [55] * 4,
            "sexo": [1, 2, 1, 2],
            "anios_con_diabetes": [10] * 4,
            "insulina_diaria": [0, 1, 0, 1],
            "depresion": [0, 0, 1, 0],
            "consultas_control_12m": [2, 4, 1, 6],
            "num_hospitalizaciones": [0, 1, 0, 2],
            "num_complicaciones": [1] * 4,
            "score_riesgo": [12, 8, 3, 14],
            "categoria_riesgo": ["alto", "medio", "bajo", "alto"],
        }
    )
    return base.iloc[:n].copy()


def test_recursos_nunca_son_negativos_y_accion_se_ajusta():
    env = DiabetesFollowUpEnv(cohorte(), capacidad_mensual=5, horizonte=1)
    env.reset(seed=42)
    infos = []
    for _ in range(4):
        _, _, terminado, _, info = env.step(3)
        infos.append(info)
        assert info["recursos_despues"] >= 0
        assert info["recursos_usados_mes"] <= info["capacidad_mensual"]
    assert infos[0]["accion_ejecutada"] == 3
    assert infos[1]["accion_ejecutada"] == 0
    assert infos[1]["accion_ajustada"] is True
    assert terminado is True


def test_degrada_a_mayor_accion_viable():
    env = DiabetesFollowUpEnv(cohorte(), capacidad_mensual=4, horizonte=1)
    env.reset(seed=1)
    _, _, _, _, info = env.step(3)
    assert info["accion_propuesta"] == 3
    assert info["accion_ejecutada"] == 2
    assert info["costo_real"] == 3
    assert info["recursos_despues"] == 1


def test_capacidad_cero_solo_permite_sin_contacto():
    env = DiabetesFollowUpEnv(cohorte(), capacidad_mensual=0, horizonte=1)
    env.reset(seed=1)
    _, _, _, _, info = env.step(3)
    assert info["accion_ejecutada"] == 0
    assert info["recursos_despues"] == 0


def test_observacion_incluye_recursos_restantes():
    env = DiabetesFollowUpEnv(cohorte(), capacidad_mensual=5, horizonte=1)
    obs, _ = env.reset(seed=1)
    assert obs.shape == (13,)
    assert obs[-1] == pytest.approx(1.0)
    obs, _, _, _, _ = env.step(1)
    assert obs[-1] == pytest.approx(0.8)


def test_accion_fuera_de_rango_falla():
    env = DiabetesFollowUpEnv(cohorte(), capacidad_mensual=5, horizonte=1)
    env.reset(seed=1)
    with pytest.raises(ValueError):
        env.step(4)


def test_identificador_original_se_conserva():
    env = DiabetesFollowUpEnv(cohorte(), capacidad_mensual=5, horizonte=1)
    env.reset(seed=1)
    _, _, _, _, info = env.step(0)
    assert info["perfil_id"] == "P000"
