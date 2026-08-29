
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

## Tratamiento de valores faltantes (resultado aplicado)

Se identificaron 5 casos con código especial 99 ("no sabe") en `a0302` (edad al diagnóstico) y 1 caso en `a0303num` (frecuencia de control médico). Ambos se recodificaron como valores faltantes y se imputaron con la mediana de la cohorte (n=1,544). La variable derivada `anios_con_diabetes` se recalculó después de esta corrección para evitar valores inconsistentes. Las variables binarias de complicaciones y comorbilidades no presentaron valores faltantes adicionales tras el filtrado inicial; se imputaron como 0 los casos sin respuesta, bajo el supuesto de ausencia de la condición.

## Corrección de codificación en variables binarias

Se detectó que las variables `a0406a` (hipertensión) y `a0604` (colesterol) conservaban la codificación original de ENSANUT (1=Sí, 2=No), mientras que las variables de complicaciones (a0316a-j) ya habían sido binarizadas. Al aplicar imputación de faltantes con 0 sobre la codificación cruda, se generó ambigüedad entre "No" (código 2 original) y el valor de imputación. Se corrigió recodificando explícitamente todas las variables binarias desde su origen: 1->1 (Sí), 2->0 (No), y códigos especiales (8, 9, 98, 99)->NaN antes de imputar. El score de riesgo y la categoría de riesgo se recalcularon con los datos corregidos.

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
