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

### V2.0.0 — Capacidad operativa estricta

**Estado:** En desarrollo.

**Archivos modificados o añadidos:**

- `src/config.py`
- `src/environment/diabetes_followup_env.py`
- `tests/test_resource_constraint.py`
- `CHANGELOG.md`
- `docs/CONTROL_CAMBIOS.md`

**Cambios funcionales:**

- Se centralizan nombres, costos de acciones y capacidad predeterminada.
- Se separan la acción propuesta por el algoritmo y la acción realmente ejecutada.
- Si faltan recursos, la acción se reduce hasta encontrar la intervención viable de mayor intensidad.
- Los recursos se descuentan inmediatamente y nunca pueden quedar negativos.
- La observación incorpora la fracción de recursos mensuales restantes.
- `info` conserva los campos necesarios para un reporte por paciente y mes.

**Riesgos de compatibilidad:**

- La observación cambia de 8 a 9 variables; los modelos previamente entrenados deben reentrenarse.
- Los costos cambian de `0, 1, 2, 3` a `0, 1, 3, 5`.
- La evaluación debe usar `accion_ejecutada`, no solamente la acción propuesta.

**Validación mínima:**

```bash
pytest -q tests/test_resource_constraint.py
```

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

Si la rama ya fue integrada, se deberá revertir el commit de fusión mediante `git revert`; no se utilizará `git reset --hard` sobre `main`.
