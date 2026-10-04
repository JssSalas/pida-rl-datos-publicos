# Matriz CRISP-DM del PIDA

Este documento vincula las seis fases de CRISP-DM con evidencia verificable del repositorio. El proyecto es un prototipo metodológico basado en simulación y datos públicos; no constituye una herramienta clínica.

## 1. Entendimiento del negocio

**Pregunta:** ¿cómo asignar de forma adaptativa una capacidad mensual limitada de mensajes, llamadas y teleorientación a perfiles de personas con diabetes?

**Criterios de éxito:** comparar políticas con un protocolo común; respetar la capacidad; aumentar la cobertura de riesgo alto; cuantificar recompensa, eventos simulados, estabilidad y brechas operativas.

**Evidencia:**

- `README.md`: problema, objetivos, alcance y exclusiones.
- `docs/modelo_mdp.md`: formulación del proceso de decisión.
- `docs/CONTROL_CAMBIOS.md`: línea base, evolución y recuperación.

## 2. Entendimiento de datos

Se utilizan fuentes públicas para construir una cohorte analítica no identificable. Las variables, procedencia, fecha de consulta y restricciones de uso deben quedar asentadas antes de modelar.

**Evidencia:**

- `docs/data_sources.md`: bitácora de fuentes.
- `notebooks/01_descarga_datos.ipynb` y `02_eda.ipynb`: adquisición y exploración.
- `notebooks/03_preparacion_datos.ipynb`: cohorte procesada y diccionario operativo.

**Control:** `FOLIO_INT` funciona como identificador técnico para enlazar resultados; no debe interpretarse como identidad clínica.

## 3. Preparación de datos

La cohorte debe incluir las columnas requeridas por `DiabetesFollowUpEnv`, valores numéricos finitos y únicamente las categorías `bajo`, `medio` y `alto`.

**Evidencia:**

- `src/data/`: utilidades de preparación y validación.
- `src/environment/diabetes_followup_env.py`: contrato de columnas y validaciones.
- Pruebas de entorno y evaluación en `tests/`.

## 4. Modelación

El entorno representa decisiones mensuales con cuatro acciones: 0 sin contacto, 1 mensaje, 2 llamada y 3 teleorientación. La acción 3 es una intensidad de seguimiento, no una cuarta categoría de riesgo.

| Modelo | Implementación | Notebook |
|---|---|---|
| Aleatoria y reglas | `src/policies/baselines.py` | `05_politicas_base_capacidad_v2.ipynb` |
| Q-learning | `src/policies/q_learning.py` | `06_q_learning_capacidad_v2.ipynb` |
| DQN | `src/policies/dqn.py` | `07_dqn_capacidad_v2.ipynb` |
| PPO | `src/policies/ppo.py` | `08_ppo_capacidad_v2.ipynb` |

Los modelos entrenados se guardan en NPZ. Cada ejecución debe registrar semilla, hiperparámetros, costos, capacidad, horizonte y versión del código.

## 5. Evaluación

La comparación usa la misma cohorte, dinámica, costos, horizonte y semillas. Se reportan acciones propuestas y ejecutadas para distinguir la política aprendida de la restricción operativa.

**Métricas:** recompensa, eventos adversos simulados, cobertura de riesgo alto, consumo y utilización de recursos, ajustes por capacidad, estabilidad entre semillas y brechas descriptivas por subgrupo.

**Evidencia:**

- `src/evaluation/reporting.py` y `src/evaluation/integral.py`.
- `notebooks/09_evaluacion_integral_equidad_v2.ipynb`.
- Manifiesto y CSV generados por la evaluación integral.

Las brechas por sexo codificado, edad y riesgo son diagnósticos descriptivos; no demuestran causalidad, discriminación ni equidad clínica.

## 6. Despliegue

El dashboard Streamlit consume exclusivamente los reportes integrales V2 validados. Permite revisar políticas, clasificaciones 0–3, sensibilidad a capacidad, estabilidad, cobertura y brechas operativas.

**Evidencia:**

- `dashboard_streamlit/app.py` y `data_loader.py`.
- `dashboard_streamlit/README.md`.
- `.github/workflows/ci.yml`: sintaxis, importaciones y pruebas en Python 3.10–3.12.
- `docs/VALIDACION_REPRODUCIBILIDAD.md`: protocolo de ejecución y aceptación.

## Puertas de aceptación

Antes de fusionar a `main` deben cumplirse todas:

- Las pruebas automatizadas pasan en las versiones de Python soportadas.
- Ningún episodio excede la capacidad ni produce recursos negativos.
- Solo existen las categorías de riesgo bajo, medio y alto.
- La comparación conserva semillas y configuración comunes.
- Los reportes incluyen acción propuesta y ejecutada.
- No hay secretos, credenciales ni datos personales en el repositorio.
- El dashboard carga el manifiesto y valida el esquema de los CSV.
- Las limitaciones de simulación aparecen en README, notebooks y dashboard.

## Riesgos residuales

- Las transiciones y recompensas contienen supuestos del simulador.
- El umbral de teleorientación y los costos son parámetros operativos, no puntos de corte clínicos validados.
- Los resultados no se generalizan a una institución sin calibración, validación externa y autorización ética.
- El despliegue actual es demostrativo; no incluye autenticación, expediente clínico ni integración hospitalaria.
