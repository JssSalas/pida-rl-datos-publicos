# Dashboard PIDA-RL V2

Aplicación Streamlit para explorar la evaluación integral de políticas de priorización de seguimiento en personas con diabetes. Consume directamente los CSV generados por `09_evaluacion_integral_equidad_v2.ipynb`.

## Preparación

1. Ejecuta los notebooks 03 y 05–09 en orden.
2. Copia la carpeta de resultados integrales a `dashboard_data/v2` o define la variable `PIDA_DASHBOARD_DATA_DIR`.
3. Conserva `manifest.csv` junto con los demás CSV para validar archivos y conteos.

La carpeta debe contener, como mínimo:

- `episodios.csv`
- `resumen_algoritmos.csv`
- `clasificaciones_propuestas.csv`
- `clasificaciones_ejecutadas.csv`
- `estabilidad_semillas.csv`
- `metricas_subgrupos.csv`
- `brechas_equidad.csv`

Las tablas `detalle.csv`, `sensibilidad_episodios.csv` y `sensibilidad_resumen.csv` son opcionales, aunque habilitan trazabilidad y análisis adicionales.

## Ejecución local

```bash
pip install -r dashboard_streamlit/requirements.txt
streamlit run dashboard_streamlit/app.py
```

Para usar otra carpeta:

```bash
PIDA_DASHBOARD_DATA_DIR=/ruta/al/reporte streamlit run dashboard_streamlit/app.py
```

## Secciones

- **Panorama:** métricas comparables de las políticas seleccionadas.
- **Clasificaciones:** contraste entre acciones propuestas y ejecutadas `0–3`.
- **Capacidad:** sensibilidad por escenario y estabilidad entre semillas.
- **Equidad:** métricas y brechas descriptivas por sexo codificado, edad y riesgo.
- **Trazabilidad:** manifiesto, huella del reporte y descargas CSV filtradas.

## Acuerdos metodológicos

La estratificación mantiene únicamente `bajo`, `medio` y `alto`. `3 = Teleorientación` es una acción y no una cuarta categoría de riesgo. Los escenarios de capacidad son supuestos del simulador, no estimaciones de capacidad institucional.

Los resultados provienen de un entorno de simulación construido con datos públicos y supuestos explícitos. La aplicación no es un dispositivo médico y no debe utilizarse para decisiones clínicas individuales. Las brechas mostradas son diagnósticos operativos descriptivos; no constituyen pruebas causales ni de equidad clínica.
