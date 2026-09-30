# Validación y reproducibilidad

## Propósito

Este protocolo permite reconstruir el entorno, comprobar sus invariantes y generar evidencia comparable sin depender de resultados guardados de una ejecución anterior.

## Entorno soportado

- Python 3.10, 3.11 o 3.12.
- Dependencias declaradas en `requirements.txt`.
- Ejecución local, GitHub Actions o Google Colab.

## Instalación local

```bash
git clone https://github.com/JssSalas/pida-rl-datos-publicos.git
cd pida-rl-datos-publicos
git switch feature/entorno-capacidad-v2
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Validación rápida

```bash
python -m compileall -q src dashboard_streamlit tests
python -m pytest -q
```

## Orden reproducible

1. Ejecutar los notebooks de datos 01–03 y conservar la cohorte procesada.
2. Ejecutar `05_politicas_base_capacidad_v2.ipynb`.
3. Entrenar Q-learning con el notebook 06.
4. Entrenar DQN con el notebook 07.
5. Entrenar PPO con el notebook 08.
6. Ejecutar la evaluación integral con el notebook 09.
7. Apuntar `PIDA_DASHBOARD_DATA_DIR` a la carpeta de CSV y abrir Streamlit.

```bash
export PIDA_DASHBOARD_DATA_DIR=/ruta/a/resultados_integrales
streamlit run dashboard_streamlit/app.py
```

## Parámetros mínimos por corrida

Cada ejecución debe registrar:

- SHA del commit y fecha.
- Versión de Python y dependencias.
- Fuente y huella de la cohorte.
- Semillas de entrenamiento y evaluación.
- Horizonte, capacidad mensual y costos de acciones.
- Hiperparámetros del algoritmo.
- Tiempo de entrenamiento.
- Ruta o huella del modelo guardado.

## Invariantes obligatorios

| Invariante | Criterio |
|---|---|
| Capacidad | `recursos_usados_mes <= capacidad_mensual` |
| Recursos | `recursos_restantes >= 0` |
| Acciones | Propuesta y ejecutada pertenecen a `{0,1,2,3}` |
| Riesgo | Solo `bajo`, `medio`, `alto` |
| Identificación | `FOLIO_INT` no se duplica en la cohorte base |
| Comparabilidad | Mismas semillas y configuración por política |
| Trazabilidad | Una decisión por perfil, mes, semilla y política |

## Repetición y tolerancia

Las políticas estocásticas deben repetirse con varias semillas. La reproducibilidad significa obtener el mismo resultado con la misma semilla, versión de código y dependencias; no implica que semillas diferentes deban producir valores idénticos.

Las comparaciones deben reportar media, desviación estándar y rango. No se seleccionará una política utilizando únicamente la mejor corrida.

## Evidencia de CI

El flujo `.github/workflows/ci.yml` se ejecuta en cada `push` a `main` o ramas `feature/**` y en cada `pull_request` hacia `main`. Comprueba instalación, sintaxis, importaciones críticas y pruebas para Python 3.10–3.12.

## Lista previa a fusión

- [ ] CI verde en todas las versiones de Python.
- [ ] Notebook 09 ejecutado de principio a fin con modelos reentrenados.
- [ ] Manifiesto y CSV conservan sus conteos y huella.
- [ ] Dashboard carga sin errores y muestra las seis políticas disponibles.
- [ ] No existe una cuarta categoría de riesgo.
- [ ] No se versionaron modelos, datos pesados, credenciales o información identificable.
- [ ] Limitaciones y supuestos revisados.
- [ ] Pull request revisado antes de fusionar.

## Recuperación

Para abandonar la rama sin alterar la versión estable:

```bash
git switch main
git pull origin main
```

Si un cambio ya fue fusionado, se debe crear un commit de reversión con `git revert`; no se reescribirá el historial compartido.
