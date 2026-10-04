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

- Configuración central, acciones propuestas y ejecutadas, descuento real de recursos y auditoría por decisión.
- Validación: cinco pruebas aprobadas.

### V2.1.0 — Evaluación trazable

**Commit:** `d402995f9b1b5cee6cab3e2ecc01c2d71ffad195`.

- Registro por política, semilla, perfil y mes; resúmenes comparables y cinco CSV.

### V2.2.0 — Cohorte y políticas base

**Commit:** `9d242aadcd05978a6c331c672ab0e8e99dedd20f`.

- Estado de 13 variables, conservación de `FOLIO_INT`, política aleatoria y reglas simples.

### V2.3.0 — Notebook de comparación base

**Commit:** `d47872beb09775ea8b05c5f9f63e7a9ed3f2528e`.

- Notebook 05 con configuración central, verificaciones de capacidad y exportación a Drive.

### V2.4.0 — Reglas escalonadas

**Commit:** `572d990d9d59d1338505cac071ad5c7c867057ae`.

- Bajo propone 0; medio 1 o 2; alto 2 o 3.
- No se crea una cuarta categoría; el umbral de teleorientación es configurable.

### V2.5.0 — Q-learning tabular

**Commit:** `4b588cf430b09f6b35aad67b7327d1524bcf484f`.

- Q-learning epsilon-greedy, Bellman, discretización, historial y persistencia NPZ.

### V2.6.0 — Deep Q-Network

**Commit:** `53b0cf21b756b7f7ba6818f496dd8254f097118b`.

- DQN con replay, red objetivo, Adam, recorte de gradiente y notebook 07.

### V2.7.0 — Proximal Policy Optimization

**Commit:** `4e85b79afd7df1e5620be1824dc6e3096c16b4a4`.

- PPO actor-crítico, GAE, objetivo recortado, entropía, KL y notebook 08.

### V2.8.0 — Evaluación integral y equidad operativa

**Commit:** `f3941ab60053dbb8fe0c6f7bae57dc12cc5d35f0`.

- Seis políticas bajo un protocolo común, estabilidad, sensibilidad y brechas descriptivas.
- Validación acumulada reportada en el bloque: 34 pruebas aprobadas.

### V2.9.0 — Dashboard Streamlit integral

**Commit:** `9194301b3900668182aeb082024f529cea7619d5`.

- Dashboard conectado a CSV integrales, filtros comunes, acciones 0–3, sensibilidad, estabilidad y equidad.
- Cargador con validación de esquema, manifiesto, categorías y huella de archivos.

### V2.10.0 — Reproducibilidad, CI y cierre CRISP-DM

**Commit:** `2404b78526f2f85e59883329da316666ebf0db02`.

- Se añade `requirements.txt` en la raíz con rangos compatibles y explícitos.
- GitHub Actions valida Python 3.10–3.12 mediante instalación, compilación, importaciones y pruebas.
- Se crea la matriz CRISP-DM con evidencia y puertas de aceptación.
- Se documentan el orden de ejecución, metadatos mínimos, invariantes y lista previa a fusión.
- El README se alinea con la arquitectura y estado real de V2.
- Este bloque no modifica las políticas, recompensas, transiciones ni categorías de riesgo.

### V2.11.0 — Auditoría final y reparación de CI

**Commit de auditoría inicial:** `d27e6aa929f196157c022451daa271efa55d3b13`.

- El primer flujo de CI ejecutó correctamente 39 pruebas en Python 3.10, 3.11 y 3.12, pero falló al importar un símbolo inexistente.
- La importación se alineó con `construir_reporte_integral`, parte de la API pública real del módulo.
- Se incorporó Ruff a CI y se corrigieron tres incidencias E702 en pruebas DQN/PPO.
- La segunda ejecución falló antes de las pruebas porque el rango abierto de Ruff resolvió la versión 0.16.9, cuyas reglas predeterminadas difieren de la 0.13.2 usada durante la auditoría.
- Para hacer el control estático determinista, Ruff queda fijado exactamente en 0.13.2; con esa versión el árbol completo supera la validación.
- Auditoría local: 39 pruebas aprobadas, árbol de trabajo limpio, sin archivos mayores a 5 MB, sin modelos o credenciales versionados y notebooks sin salidas ejecutadas.
- No se modifican políticas, recompensas, transiciones, costos, acciones ni categorías de riesgo.

### V2.11.1 — Resguardo manual de notebooks autocontenidos

**Commit:** `02ab45d580a6ac1627399cf6feffbf43694f90f7` (subida manual del usuario).

- Se añadieron nueve notebooks `06–14 *_autocontenido/_corregido` de una línea de trabajo paralela. No forman parte del flujo 00–09 auditado en V2.12.0.

### V2.12.0 — Notebooks corregidos 00–09 y ejecución de prueba

- Se crean diez notebooks corregidos en `notebooks/corregidos/`. Los originales no se modifican.
- Se resguardan sin cambios en `notebooks/historicos_colab/` los originales 00–04, que solo existían en Google Drive.
- Las rutas fijas de Drive se reemplazan por `PROJECT_ROOT` (datos y resultados) y `REPO_ROOT` (código).
- Se añade un modo prueba (`PIDA_MODO_PRUEBA=1`) con cohorte estratificada de 120 perfiles, capacidad proporcional y pocos episodios.
- Ejecución completa 00 → 09 sin errores. La cohorte regenerada es idéntica a la de Drive (1 542 × 16). Se registran cero violaciones de capacidad y solo aparecen las categorías bajo, medio y alto.
- La auditoría de columnas no encontró variables inexistentes. Las discrepancias metodológicas quedan documentadas en `docs/NOTEBOOKS_CORREGIDOS.md`.
- No se modifican `src/`, políticas, recompensas, transiciones, costos, acciones ni categorías de riesgo. `pytest` reporta 39 aprobadas.

### V2.13.0 — Línea v1 de despliegue y dashboards publicables

- Se corrigen los notebooks 05–14 autocontenidos en `notebooks/corregidos/linea_v1_despliegue/` y se resguarda el original 05 de Drive. Los originales no se modifican.
- Ejecución completa 05 → 14 en modo prueba sin errores.
- Se corrigen dos errores del notebook 14 que impedían terminarlo: un `SyntaxError` y un `NameError` en un f-string.
- El notebook 13 ya no sobrescribe el dashboard V2: el v1 se publica en `dashboard_streamlit_v1/` y los datos V2 en `dashboard_data/v2/`. Además, rechaza publicar en `main`, lee los secretos de Colab o de variables de entorno e incluye una prueba de humo con `streamlit.testing`.
- El notebook 12 exporta y valida el reporte integral V2 para el dashboard principal, sin `detalle.csv`.
- Nueva prueba `tests/test_dashboard_despliegue.py` y guía `docs/DESPLIEGUE_STREAMLIT.md`.
- No se modifican `src/`, políticas, recompensas, transiciones, costos, acciones ni categorías de riesgo.

## Recuperación

Para volver al estado estable sin eliminar historial:

```bash
git switch main
git pull origin main
```

Para comparar V2 con la línea base:

```bash
git diff 542d2cd5765b9f82e8a2f93f01240eb604eba52a..feature/entorno-capacidad-v2
```

Para inspeccionar un avance concreto:

```bash
git show <SHA_DEL_COMMIT>
```

Si la rama ya fue integrada, se deberá revertir el commit de fusión mediante `git revert`; no se utilizará `git reset --hard` sobre `main`.

### V2.14.0 — Cumplimiento de la Definición del PIDA

**Commits:** `cf65620` (código) y el commit de resultados y documentación posterior (ver `git log`).

- Protocolo de evaluación de los criterios de la sección 5 del PIDA:
  - 100 episodios por política en el escenario base;
  - 7 escenarios de robustez;
  - brechas por sexo y edad;
  - verificación del diccionario de datos.
- El entorno V2 lee la cohorte con NumPy. La equivalencia se verificó paso a paso contra la versión anterior (observaciones, recompensas, `info` y tabla Q), sin cambios en el MDP.
- Hallazgo documentado: γ se aplica por decisión (18 504 por episodio). Con γ = 0.95 el agente no percibe el costo de oportunidad de la capacidad. Con γ = 0.9995, Q-learning supera a Reglas simples (+1.4 %). Ver `docs/CUMPLIMIENTO_PIDA.md`.
- Validación: 48 pruebas aprobadas y Ruff sin observaciones. Ejecución completa de 05–10 sin errores.
