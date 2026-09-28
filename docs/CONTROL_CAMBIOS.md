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

**Estado:** En desarrollo.

- Se añade `notebooks/05_politicas_base_capacidad_v2.ipynb`.
- La capacidad, los costos, el horizonte y las semillas se ajustan desde una sola sección.
- Se reutiliza `cohorte_diabetes.csv` generada por el notebook 03.
- Se evalúan ambas políticas bajo el mismo protocolo.
- Se comprueba que no existan recursos negativos ni excesos de capacidad.
- Se exportan detalle, episodios, resumen y distribuciones de acciones a Google Drive.

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
