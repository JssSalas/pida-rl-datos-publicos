# pida-rl-datos-publicos
# Priorización Adaptativa de Seguimiento en Personas con Diabetes en México mediante Aprendizaje por Refuerzo

## Descripción

Este Proyecto Integrador de Dominio Autónomo (PIDA) desarrolla y evalúa un agente de Aprendizaje por Refuerzo (RL) para priorizar la intensidad de seguimiento mensual de perfiles de personas con diabetes en México.

El proyecto utiliza fuentes públicas y un entorno de simulación. Su propósito es comparar políticas de asignación de recursos limitados para seguimiento, sin generar recomendaciones clínicas individuales ni utilizar datos personales identificables.

## Problema de negocio

Los programas de seguimiento para personas con diabetes tienen capacidad limitada para realizar llamadas, mensajes y teleorientación. Una asignación uniforme de recursos puede dejar sin atención oportuna a perfiles de mayor riesgo.

El problema consiste en decidir qué intensidad de seguimiento asignar a cada perfil de riesgo, procurando mejorar los resultados simulados, cubrir a las personas de alto riesgo, respetar la capacidad operativa y evitar inequidades entre subgrupos.

## Objetivo general

Construir y evaluar un entorno de simulación tipo Gymnasium para entrenar agentes de Aprendizaje por Refuerzo que asignen de forma adaptativa la intensidad mensual de seguimiento a perfiles de personas con diabetes en México.

## Objetivos específicos

- Construir un entorno de simulación basado en un Proceso de Decisión de Márkov.
- Usar fuentes públicas para parametrizar perfiles de riesgo y transiciones simuladas.
- Implementar políticas de referencia aleatoria y basada en reglas de riesgo.
- Entrenar y comparar Q-learning, DQN y PPO.
- Evaluar recompensa acumulada, cobertura de alto riesgo, uso de recursos y equidad.
- Desarrollar un dashboard en Streamlit para explorar los resultados.
- Documentar el proyecto conforme a CRISP-DM.

## Alcance y exclusiones

### Incluye

- Datos públicos agregados o microdatos públicos autorizados.
- Simulación de cohortes o perfiles sintéticos no identificables.
- Evaluación comparativa de políticas de seguimiento.
- Dashboard exploratorio para comunicar resultados.

### No incluye

- Diagnóstico, tratamiento o prescripción clínica.
- Uso de expedientes clínicos reales o datos personales identificables.
- Recomendaciones automatizadas para pacientes reales.
- Implementación clínica directa sin validación institucional, ética y regulatoria.

## Metodología CRISP-DM

| Fase | Actividades principales | Entregables |
|---|---|---|
| 1. Entendimiento del negocio | Problema, actores, objetivos, criterios de éxito y restricciones | Definición del PIDA y plan de trabajo |
| 2. Entendimiento de los datos | Identificación de fuentes, ingestión, diccionario y análisis exploratorio | Bitácora de fuentes y diagnóstico de calidad |
| 3. Preparación de los datos | Limpieza, transformación, ingeniería de variables y construcción de perfiles | Dataset procesado y bitácora de preparación |
| 4. Modelación | Diseño del MDP, políticas base, Q-learning, DQN y PPO | Entorno Gymnasium y modelos entrenados |
| 5. Evaluación | Comparación de políticas, capacidad, cobertura, equidad y sensibilidad | Reporte de evaluación y selección del modelo |
| 6. Despliegue | Dashboard, repositorio y documentación técnica | Aplicación Streamlit y documentación final |

## Fuentes públicas previstas

- ENSANUT: perfiles de riesgo, diagnóstico autorreportado y variables sociodemográficas.
- DGIS/SINAIS: indicadores de atención, egresos y capacidad del sistema de salud.
- INEGI: mortalidad por diabetes por entidad, sexo y grupo de edad.
- CENAPRECE y normativa mexicana: criterios de prevención, seguimiento y estratificación de riesgo.

Consulta el detalle de fuentes, variables, fecha de descarga y condiciones de uso en [`docs/data_sources.md`](docs/data_sources.md).

## Diseño del entorno RL

### Estado

El estado representa un perfil mensual simulado e incluirá variables como:

- Grupo de edad.
- Sexo.
- Diagnóstico previo de diabetes.
- Categoría de riesgo metabólico.
- Comorbilidades.
- Antecedente de contacto.
- Adherencia estimada.
- Vulnerabilidad social.
- Mes o tiempo restante del episodio.

### Acciones

| Acción | Intervención simulada |
|---:|---|
| 0 | Sin contacto |
| 1 | Mensaje educativo o recordatorio |
| 2 | Llamada de seguimiento |
| 3 | Teleorientación prioritaria |

### Recompensa

La recompensa combinará:

- Beneficio por cobertura o mejora simulada de perfiles de alto riesgo.
- Penalización por eventos adversos simulados.
- Penalización por exceder la capacidad de seguimiento.
- Penalización por brechas injustificadas entre subgrupos.

Las probabilidades de transición serán supuestos explícitos, calibrados con evidencia pública y evaluados mediante análisis de sensibilidad.

## Métricas de evaluación

- Recompensa acumulada media por episodio.
- Cobertura de perfiles de alto riesgo.
- Uso de recursos respecto a la capacidad disponible.
- Tasa de eventos adversos simulados.
- Equidad de cobertura y resultados entre subgrupos.
- Tiempo de entrenamiento y estabilidad entre semillas.

## Estructura del repositorio

```text
├── app/                 # Dashboard Streamlit
├── data/
│   ├── raw/             # Datos descargados; no versionados
│   ├── processed/       # Datos preparados; no versionados si son sensibles o pesados
│   └── results/         # Resultados reproducibles resumidos
├── docs/                # Documentación CRISP-DM y metodología
├── notebooks/           # Notebooks de Colab reproducibles
├── reports/             # Figuras, tablas e informe ejecutivo
├── src/
│   ├── data/            # Ingesta y preparación
│   ├── environment/     # Entorno Gymnasium
│   ├── policies/        # Políticas aleatoria y por reglas
│   ├── models/          # Q-learning, DQN y PPO
│   └── evaluation/      # Métricas, equidad y sensibilidad
├── tests/               # Pruebas automatizadas
├── .gitignore
├── requirements.txt
└── README.md
```

## Instalación

```bash
git clone https://github.com/[usuario]/[repositorio].git
cd [repositorio]
pip install -r requirements.txt
```

Para Google Colab, abre el notebook `notebooks/00_setup.ipynb` y ejecuta sus celdas en orden.

## Reproducibilidad

- Todas las ejecuciones deben registrar semilla, fecha, versión de librerías, configuración del entorno e hiperparámetros.
- Los modelos se comparan con el mismo horizonte temporal, tamaño de cohorte, restricciones operativas y conjunto de semillas.
- No se cargan credenciales, tokens, datos personales ni microdatos restringidos al repositorio.

## Consideraciones éticas y de seguridad

Este proyecto es un prototipo de investigación y simulación. No sustituye el juicio clínico, la evaluación médica ni la validación de instituciones de salud.

Las conclusiones deben interpretarse como resultados de un entorno simulado y no como evidencia causal o recomendación clínica. Cualquier aplicación con datos reales requiere aprobación institucional, evaluación ética, controles de seguridad, validación externa y monitoreo de sesgos.

## Estado del proyecto

**Fase actual:** Entendimiento del negocio y recopilación de fuentes públicas.

- [x] Definición preliminar del problema.
- [x] Identificación inicial de fuentes públicas.
- [ ] Descarga y diccionario de datos.
- [ ] Análisis exploratorio.
- [ ] Construcción del entorno Gymnasium.
- [ ] Implementación de políticas base.
- [ ] Entrenamiento de agentes RL.
- [ ] Evaluación y análisis de sensibilidad.
- [ ] Dashboard Streamlit.
- [ ] Despliegue y documentación final.

## Autor

**Jesús Carlos Salas García**  
PIDA — Certificación Senior Data Scientist  
Dominio de aplicación: Aprendizaje por Refuerzo
