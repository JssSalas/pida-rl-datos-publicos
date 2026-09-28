# Changelog

Los cambios relevantes del proyecto se documentan en este archivo.

## [No publicado]

### Añadido

- Configuración central para acciones, costos y capacidad mensual.
- Registro de acción propuesta, acción ejecutada y motivo de ajuste.
- Recursos restantes como componente del estado del agente.
- Pruebas de invariantes de capacidad y degradación de acciones.
- Documento `docs/CONTROL_CAMBIOS.md` con línea base y recuperación.

### Cambiado

- El entorno impide exceder la capacidad en vez de limitarse a penalizar el exceso.
- Los costos predeterminados son 0, 1, 3 y 5 unidades para acciones 0, 1, 2 y 3.

### Compatibilidad

- La observación pasa de 8 a 9 elementos y requiere reentrenar modelos existentes.
