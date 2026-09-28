# Changelog

Los cambios relevantes del proyecto se documentan en este archivo.

## [No publicado]

### Añadido

- Configuración central para acciones, costos y capacidad mensual.
- Registro de acción propuesta, acción ejecutada y motivo de ajuste.
- Recursos restantes como componente del estado del agente.
- Pruebas de invariantes de capacidad y degradación de acciones.
- Documento `docs/CONTROL_CAMBIOS.md` con línea base y recuperación.
- Evaluación detallada por paciente, mes, semilla y algoritmo.
- Tablas separadas de clasificaciones propuestas y ejecutadas para las acciones 0 a 3.
- Resumen comparable por algoritmo y exportación de cinco tablas CSV.
- Políticas base reproducibles: aleatoria, reglas simples y reglas escalonadas.
- Notebook de Colab `05_politicas_base_capacidad_v2.ipynb` para ejecutar la primera comparación.
- Pruebas del protocolo de evaluación, reportes y políticas base.
- Regla escalonada configurable: riesgo medio propone mensaje o llamada; riesgo alto propone llamada o teleorientación.
- Prueba explícita que impide introducir una cuarta categoría de riesgo.

### Cambiado

- El entorno impide exceder la capacidad en vez de limitarse a penalizar el exceso.
- Los costos predeterminados son 0, 1, 3 y 5 unidades para acciones 0, 1, 2 y 3.
- El estado utiliza las 13 variables compatibles con la cohorte preparada por el notebook 03, incluida la fracción de recursos restantes.
- El identificador `FOLIO_INT` se conserva como `perfil_id` en el reporte.
- La interfaz histórica `evaluar_politica` se conserva, pero internamente utiliza el registro detallado.
- La estratificación continúa limitada a `bajo`, `medio` y `alto`; `score_riesgo` únicamente gradúa la intensidad dentro de medio y alto.

### Compatibilidad

- Aunque se conserva una observación de 13 elementos, su última variable representa capacidad estricta y los costos cambiaron; los modelos existentes deberán reentrenarse.
- El umbral predeterminado `score_riesgo >= 6` para teleorientación es un supuesto operativo configurable, no una categoría ni un punto de corte clínico validado.
