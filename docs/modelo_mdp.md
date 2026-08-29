
# Diseño del Proceso de Decisión de Márkov (MDP)

## Unidad de decisión

Cada episodio simula el seguimiento mensual de una cohorte de personas con diabetes diagnosticada (n=1,544, ENSANUT Continua 2022) durante un horizonte de 12 meses.

## Espacio de estados

El estado de cada perfil en el mes t se representa como un vector con las siguientes variables:

| Variable | Tipo | Fuente | Rango |
|---|---|---|---|
| edad | Continua (normalizada) | ENSANUT Adultos | 20-99 |
| sexo | Binaria | ENSANUT Adultos | 0/1 |
| anios_con_diabetes | Continua (normalizada) | Derivada | 0-80 |
| num_complicaciones | Discreta | Derivada (a0316a-j consolidada) | 0-9 |
| num_comorbilidades | Discreta | Derivada (a0406a, a0604) | 0-2 |
| categoria_riesgo | Categórica (codificada ordinal) | Derivada (percentiles) | bajo/medio/alto |
| meses_sin_contacto | Discreta | Simulada (dinámica del entorno) | 0-12 |
| mes_actual | Discreta | Simulada | 1-12 |

Las primeras seis variables provienen de ENSANUT y son fijas por episodio (definen el perfil). Las dos últimas son dinámicas: cambian según las acciones del agente durante la simulación.

## Espacio de acciones

| Acción | Descripción | Costo en recursos (unidades) |
|---:|---|---:|
| 0 | Sin contacto | 0 |
| 1 | Mensaje educativo/recordatorio | 1 |
| 2 | Llamada de seguimiento | 2 |
| 3 | Teleorientación prioritaria | 3 |

## Restricción de capacidad operativa

En cada mes, la suma de costos de las acciones ejecutadas sobre toda la cohorte no puede exceder un presupuesto fijo (por ejemplo, 20% de la cohorte con acción 2 o 3, definido como parámetro configurable del entorno).

## Función de transición (supuestos parametrizados)

Las probabilidades de que un perfil mejore, se mantenga o empeore en su categoría de riesgo dependen de:
- La acción recibida (mayor intensidad → mayor probabilidad de mejora o estabilidad).
- Los meses sin contacto acumulados (más meses sin contacto → mayor probabilidad de empeorar).
- La categoría de riesgo actual (perfiles de alto riesgo tienen mayor probabilidad basal de eventos adversos).

Estas transiciones son supuestos explícitos calibrados con literatura de referencia y sometidos a análisis de sensibilidad; no son datos observados longitudinalmente.

## Función de recompensa

r(s, a) = w1 * cobertura_alto_riesgo - w2 * penalizacion_evento_adverso - w3 * exceso_capacidad - w4 * inequidad_subgrupo

Donde:
- **cobertura_alto_riesgo**: recompensa positiva por atender (acción >= 2) a un perfil de alto riesgo.
- **penalizacion_evento_adverso**: penalización fuerte si un perfil sin seguimiento adecuado sufre un evento adverso simulado.
- **exceso_capacidad**: penalización si se excede el presupuesto operativo mensual.
- **inequidad_subgrupo**: penalización por diferencias sistemáticas de cobertura entre sexo/edad.

## Horizonte y criterio de terminación

Episodio de longitud fija: 12 meses (un año simulado). No hay terminación anticipada, salvo un límite máximo de eventos adversos acumulados (opcional, a definir en la etapa de evaluación).

## Corrección de codificación de sexo

Durante la validación con `check_env()` se identificó que la variable `sexo` conservaba la codificación original de ENSANUT, donde el valor 2 representaba una categoría válida. Debido a que el espacio de observación del entorno utiliza valores normalizados entre 0 y 1, la variable se recodificó como una variable binaria: 1 original -> 0 y 2 original -> 1. Se verificó que las observaciones generadas por `reset()` y `step()` cumplen los límites declarados en `observation_space`.

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
