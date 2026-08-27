
## Calibración final de categoría de riesgo

Se recalibró el umbral de riesgo usando percentiles de la distribución empírica 
del score (complicaciones×2 + comorbilidades), en lugar de un corte fijo 
arbitrario. Los percentiles 50 y 80 de la cohorte (n=1,544) definen los cortes 
medio/alto.

Distribución resultante:
- Bajo riesgo: 600 personas (38.9%)
- Medio riesgo: 552 personas (35.8%)
- Alto riesgo: 392 personas (25.4%)

Esta distribución es consistente con escenarios reales de capacidad operativa 
limitada, donde aproximadamente una cuarta parte de la cohorte requiere 
seguimiento prioritario.

## Calibración final de categoría de riesgo

Se recalibró el umbral de riesgo usando percentiles de la distribución empírica
del score (complicaciones×2 + comorbilidades), en lugar de un corte fijo
arbitrario. Los percentiles 50 y 80 de la cohorte (n=1,544) definen los cortes
medio/alto.

Distribución resultante:
- Bajo riesgo: 600 personas (38.9%)
- Medio riesgo: 552 personas (35.8%)
- Alto riesgo: 392 personas (25.4%)

Esta distribución es consistente con escenarios reales de capacidad operativa
limitada, donde aproximadamente una cuarta parte de la cohorte requiere
seguimiento prioritario.

## Tratamiento de valores faltantes

- Códigos especiales (8, 9, 98, 99, 998, 999 = "no sabe"/"no aplica") se recodificaron como valores faltantes antes de cualquier imputación.
- Variables binarias de complicaciones y comorbilidades: los valores faltantes se imputaron como 0 (ausencia de la condición), bajo el supuesto de que la falta de respuesta indica no haber presentado el evento.
- Variables numéricas continuas (edad, años con diabetes, frecuencia de control médico): los valores faltantes se imputaron con la mediana de la cohorte.
- Esta estrategia prioriza mantener el tamaño completo de la cohorte (n=1,544) sobre la eliminación de registros, dado el tamaño ya limitado de la muestra.
