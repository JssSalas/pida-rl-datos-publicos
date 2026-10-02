# Notebooks corregidos y ejecución de prueba (V2.12.0)

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
5. **Línea paralela.** Los notebooks `06–14 *_autocontenido/_corregido` subidos manualmente pertenecen a otra línea de trabajo. No forman parte de esta ejecución.

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
