# Dashboard PIDA-RL Diabetes México

## Propósito

Aplicación Streamlit para explorar resultados de simulación de políticas de priorización de seguimiento en personas con diabetes.

## Ejecución local

1. Instala dependencias:

```bash
pip install -r requirements.txt
```

2. Mantén la carpeta `dashboard_data` junto a la carpeta `dashboard_streamlit`.

3. Desde el directorio que contiene ambas carpetas ejecuta:

```bash
streamlit run dashboard_streamlit/app.py
```

## Alcance

Los resultados provienen de un simulador con datos públicos y supuestos explícitos. La aplicación no usa datos clínicos reales, no es un dispositivo médico y no debe utilizarse para decisiones clínicas individuales.

La auditoría disponible es por nivel de riesgo. No se infieren ni se muestran resultados por sexo o edad porque las trazas de evaluación agregadas no contienen esos atributos.
