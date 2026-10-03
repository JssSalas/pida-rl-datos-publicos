# Bitácora de fuentes públicas

## ENSANUT Continua 2022

- **Institución:** Instituto Nacional de Salud Pública (INSP)
- **URL de descarga:** https://ensanut.insp.mx/encuestas/ensanutcontinua2022/descargas.php
- **Formato:** SPSS (.sav), Stata (.dta), CSV
- **Fecha de descarga:** [completar]
- **Variables clave:** edad, sexo, diagnóstico previo de diabetes, comorbilidades.
- **Variables usadas en la cohorte:** ver la verificación en `docs/CUMPLIMIENTO_PIDA.md`, sección 4. Glucosa, IMC y entidad federativa no forman parte del estado actual; los archivos `Muestras_Sangre` descargados no contienen glucosa.
- **Uso en el proyecto:** construcción de perfiles de riesgo (estado del entorno RL)
- **Condiciones de uso:** dato público, sin identificación individual; citar INSP como fuente

## CENAPRECE — Cuestionario de factores de riesgo

- **Institución:** Centro Nacional de Programas Preventivos y Control de Enfermedades
- **URL:** http://www.cenaprece.salud.gob.mx/programas/interior/adulto/descargas/pdf/DIABETES.pdf
- **Formato:** PDF
- **Fecha de descarga:** [completar]
- **Uso en el proyecto:** definición de reglas de riesgo para la política de referencia

## DGIS/SINAIS — Datos Abiertos Secretaría de Salud

- **Institución:** Dirección General de Información en Salud
- **URL:** http://www.dgis.salud.gob.mx/contenidos/basesdedatos/Datos_Abiertos_gobmx.html
- **Formato:** CSV
- **Fecha de descarga:** [completar]
- **Uso en el proyecto:** calibrar capacidad operativa del sistema de salud

## INEGI — Mortalidad por diabetes mellitus

- **Institución:** Instituto Nacional de Estadística y Geografía
- **URL:** https://www.inegi.org.mx/app/tabulados/interactivos/?px=Mortalidad_04&bd=Mortalidad
- **Formato:** Tabulado interactivo (exportable a CSV)
- **Fecha de descarga:** [completar]
- **Uso en el proyecto:** contexto de mortalidad (110 059 defunciones por diabetes en 2023, EDR 2023). El código actual no calibra ni valida las tasas simuladas con INEGI; ver la limitación L4 de `docs/CUMPLIMIENTO_PIDA.md`.

## Decisión metodológica: clasificación de diabetes

Se optó por clasificar el estado de diabetes únicamente mediante **diagnóstico
previo autorreportado** (variable `a0301` de la base Adultos_ENSANUT_2022),
consistente con la metodología de reporte oficial del INSP para prevalencia por
diagnóstico médico.

**Limitación documentada:** no se incluye la clasificación de diabetes no
diagnosticada (que requeriría valores bioquímicos de glucosa en ayuno), debido a
 que el archivo de laboratorio disponible (`Muestras_Sangre_ENSANUT_2022.sav`)
 corresponde a pruebas de papel filtro (hemoglobina), no a química sanguínea.
 Esta limitación se declara explícitamente en el reporte de evaluación del
 proyecto.
