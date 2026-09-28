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
- Pruebas del protocolo de evaluación y de la estructura de los reportes.

### Cambiado

- El entorno impide exceder la capacidad en vez de limitarse a penalizar el exceso.
- Los costos predeterminados son 0, 1, 3 y 5 unidades para acciones 0, 1, 2 y 3.
- La interfaz histórica `evaluar_politica` se conserva, pero internamente utiliza el registro detallado.

### Compatibilidad

- La observación pasa de 8 a 9 elementos y requiere reentrenar modelos existentes.
