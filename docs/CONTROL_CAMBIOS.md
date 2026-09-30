# Control de cambios

Este documento registra cambios funcionales, evidencia de validación y procedimientos de recuperación. La rama `main` no se modifica directamente; el desarrollo se realiza en ramas `feature/*` y se integra mediante pull request.

## Línea base

| Elemento | Valor |
|---|---|
| Repositorio | `JssSalas/pida-rl-datos-publicos` |
| Rama estable | `main` |
| Commit base | `542d2cd5765b9f82e8a2f93f01240eb604eba52a` |
| Rama de trabajo | `feature/entorno-capacidad-v2` |
| Fecha de inicio | 2026-09-28 |

## Registro

### V2.0.0 — Capacidad estricta

**Commit:** `a3f4a4b45a6ddbba81c51d1fe582ecbc256dfcf4`.

- Se centralizan nombres, costos y capacidad.
- Se separan acciones propuestas y ejecutadas.
- Los recursos se descuentan y nunca quedan negativos.
- Se registra información suficiente para auditar cada decisión.
- Validación: cinco pruebas aprobadas.

### V2.1.0 — Evaluación trazable

**Commit:** `d402995f9b1b5cee6cab3e2ecc01c2d71ffad195`.

- Registro por algoritmo, semilla, paciente, mes y paso.
- Resumen por episodio de recompensa, contactos, eventos, recursos, utilización y cobertura.
- Clasificaciones propuestas y ejecutadas con las cuatro acciones.
- Exportación de cinco tablas CSV.

### V2.2.0 — Cohorte y políticas base

**Commit:** `9d242aadcd05978a6c331c672ab0e8e99dedd20f`.

- El estado se alinea con las 13 variables usadas por la cohorte existente.
- Se validan columnas, valores finitos y categorías de riesgo.
- Se conserva `FOLIO_INT` como identificador del perfil en los reportes.
- La política aleatoria usa un generador reproducible por semilla.
- La política por reglas asigna 0 a riesgo bajo, 1 a medio y 2 a alto.
- Validación acumulada: once pruebas aprobadas.

### V2.3.0 — Notebook de comparación base

**Commit:** `d47872beb09775ea8b05c5f9f63e7a9ed3f2528e`.

- Se añade `notebooks/05_politicas_base_capacidad_v2.ipynb`.
- La capacidad, los costos, el horizonte y las semillas se ajustan desde una sola sección.
- Se reutiliza `cohorte_diabetes.csv` generada por el notebook 03.
- Se comprueban recursos negativos y excesos de capacidad.
- Se exportan detalle, episodios, resumen y distribuciones de acciones a Google Drive.

### V2.4.0 — Reglas escalonadas

- Se mantiene exactamente la estratificación `bajo`, `medio` y `alto`; no se crea una cuarta categoría.
- Se añade una tercera referencia: bajo propone 0; medio propone 1 o 2; alto propone 2 o 3.
- El umbral predeterminado de teleorientación es `score_riesgo >= 6` y se documenta como supuesto operativo configurable.
- Se añade una fábrica de políticas para evaluar sensibilidad con otros umbrales, por ejemplo 5, 6 y 7.
- Se incorporan pruebas para la asignación escalonada, la configuración del umbral y el rechazo de umbrales inválidos.

### V2.5.0 — Q-learning tabular

- Se añade Q-learning epsilon-greedy con actualización de Bellman y cuatro acciones.
- El estado discreto conserva tres niveles de riesgo e incorpora score, tiempo sin contacto, mes y recursos restantes.
- Se separan semillas de entrenamiento y evaluación.
- Se registran recompensa, eventos adversos, ajustes, recursos, epsilon y estados visitados por episodio.
- La tabla Q se exporta a CSV y el modelo a NPZ sin serialización ejecutable.
- El notebook 06 compara Aleatoria, Reglas simples, Reglas escalonadas y Q-learning con el mismo protocolo.
- Pruebas: discretización, actualización de Bellman, reproducibilidad, capacidad, exportación y recuperación del modelo.

### V2.6.0 — Deep Q-Network

- Se añade DQN con una red de 13 entradas, dos capas ocultas configurables y cuatro salidas.
- Se incorporan replay buffer circular, red objetivo, Bellman, Adam y recorte de gradiente.
- Entrenamiento por pasos con semillas separadas de evaluación e historial por ventanas.
- El modelo se persiste en NPZ sin serialización ejecutable.
- El notebook 07 compara políticas base, Q-learning y DQN bajo el mismo protocolo.
- Se conserva exclusivamente la estratificación de riesgo bajo, medio y alto.
- Pruebas: red, replay circular, reproducibilidad, sincronización objetivo, capacidad y recuperación del modelo.

### V2.7.0 — Proximal Policy Optimization

- Se añade PPO discreto con red actor-crítico compartida de 13 entradas y cuatro acciones.
- Se implementan rollouts on-policy, ventaja generalizada, objetivo recortado, entropía y parada temprana por KL.
- Entrenamiento reproducible con semillas separadas de evaluación e historial por actualización.
- El modelo se persiste en NPZ sin serialización ejecutable.
- El notebook 08 compara políticas base, Q-learning, DQN y PPO bajo el mismo protocolo.
- Se conserva exclusivamente la estratificación de riesgo bajo, medio y alto.
- Pruebas: probabilidades, GAE, reproducibilidad, actualización, capacidad y recuperación del modelo.

### V2.8.0 — Evaluación integral y equidad operativa

- Se comparan las seis políticas con la misma cohorte, dinámica, costos, horizonte y semillas.
- Se incorpora estabilidad entre semillas para recompensa, eventos, recursos, utilización, cobertura y ajustes.
- Se añaden escenarios configurables de sensibilidad a capacidad, sin presentar sus valores como capacidad institucional observada.
- Se calculan métricas de cobertura, intensidad, ajustes, eventos y recompensa por sexo codificado, grupo de edad y riesgo.
- Las brechas max-min se documentan como diagnósticos operativos descriptivos, no como pruebas de equidad clínica o causal.
- El notebook 09 exige modelos Q-learning, DQN y PPO ya entrenados y exporta tablas CSV con manifiesto.
- Se conserva exclusivamente la estratificación de riesgo bajo, medio y alto.
- Validación acumulada: 34 pruebas aprobadas y sintaxis de las celdas ejecutables verificada.

## Recuperación

Para volver al estado anterior sin eliminar historial:

```bash
git switch main
git pull origin main
```

Para comparar la nueva versión con la línea base:

```bash
git diff 542d2cd5765b9f82e8a2f93f01240eb604eba52a..feature/entorno-capacidad-v2
```

Para inspeccionar un avance concreto:

```bash
git show <SHA_DEL_COMMIT>
```

Si la rama ya fue integrada, se deberá revertir el commit de fusión mediante `git revert`; no se utilizará `git reset --hard` sobre `main`.
