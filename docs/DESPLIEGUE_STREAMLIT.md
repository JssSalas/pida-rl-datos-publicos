# Despliegue del dashboard (V2.13.0)

El repositorio publica dos aplicaciones Streamlit. Ambas se pueden desplegar desde la misma rama en Streamlit Community Cloud.

| Aplicación | Main file path | Datos versionados | Origen de los datos |
|---|---|---|---|
| **Principal V2** (capacidad estricta) | `dashboard_streamlit/app.py` | `dashboard_data/v2/` | Notebook `09_evaluacion_integral_equidad_v2_corregido`, modo completo, exportado por el notebook 12 corregido |
| **Línea v1** (entorno autocontenido) | `dashboard_streamlit_v1/app.py` | `dashboard_data/*_v1.*` | Notebooks 05–11 autocontenidos, ejecución completa en Colab |

- `dashboard_streamlit_v1/app.py` es idéntico al `dashboard_streamlit/app.py` de `main`, es decir, al generado por el notebook 12.
- Se movió a su propia carpeta para que el notebook 13 no sobrescriba el dashboard V2.
- `dashboard_data/v2/` contiene solo tablas agregadas y `manifest.csv`.
- `detalle.csv`, que es la traza por perfil y mes, se excluye explícitamente en `.gitignore`.

## Desplegar en Streamlit Community Cloud

1. Entra a [share.streamlit.io](https://share.streamlit.io/) con la cuenta de GitHub `JssSalas`.
2. Selecciona **Create app → Deploy a public app from GitHub**.
3. Configura la aplicación:
   - **Repository:** `JssSalas/pida-rl-datos-publicos`
   - **Branch:** `feature/entorno-capacidad-v2`. Usa `main` cuando el pull request #1 se haya integrado.
   - **Main file path:** `dashboard_streamlit/app.py`. Para la línea v1 usa `dashboard_streamlit_v1/app.py`.
   - **Python:** 3.12. En *Advanced settings* no se requieren secretos.
4. Selecciona **Deploy**. Cada aplicación instala el `requirements.txt` de su carpeta (`streamlit`, `pandas` y `plotly`).

Si ya existe una app desplegada desde `main` con `dashboard_streamlit/app.py`, seguirá mostrando la versión v1 hasta que se integre el PR. Después mostrará el dashboard V2, porque en esa ruta vivirá la aplicación V2 y sus datos en `dashboard_data/v2/`.

## Vista temporal desde Colab (ngrok)

Ejecuta los notebooks en `notebooks/corregidos/linea_v1_despliegue/` hasta el 13.

1. En **Secretos** de Colab, define `NGROK_AUTHTOKEN` con acceso habilitado para el notebook.
2. `DASHBOARD_VERSION = 'v2'` es el valor por defecto. Para la línea v1, define `PIDA_DASHBOARD_VERSION=v1`.
3. La celda A0 renderiza ambas aplicaciones con `streamlit.testing` y falla si encuentra errores.
4. La celda A2 inicia Streamlit, comprueba `/_stcore/health` y abre el túnel. Sin token, el dashboard se sirve solo de forma local.

## Publicar datos actualizados

El flujo B del notebook 13 publica los datos actualizados:

1. B1 copia `dashboard_streamlit_v1/`, `dashboard_data/*_v1.*` y `dashboard_data/v2/`.
2. B2 muestra los cambios.
3. B4 publica solo si `CONFIRMACION_PUBLICACION = 'PUBLICAR'`.

Reglas de B4:
- Se rechaza publicar en `main`.
- Se exige el secreto `TOKEN-pida-rl-datos-publicos` (o la variable `GITHUB_TOKEN`).
- En modo prueba, B1 y B4 se omiten para no publicar resultados de prueba.

## Verificación automática

`tests/test_dashboard_despliegue.py` se ejecuta en CI con Python 3.10, 3.11 y 3.12. Comprueba que:

- los datos V2 publicados pasan `load_integral_report`, no incluyen `detalle.csv` y contienen solo los riesgos bajo, medio y alto;
- ambas aplicaciones renderizan sin excepciones ni mensajes de error usando los datos versionados.

## Alcance

Los resultados provienen de un simulador construido con datos públicos (ENSANUT 2022) y supuestos explícitos. Las aplicaciones no son dispositivos médicos y no deben usarse para decisiones clínicas individuales.
