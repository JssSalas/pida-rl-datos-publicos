# Notebooks corregidos y ejecución de prueba (V2.12.0 – V2.13.0)

## Alcance

Se ejecutaron de principio a fin, en sesiones de kernel independientes, los notebooks históricos **00–04** (Colab/Drive) y los notebooks V2 **05–09** de la rama `feature/entorno-capacidad-v2`, usando una cohorte pequeña y pocos episodios.

- Los originales **no se modificaron**. Las versiones corregidas están en `notebooks/corregidos/`.
- Los originales 00–04, que solo existían en Google Drive (`Colab Notebooks/`), se resguardan sin cambios en `notebooks/historicos_colab/`.
- Las acciones son `0 = sin contacto`, `1 = mensaje`, `2 = llamada` y `3 = teleorientación`. La acción 3 es una intensidad de seguimiento, no una categoría de riesgo.
- Solo existen tres categorías de riesgo: `bajo`, `medio` y `alto`.

| Original | Corregido |
|---|---|
| Drive `00_setup_colab_reinicio.ipynb` | `00_setup_colab_corregido.ipynb` |
| Drive `01_fuentes_y_carga_reinicio.ipynb` | `01_fuentes_y_carga_corregido.ipynb` |
| Drive `02_entendimiento_datos_reinicio.ipynb` | `02_entendimiento_datos_corregido.ipynb` |
| Drive `03_preparacion_cohorte_reinicio_v2.ipynb` | `03_preparacion_cohorte_corregido.ipynb` |
| Drive `04_definicion_mdp_limpio.ipynb` | `04_definicion_mdp_corregido.ipynb` |
| `notebooks/05_politicas_base_capacidad_v2.ipynb` | `05_politicas_base_capacidad_v2_corregido.ipynb` |
| `notebooks/06_q_learning_capacidad_v2.ipynb` | `06_q_learning_capacidad_v2_corregido.ipynb` |
| `notebooks/07_dqn_capacidad_v2.ipynb` | `07_dqn_capacidad_v2_corregido.ipynb` |
| `notebooks/08_ppo_capacidad_v2.ipynb` | `08_ppo_capacidad_v2_corregido.ipynb` |
| `notebooks/09_evaluacion_integral_equidad_v2.ipynb` | `09_evaluacion_integral_equidad_v2_corregido.ipynb` |

Cada notebook corregido empieza con una celda que enumera sus cambios.

## Rutas: `PROJECT_ROOT`

Todas las rutas fijas `/content/drive/MyDrive/PIDA-RL-Diabetes` se sustituyeron por un bootstrap común:

| Variable | Significado | Resolución |
|---|---|---|
| `PROJECT_ROOT` | Datos, modelos y resultados | `PIDA_PROJECT_ROOT`, o `MyDrive/PIDA-RL-Diabetes` en Colab, o `./PIDA-RL-Diabetes` en local |
| `REPO_ROOT` | Código del repositorio | `PIDA_REPO_ROOT`, o búsqueda ascendente de `src/`, o `/content/pida-rl-datos-publicos` en Colab |
| `PERSISTENT_ROOT` | Alias de `PROJECT_ROOT` | Compatibilidad con el código original |
| `RESULTS_V2_DIR` | Resultados V2 | `results/capacidad_v2`, o `results/capacidad_v2_prueba` en modo prueba |

En los notebooks históricos, `PROJECT_ROOT` antes designaba el repositorio; ahora ese papel corresponde a `REPO_ROOT`.

## Modo prueba

Se activa con `PIDA_MODO_PRUEBA=1`. Sin esa variable, el comportamiento y los hiperparámetros son los originales.

| Parámetro | Completo | Prueba |
|---|---|---|
| Cohorte | 1 542 perfiles | 120 perfiles, muestra estratificada por `categoria_riesgo` (semilla 2026) |
| Capacidad mensual | 100 | 8, escalada para conservar recursos por persona |
| Sensibilidad de capacidad | 50 / 100 / 150 | 4 / 8 / 12 |
| Q-learning | 1 500 episodios | 5 episodios |
| DQN | 100 000 pasos | 3 000 pasos |
| PPO | 100 000 pasos, rollout 2 048 | 4 096 pasos, rollout 1 024 |
| Semillas de evaluación | 42, 123, 2026 | 42, 123, 2026 |

La submuestra no crea columnas: solo selecciona filas de `cohorte_diabetes.csv`.

## Lista de cambios

### Comunes a 00–04
1. La celda de inicialización se sustituyó por el bootstrap `PROJECT_ROOT`/`REPO_ROOT`.
2. Se aplicó el renombrado `PROJECT_ROOT` → `REPO_ROOT` y `PERSISTENT_ROOT` → `PROJECT_ROOT`.
3. El clonado ahora usa `--branch feature/entorno-capacidad-v2`. Antes clonaba `main`, que no contiene `src/` V2.

### Específicos
- **00:** Drive se monta únicamente en Colab. El notebook instala solo dependencias faltantes. El checklist exige Drive únicamente en Colab y añade `PROJECT_ROOT disponible`.
- **03:** Se verifica el contrato de esquema contra `DiabetesFollowUpEnv.COLUMNAS_REQUERIDAS`, sin crear columnas.
- **04:** Se documenta, en una tabla y en el JSON de especificación, la discrepancia entre el entorno histórico y el entorno V2.

### Comunes a 05–09
1. Se eliminaron `from google.colab import drive`, `drive.mount(...)` y las rutas fijas de Drive.
2. Las rutas de modelos y resultados usan `RESULTS_V2_DIR`.
3. Se añadió el modo prueba, con submuestra estratificada y capacidad proporcional.
4. Se añadieron hiperparámetros reducidos para 06, 07 y 08 únicamente en modo prueba.

## Auditoría de columnas

| Etapa | Columnas requeridas | Origen | Estado |
|---|---|---|---|
| 03 → cohorte | 16 columnas (`FOLIO_INT`, `edad`, `sexo`, `anios_con_diabetes`, `insulina_diaria`, `depresion`, `consultas_control_12m`, `num_hospitalizaciones`, cinco `complicacion_*`/`evento_agudo_diabetes`, `num_complicaciones`, `score_riesgo`, `categoria_riesgo`) | Creadas explícitamente en 03 a partir de ENSANUT Adultos | OK |
| 04 entorno histórico | 10 columnas de estado | Cohorte 03 | OK |
| 05–09 entorno V2 | `COLUMNAS_REQUERIDAS` (10) | Cohorte 03 | OK |
| 09 equidad | `FOLIO_INT`, `sexo`, `edad`, `categoria_riesgo` | Cohorte 03; `grupo_sexo` y `grupo_edad` se derivan en `src/evaluation/integral.py` | OK |
| Estado del simulador | `meses_sin_contacto`, mes y recursos restantes | Creados por el entorno en `reset()`, no por la cohorte | OK |

No se encontró ninguna variable usada que no exista o que no se cree explícitamente. Ninguna variable fue inventada.

## Discrepancias documentadas (no corregidas)

1. **Entorno 04 frente a V2.** El entorno 04 usa costos 0/1/2/3, capacidad como fracción de 0.20 y rechazo con penalización −3. El entorno V2 usa costos 0/1/3/5, capacidad absoluta de 100 y degradación a la acción viable. Las conclusiones comparativas deben provenir del V2.
2. **Presión de capacidad.** Con capacidad 100 y 1 542 perfiles hay 0.065 unidades por persona al mes. La utilización es del 100 % y la cobertura de alto riesgo es muy baja en todas las políticas. Debe revisarse como supuesto del escenario.
3. **Semillas de carga.** Los notebooks 08 y 09 cargan Q-learning, DQN y PPO con `seed=20_000`. Esto no afecta la evaluación, porque es determinista y sin exploración.
4. **Archivo generado.** El notebook 04 escribe `src/environment/diabetes_followup_env_clean.py` en la copia local. Es un artefacto generado y se ignora en Git.
5. **Línea paralela.** Los notebooks `06–14 *_autocontenido/_corregido` subidos manualmente forman la línea v1 de despliegue. Se corrigieron y ejecutaron en V2.13.0 (ver la sección siguiente).

## Salida de la ejecución de prueba

- Entorno: Python 3.12.13, numpy 2.5.3, pandas 2.3.3, gymnasium 1.3.0, stable-baselines3 2.9.0 y pyreadstat 1.3.6.
- Commit evaluado: `02ab45d`.
- Pruebas: `pytest` reporta 39 aprobadas.

| Notebook | Estado | Segundos |
|---|---|---|
| 00 setup | OK | 5.3 |
| 01 fuentes y carga | OK | 2.4 |
| 02 entendimiento | OK | 2.9 |
| 03 cohorte | OK | 2.2 |
| 04 MDP | OK | 3.2 |
| 05 políticas base | OK | 5.4 |
| 06 Q-learning | OK | 10.2 |
| 07 DQN | OK | 11.1 |
| 08 PPO | OK | 13.3 |
| 09 evaluación integral | OK | 42.1 |

### Cohorte (03)

| Paso | Registros |
|---|---|
| Registros en Adultos ENSANUT 2022 | 11 913 |
| Diabetes gestacional excluida (a0301 = 2) | 18 |
| Sin diagnóstico (a0301 = 3) | 10 351 |
| Con diabetes diagnosticada (a0301 = 1) | 1 544 |
| Cohorte final, tras validar clave, edad y sexo | **1 542** (alto 612, medio 544, bajo 386) |

La cohorte regenerada es idéntica, celda por celda, al `cohorte_diabetes.csv` guardado en Drive.

### Invariantes verificados

| Invariante | Resultado |
|---|---|
| Recursos usados ≤ capacidad | 0 violaciones en 05, 06, 07, 08 y 09 |
| Recursos negativos | 0 |
| Categorías presentes | únicamente `alto`, `bajo`, `medio` |
| Acciones ejecutadas | únicamente 0–3 |
| Decisiones registradas en 05 | 12 960 = 120 × 12 × 3 semillas × 3 políticas |
| Políticas comparadas en 09 | 6 |

### Resumen 09 (prueba, capacidad 8, 3 semillas)

| Algoritmo | Recompensa media | DE | Contactos ejecutados | Eventos adversos | Ajustes por capacidad | Utilización | Cobertura alto riesgo |
|---|---|---|---|---|---|---|---|
| Aleatoria | −1469.0 | 37.3 | 38.7 | 87.3 | 1059.7 | 1.00 | 0.029 |
| DQN | −1458.3 | 30.6 | 48.0 | 87.7 | 1164.0 | 1.00 | 0.042 |
| PPO | −1427.7 | 28.4 | 48.0 | 86.3 | 1404.0 | 1.00 | 0.042 |
| Q-learning | −1482.0 | 27.8 | 40.0 | 88.0 | 1153.0 | 1.00 | 0.028 |
| Reglas escalonadas | −1428.3 | 20.2 | 24.0 | 87.7 | 1056.0 | 1.00 | 0.042 |
| Reglas simples | −1371.0 | 17.3 | 48.0 | 87.0 | 1056.0 | 1.00 | 0.083 |

Estos valores son una **prueba de humo**: comprueban que el flujo funciona y no deben interpretarse. Los agentes se entrenaron con muy pocos episodios, por lo que no es esperable que superen a las reglas. Los resultados metodológicos requieren el modo completo.

## Cómo ejecutar

**Colab, modo completo:** abre cada notebook de `notebooks/corregidos/` en orden 00 → 09. Drive se monta automáticamente y `PROJECT_ROOT` será `MyDrive/PIDA-RL-Diabetes`.

**Colab, modo prueba:** antes de la primera celda ejecuta:

```python
import os
os.environ['PIDA_MODO_PRUEBA'] = '1'
```

**Local:**

```bash
export PIDA_PROJECT_ROOT=/ruta/PIDA-RL-Diabetes   # con data/raw/*.sav
export PIDA_REPO_ROOT=/ruta/pida-rl-datos-publicos
export PIDA_MODO_PRUEBA=1
```

## Línea v1 de despliegue (notebooks 05–14 autocontenidos, V2.13.0)

Los notebooks `06–14` subidos al repositorio forman una línea de trabajo propia. Sus entornos se definen dentro de cada notebook, usan Stable-Baselines3 y terminan en el dashboard y su despliegue.

Su insumo inicial, `05_politicas_base_autocontenido.ipynb`, solo existía en Google Drive. Se resguardó sin cambios en `notebooks/historicos_colab/`. Las versiones corregidas están en `notebooks/corregidos/linea_v1_despliegue/`, y los originales no se modificaron.

| Notebook corregido | Origen |
|---|---|
| `05_politicas_base_autocontenido_corregido` | Drive `05_politicas_base_autocontenido.ipynb` |
| `06_entrenamiento_dqn_autocontenido_corregido` | `notebooks/06_entrenamiento_dqn_autocontenido.ipynb` |
| `07_entrenamiento_q_learning_autocontenido_corregido` | `notebooks/07_entrenamiento_q_learning_autocontenido.ipynb` |
| `08_entrenamiento_ppo_autocontenido_corregido` | `notebooks/08_entrenamiento_ppo_autocontenido.ipynb` |
| `09_evaluacion_conjunta_modelos_corregido` | `notebooks/09_evaluacion_conjunta_modelos_corregido.ipynb` |
| `10_equidad_y_subgrupos_v3_corregido` | `notebooks/10_equidad_y_subgrupos_v3_corregido.ipynb` |
| `11_visualizaciones_conclusiones_finales_corregido` | `notebooks/11_visualizaciones_conclusiones_finales.ipynb` |
| `12_generar_dashboard_streamlit_corregido` | `notebooks/12_generar_dashboard_streamlit.ipynb` |
| `13_despliegue_streamlit_ngrok_y_github_corregido` | `notebooks/13_despliegue_streamlit_ngrok_y_github_corregido.ipynb` |
| `14_documentacion_crisp_dm_y_reproducibilidad_corregido` | `notebooks/14_documentacion_crisp_dm_y_reproducibilidad.ipynb` |

**Orden de ejecución:**

1. 00–04 (comunes).
2. V2 05–09, que genera los datos del dashboard principal.
3. Línea v1: 05 → 14.

### Cambios comunes

- Se eliminaron la detección y el montaje de Drive y el clonado de `main`. Se usa el bootstrap `PROJECT_ROOT`/`REPO_ROOT` con la rama `feature/entorno-capacidad-v2`.
- `PERSISTENT_ROOT` es la raíz de la línea v1. Coincide con `PROJECT_ROOT`; en modo prueba es `PROJECT_ROOT/prueba_linea_v1`, para no sobrescribir los resultados completos.
- La cohorte se lee siempre de `PROJECT_ROOT/data/processed/cohorte_diabetes.csv`.
- En modo prueba se usa la misma muestra estratificada de 120 perfiles. La capacidad de la línea v1 es relativa (0.20), por lo que no se escala.
- Presupuestos del modo prueba:

| Algoritmo | Prueba | Completo |
|---|---|---|
| DQN | 3 000 pasos | 100 000 pasos |
| Q-learning | 5 episodios | 250 episodios |
| PPO | 4 096 pasos | 100 000 pasos |

### Errores corregidos en los originales

| Notebook | Problema | Corrección |
|---|---|---|
| 13 | B1 copiaba el dashboard v1 sobre `dashboard_streamlit/`. En la rama de trabajo esa carpeta contiene el dashboard V2 (`data_loader.py`, manifiesto y equidad), así que publicar habría revertido V2. | El v1 se publica en `dashboard_streamlit_v1/`. El V2 no se toca y sus datos se publican en `dashboard_data/v2/`. |
| 13 | Exigía los cuatro secretos de Colab incluso para la vista temporal y no podía ejecutarse fuera de Colab. | Los secretos se leen de Colab o de variables de entorno y solo se exigen cuando se usan. |
| 13 | B4 podía publicar en cualquier rama, incluida `main`, y B3 comparaba contra `origin/main`. | Se rechaza `main` y se compara contra la rama de trabajo. |
| 14 | `policy_table.rename(columns={...)` no cerraba la llave, lo que producía un `SyntaxError`. | Se cierra el diccionario. |
| 14 | `{selected_metrics := ...:.3f}` dentro del f-string se interpretaba como especificador de formato, lo que producía un `NameError`. | Se usa directamente `selected_row.get(...)`. |
| 12 | El dashboard principal V2 no tenía datos versionados, por lo que la app de Streamlit Cloud fallaría al integrarse el PR. | Nueva sección 9: exporta el reporte integral V2 a `dashboard_data/v2/` y lo valida con el cargador de la app. |

### Nuevas verificaciones

- La celda A0 del notebook 13 renderiza ambas aplicaciones con `streamlit.testing`.
- La celda A2 comprueba `/_stcore/health`.
- `tests/test_dashboard_despliegue.py` repite estas comprobaciones en CI.

### Ejecución de prueba de la línea v1

| Notebook | Estado | Segundos |
|---|---|---|
| 05_politicas_base_autocontenido | OK | 7.5 |
| 06_entrenamiento_dqn_autocontenido | OK | 117.5 |
| 07_entrenamiento_q_learning_autocontenido | OK | 5.8 |
| 08_entrenamiento_ppo_autocontenido | OK | 112.3 |
| 09_evaluacion_conjunta_modelos | OK | 1.4 |
| 10_equidad_y_subgrupos_v3 | OK | 11.5 |
| 11_visualizaciones_conclusiones_finales | OK | 2.4 |
| 12_generar_dashboard_streamlit | OK | 1.3 |
| 13_despliegue_streamlit_ngrok_y_github | OK | 4.8 |
| 14_documentacion_crisp_dm_y_reproducibilidad | OK | 1.5 |

En las trazas de evaluación (25 920 decisiones de 6 políticas) solo aparecen las categorías bajo, medio y alto y las acciones 0–3.

En el entorno v1, los excesos de capacidad son rechazos con penalización y forman parte de su diseño. Se presentan con las políticas aleatoria, reglas de riesgo y Q-learning.

En el entorno V2 los excesos son imposibles. Ese es el motivo metodológico de V2.

Despliegue: ver `docs/DESPLIEGUE_STREAMLIT.md`.

## Ejecución completa V2 05–10 (V2.14.0)

Configuración: `PIDA_MODO_PRUEBA=0`, cohorte completa de 1 542 perfiles, capacidad mensual 100, costos 0/1/3/5, horizonte de 12 meses.

| Notebook | Estado | Segundos |
|---|---|---|
| 05_politicas_base_capacidad_v2_corregido | ok | 5.6 |
| 06_q_learning_capacidad_v2_corregido (1 500 episodios) | ok | 1 213.6 |
| 07_dqn_capacidad_v2_corregido (100 000 pasos) | ok | 27.0 |
| 08_ppo_capacidad_v2_corregido (100 000 pasos) | ok | 24.7 |
| 09_evaluacion_integral_equidad_v2_corregido | ok | 52.4 |
| 10_cumplimiento_pida_v2 (nuevo) | ok | 1 343.4 (reutilizó la caché de evaluaciones; incluye unos 15 min de entrenamiento de la sección 12) |

Resumen del notebook 09 (3 semillas):

| Política | Recompensa media | Cobertura de riesgo alto |
|---|---|---|
| Reglas simples | −18 542.0 | 4.9 % |
| Reglas escalonadas | −18 781.7 | 3.9 % |
| Q-learning | −18 918.8 | 3.5 % |
| DQN | −19 039.0 | 2.8 % |
| Aleatoria | −19 144.8 | 2.9 % |
| PPO | −19 314.0 | 2.1 % |

El notebook 10 evalúa los criterios de la sección 5 del PIDA con 100 episodios por política. Resultados y discusión en `docs/CUMPLIMIENTO_PIDA.md`.

El notebook 10 guarda cada evaluación en `cumplimiento_pida/cache/` con una huella SHA-256 de la configuración: cohorte, escenario, semillas y archivo del modelo. Una nueva ejecución con la misma configuración reutiliza esos resultados.
