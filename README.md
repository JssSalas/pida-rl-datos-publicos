# Priorización Adaptativa de Seguimiento en Diabetes

Proyecto Integrador de Dominio Autónomo (PIDA) para comparar políticas de aprendizaje por refuerzo que asignan seguimiento mensual bajo capacidad operativa limitada en una cohorte simulada de personas con diabetes en México.

> Prototipo metodológico y de investigación. No genera recomendaciones clínicas individuales ni sustituye el juicio profesional.

## Problema

Los programas de seguimiento disponen de personal y canales limitados para mensajes, llamadas y teleorientación. El proyecto estudia cómo priorizar perfiles de mayor riesgo sin exceder la capacidad y cómo cambian los resultados entre políticas y subgrupos.

## Alcance

- Entorno Gymnasium con capacidad mensual estricta.
- Cuatro acciones: 0 sin contacto, 1 mensaje, 2 llamada y 3 teleorientación.
- Tres categorías de riesgo exclusivamente: `bajo`, `medio` y `alto`.
- Políticas aleatoria, reglas simples, reglas escalonadas, Q-learning, DQN y PPO.
- Evaluación de recompensa, cobertura, recursos, eventos simulados, estabilidad y brechas operativas.
- Dashboard Streamlit conectado a reportes auditables.

La acción 3 es una intensidad de seguimiento y **no** una cuarta categoría de riesgo. Los costos, transiciones, recompensas, capacidades y umbrales son supuestos configurables del simulador, no parámetros clínicos validados.

## Arquitectura

```text
├── .github/workflows/ci.yml       # Integración continua
├── dashboard_streamlit/           # Dashboard y cargador validado
├── docs/                          # CRISP-DM, fuentes, MDP y control de cambios
├── notebooks/                     # Flujo reproducible para Google Colab
├── reports/                       # Salidas resumidas
├── src/
│   ├── data/                      # Preparación y validación
│   ├── environment/               # Entorno Gymnasium
│   ├── evaluation/                # Reportes, sensibilidad y equidad
│   └── policies/                  # Baselines, Q-learning, DQN y PPO
├── tests/                         # Pruebas automatizadas
├── requirements.txt
└── README.md
```

## Instalación

```bash
git clone https://github.com/JssSalas/pida-rl-datos-publicos.git
cd pida-rl-datos-publicos
git switch feature/entorno-capacidad-v2
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
```

## Flujo de ejecución

1. Preparar la cohorte con los notebooks 01–03.
2. Validar políticas base con el notebook 05.
3. Entrenar Q-learning, DQN y PPO con los notebooks 06–08.
4. Generar la comparación integral y el manifiesto con el notebook 09.
5. Ejecutar el dashboard sobre los CSV resultantes.

```bash
export PIDA_DASHBOARD_DATA_DIR=/ruta/a/resultados_integrales
streamlit run dashboard_streamlit/app.py
```

Consulta [`docs/VALIDACION_REPRODUCIBILIDAD.md`](docs/VALIDACION_REPRODUCIBILIDAD.md) para el protocolo completo.

## Metodología CRISP-DM

| Fase | Evidencia principal | Estado |
|---|---|---|
| Negocio | Problema, objetivos, alcance y criterios | Implementada |
| Datos | Fuentes, EDA y diccionario | Implementada |
| Preparación | Cohorte y validaciones | Implementada |
| Modelación | Entorno, baselines, Q-learning, DQN y PPO | Implementada |
| Evaluación | Semillas comunes, capacidad, sensibilidad y subgrupos | Implementada |
| Despliegue | Dashboard, CI y documentación | En validación previa a fusión |

La matriz detallada está en [`docs/CRISP_DM.md`](docs/CRISP_DM.md).

## Evaluación

Todos los algoritmos deben usar la misma cohorte, dinámica, horizonte, costos, escenarios de capacidad y semillas de evaluación. Se conservan la acción propuesta por la política y la acción ejecutada por el entorno para cuantificar demanda no atendida.

Las brechas por sexo codificado, edad y riesgo son diagnósticos operativos descriptivos; no prueban discriminación, causalidad ni equidad clínica.

## Reproducibilidad

- El CI ejecuta sintaxis, importaciones y pruebas en Python 3.10–3.12.
- Los modelos se guardan en NPZ y deben asociarse con el SHA del código y su configuración.
- Los reportes integrales incluyen un manifiesto y el dashboard calcula una huella del conjunto cargado.
- `CHANGELOG.md` y `docs/CONTROL_CAMBIOS.md` permiten auditar y revertir cada bloque.

## Fuentes y ética

Las fuentes públicas y sus condiciones se documentan en [`docs/data_sources.md`](docs/data_sources.md). No deben versionarse credenciales, tokens, expedientes clínicos, información identificable ni microdatos restringidos.

Cualquier uso con datos institucionales requiere autorización, evaluación ética, calibración local, validación externa, controles de seguridad y monitoreo continuo.

## Estado

La versión V2 está en la rama `feature/entorno-capacidad-v2`. El entorno, seis políticas, evaluación integral y dashboard están implementados; el proyecto se encuentra en validación reproducible y preparación del pull request hacia `main`.

## Autor

**Jesús Carlos Salas García**  
PIDA — Certificación Senior Data Scientist  
Dominio: Aprendizaje por Refuerzo
