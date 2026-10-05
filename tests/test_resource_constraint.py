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
    env = DiabetesFollowUpEnv(cohorte(), capacidad_mensual=5, horizonte=1, orden_aleatorio=False)
    env.reset(seed=1)
    _, _, _, _, info = env.step(0)
    assert info["perfil_id"] == "P000"


def test_perfil_y_cohorte_sincronizados_con_meses_sin_contacto():
    """El acceso NumPy (perfil) y la vista pandas (cohorte) deben coincidir en todo momento."""
    env = DiabetesFollowUpEnv(cohorte(4), capacidad_mensual=1, horizonte=3)
    env.reset(seed=3)
    for accion in [0, 1, 0, 0, 2, 0, 3, 0]:
        idx = env.idx_actual
        fila = env.cohorte.iloc[idx]
        perfil = env.perfil(idx)
        for columna in env.COLUMNAS_NUMERICAS + ["categoria_riesgo", "meses_sin_contacto"]:
            assert perfil[columna] == fila[columna]
        env.step(accion)
    assert env.cohorte["meses_sin_contacto"].tolist() == [int(v) for v in env._meses_sin_contacto]
    assert env.cohorte["meses_sin_contacto"].max() >= 1
