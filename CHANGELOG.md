# Changelog

Los cambios relevantes del proyecto se documentan en este archivo.

## [No publicado]

### Añadido

- Configuración central para acciones, costos y capacidad mensual.
- Registro de acción propuesta, acción ejecutada y motivo de ajuste.
- Recursos restantes como componente del estado del agente.
- Evaluación detallada por paciente, mes, semilla y algoritmo.
- Tablas separadas de clasificaciones propuestas y ejecutadas para las acciones 0 a 3.
- Políticas base reproducibles: aleatoria, reglas simples y reglas escalonadas.
- Q-learning, DQN y PPO reproducibles con persistencia NPZ.
- Notebooks 05–09 para políticas base, entrenamiento y evaluación integral.
- Evaluación de estabilidad, sensibilidad a capacidad y brechas operativas por subgrupo.
- Dashboard Streamlit V2 con filtros, trazabilidad y descarga de tablas.
- Validación explícita que impide introducir una cuarta categoría de riesgo.
- Flujo de integración continua para Python 3.10, 3.11 y 3.12.
- Archivo raíz `requirements.txt` para instalación reproducible.
- Matriz `docs/CRISP_DM.md` que enlaza fases, evidencia y puertas de aceptación.
- Protocolo `docs/VALIDACION_REPRODUCIBILIDAD.md` para reconstrucción, pruebas y recuperación.
- Verificación estática con Ruff dentro de la matriz de integración continua.

### Cambiado

- El entorno impide exceder la capacidad en vez de limitarse a penalizar el exceso.
- Los costos predeterminados son 0, 1, 3 y 5 unidades para acciones 0, 1, 2 y 3.
- El estado utiliza 13 variables, incluida la fracción de recursos restantes.
- `FOLIO_INT` se conserva como identificador técnico en los reportes.
- La estratificación continúa limitada a `bajo`, `medio` y `alto`; `score_riesgo` gradúa la intensidad dentro de medio y alto.
- El dashboard consume directamente las salidas auditables del notebook 09.
- El README refleja la arquitectura, ejecución y estado real de la rama V2.
- La comprobación de importaciones de CI referencia la API pública real de evaluación integral.
- Ruff queda fijado en la versión 0.13.2 para que la validación estática sea determinista y reproducible.

### Corregido

- Fallo inicial de CI en Python 3.10–3.12 causado por importar un símbolo inexistente después de que las 39 pruebas habían terminado correctamente.
- Tres incidencias E702 de estilo en las pruebas DQN y PPO detectadas durante la auditoría previa al pull request.
- Segundo fallo de CI causado por resolver automáticamente una versión futura de Ruff con reglas adicionales no presentes en la versión auditada.

### Compatibilidad

- Los modelos anteriores deben reentrenarse porque cambió la semántica de capacidad, costos y observación.
- El umbral predeterminado `score_riesgo >= 6` para teleorientación es un supuesto operativo configurable, no una categoría ni un punto de corte clínico validado.
- El dashboard V2 requiere los CSV integrales; los archivos V1 se conservan solo como legado.
