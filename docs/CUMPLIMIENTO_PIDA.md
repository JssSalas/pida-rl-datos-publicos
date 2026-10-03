# Cumplimiento de la Definición del PIDA (V2.14.0)

Este documento contrasta el estado del proyecto con la Definición del PIDA (versión corregida): MDP restringido, datos, objetivos, criterios de éxito, diccionario de datos y alcance.

La evidencia proviene de la ejecución completa (`PIDA_MODO_PRUEBA=0`, cohorte de 1 542 perfiles, capacidad 100, costos 0/1/3/5) de los notebooks corregidos 05–10. El notebook nuevo es `notebooks/corregidos/10_cumplimiento_pida_v2.ipynb`. Sus tablas se publican en `dashboard_data/v2/` y en la sección «Criterios PIDA» del dashboard.

Alcance: todos los resultados comparan políticas dentro de un simulador construido con supuestos explícitos. Son conclusiones metodológicas, no clínicas. No demuestran efectividad clínica, causalidad ni equidad clínica.

## 1. Criterios de éxito (sección 5)

| Dimensión | Umbral PIDA | Resultado | Estado |
|---|---|---|---|
| Validez técnica | 100 % de pruebas aprobadas | 48 de 48 pruebas aprobadas, incluido `check_env` de Gymnasium | Cumple |
| Factibilidad operativa | Cero violaciones de capacidad | 0 en 600 episodios base, 840 de robustez y 150 de sensibilidad | Cumple |
| Comparación | ≥ 3 políticas | 6: Aleatoria, Reglas simples, Reglas escalonadas, Q-learning, DQN y PPO | Cumple |
| Rendimiento | Recompensa media con IC95, n ≥ 100, frente a la mejor referencia | Q-learning −19 097 [−19 133; −19 061] frente a Reglas simples −18 708 [−18 744; −18 672]; n = 100; IC disjuntos | Cumple (reportado), con el RL por debajo |
| Rendimiento aspiracional | ≥ 10 % sobre la mejor regla | −2.1 % | No cumple; la causa se documenta en la sección 2 |
| Prioridad clínica simulada | Cobertura de riesgo alto no inferior a la política por reglas | 3.50 % (Q-learning) frente a 4.90 % | No cumple con γ = 0.95; cumple con γ = 0.9995 (6.66 %, sección 2) |
| Robustez | Resultados en todos los escenarios; mejora en ≥ 80 % (meta) | 7 escenarios: capacidad ×0.5 y ×1.5, costos 0/1/2/3 y 0/1/4/7, riesgo basal ×0.75 y ×1.25, efecto del contacto ×0.5. El RL mejora en 0 de 7 | Reportado en todos; meta no alcanzada |
| Equidad operativa | Brecha reportada; meta ≤ 10 pp | Brecha máxima entre políticas de 1.42 pp (edad) y 0.72 pp (sexo) | Cumple |
| Reproducibilidad | Ejecutable desde cero en Colab | Bootstrap `PROJECT_ROOT`, semillas fijas, manifiesto y huellas de configuración. Ejecución completa local: 05–09 en 22 minutos; el notebook 10 añade unos 30 minutos | Pendiente de confirmar en Colab |

Notas sobre la medición:
- Los IC95 son de aproximación normal y de bootstrap percentil con 5 000 remuestreos (`src/evaluation/pida.py`). Ambos coinciden.
- La cobertura de riesgo alto tiene IC de ancho casi nulo porque el orden de la cohorte es fijo y la capacidad se agota siempre en los mismos perfiles. Ver la limitación L3.
- Los agentes se entrenan solo en el escenario base. La robustez mide, por tanto, la transferencia de una política fija a condiciones distintas.
- La brecha es el máximo menos el mínimo de la cobertura (contactos ejecutados / decisiones), agregada sobre los episodios. Los grupos de edad usan los mismos cortes que `integral.py` (≤ 44, 45–64, ≥ 65). La edad mínima observada es 21, aunque la etiqueta del primer grupo sea «18-44».

## 2. Por qué el RL no supera a las reglas (sensibilidad)

La sección 5 pide documentar la causa si no se alcanza la meta aspiracional. Las secciones 7 y 12 del notebook 10 y dos experimentos complementarios dan tres hallazgos.

### 2.1 El problema sí tiene margen de mejora

Una regla diagnóstica, «riesgo alto → acción 1 y el resto → 0», obtiene −16 805 [−16 875; −16 735] en 30 episodios comunes. Eso es +10.1 % sobre Reglas simples, con una cobertura de riesgo alto del 16.3 %.

Esta regla no forma parte del conjunto de referencias del PIDA. Se añadió después de ver los resultados y solo sirve para medir si el margen existe.

La explicación es aritmética:
- Contactar a una persona de riesgo alto con la acción 1 cuesta 1 unidad. Da +1.5 de bono y evita −1.5 de penalización: 3 puntos por unidad.
- La acción 2 en riesgo alto (Reglas simples) da 4.5 puntos por 3 unidades: 1.5 por unidad.

### 2.2 El descuento por decisión impide que el agente lo encuentre

El entorno V2 aplica γ en cada decisión: 1 542 por mes y 18 504 por episodio. Con γ = 0.95, una recompensa 100 decisiones más adelante pesa 0.95¹⁰⁰ ≈ 0.006. El agente no percibe el costo de oportunidad de gastar la capacidad en los primeros perfiles del mes.

La Definición del PIDA plantea T = 12 meses con γ configurable, es decir, un descuento a escala mensual. Este es un desajuste de formulación entre el código y el PIDA.

Q-learning con 400 episodios y 30 episodios de evaluación comunes (sección 12 del notebook 10):

| Política | Recompensa media [IC95] | Cobertura de riesgo alto | Frente a Reglas simples |
|---|---|---|---|
| Reglas simples | −18 690 [−18 760; −18 621] | 4.90 % | — |
| Q-learning, γ = 0.95 | −19 217 [−19 285; −19 148] | 2.94 % | −2.8 % |
| Q-learning, γ = 0.9995 | −18 437 [−18 509; −18 366] | 6.66 % | +1.4 % |
| Q-learning, γ = 1.0 | −19 072 [−19 147; −18 998] | 4.52 % | −2.0 % |
| Diagnóstica: alto → 1 | −16 805 [−16 875; −16 735] | 16.34 % | +10.1 % |

Con γ = 0.9995, el agente supera a la mejor regla con IC disjuntos y cumple el criterio de cobertura de riesgo alto. Aun así, queda lejos del margen disponible.

### 2.3 Más entrenamiento sin corregir γ no basta

En el notebook 07, DQN se entrena con 100 000 pasos, unos 5.4 episodios. Para descartar que el problema fuera solo de entrenamiento, DQN y PPO se reentrenaron con 1 000 000 de pasos (unos 54 episodios) y γ = 0.95. El script `build/experimento_entrenamiento.py` está en el ZIP de entrega, no en el repositorio.

Resultados en 30 episodios: DQN −19 197 y PPO −19 157, ambos por debajo de Reglas simples (−18 690).

### Recomendación (decisión del equipo)

Hay dos opciones:
- Aplicar el descuento por mes, con γ_paso = 1 dentro del mes y γ_mes configurable.
- Usar γ ≥ 0.9995 por paso, reentrenar Q-learning, DQN y PPO, y repetir el notebook 10.

Cambiar el γ por defecto modifica el MDP formulado, así que no se aplicó sin aprobación. Las metas del PIDA no se ajustan después de ver los resultados.

## 3. MDP restringido (sección 2)

| Elemento PIDA | Implementación V2 | Estado |
|---|---|---|
| Estado: riesgo, score, variables clínicas y demográficas, meses sin contacto, mes, fracción de recursos | Observación de 13 componentes en [0, 1]: edad, sexo, años con diabetes, insulina, depresión, consultas, hospitalizaciones, complicaciones, score, riesgo, meses sin contacto, mes y fracción de recursos restantes | Cumple |
| Acciones 0–3, donde 3 es teleorientación | `Discrete(4)`; 3 = teleorientación. Solo hay tres categorías de riesgo, validadas en el entorno y en el dashboard | Cumple |
| Costo c(a) configurable | `costos_accion`, por defecto 0/1/3/5; se validan no negativos y no decrecientes | Cumple |
| Restricción ∑c ≤ C por mes | Ajuste a la acción más intensa pagable (`_resolver_accion`); 0 violaciones | Cumple |
| T = 12, γ configurable | T = 12 meses; γ configurable, pero aplicado por decisión y no por mes | Desajuste, ver 2.2 |
| Transición con eventos adversos | Probabilidad paramétrica (riesgo, complicaciones, hospitalización, meses sin contacto) con reducción por acción | Supuesto no calibrado (L4) |

## 4. Diccionario de datos (sección 6): verificación

La verificación se hace en la sección 11 del notebook 10 (`verificacion_diccionario.csv`). No se añadió ninguna columna a la cohorte.

| Variable PIDA | Situación en la cohorte | Disponibilidad en ENSANUT 2022 (archivos del proyecto) |
|---|---|---|
| id_persona (hash) | `FOLIO_INT`, el folio público de ENSANUT. No entra al estado ni al dashboard. No está hasheado | Hashearlo es trivial si el comité lo exige |
| edad ≥ 20 | `edad`, mínimo 21 | Adultos |
| sexo | `sexo` (1/2) | Adultos |
| entidad_federativa | No incluida | Adultos: `entidad`, 100 % de cobertura |
| diabetes_diagnosticada | Criterio de inclusión `a0301 = 1` | Adultos |
| glucosa | No incluida | No está en los archivos descargados. `Muestras_Sangre_ENSANUT_2022.sav` solo contiene serología (proteínas N y S en papel filtro). Requiere la base de laboratorio de ENSANUT |
| imc | No incluida | `Antro_Tension`: peso `an01_1` y talla `an04_1`, válidos para 568 de 1 542 perfiles (36.8 %, submuestra antropométrica) |
| comorbilidades | Complicaciones (pie, visual, renal, macrovascular), evento agudo y depresión | La hipertensión diagnosticada (`a0401`) está disponible al 100 %, pero no está incluida |
| score_riesgo, nivel_riesgo | `score_riesgo`, `categoria_riesgo` (bajo, medio, alto) | Derivadas |
| meses_sin_contacto, mes, recursos_restantes | Estado del entorno | Derivadas |
| accion, costo_accion, recompensa, evento_adverso | `info` de cada paso y tablas de evaluación | Derivadas |

Extensión propuesta, que requiere reentrenar: incorporar `entidad`, `a0401` (hipertensión) y, si se acepta la pérdida de cobertura o una imputación documentada, el IMC.

## 5. Datos y contexto (secciones 3 y 7)

- Prevalencia de diabetes ENSANUT 2022: 18.3 % en total (12.6 % diagnosticada y 5.8 % no diagnosticada), en adultos ≥ 20 años; prediabetes 22.1 %. El 18.3 % queda verificado. Fuentes: [Basto-Abreu et al., Salud Pública de México 2023](https://www.saludpublica.mx/index.php/spm/article/view/14832), [PubMed 38060942](https://pubmed.ncbi.nlm.nih.gov/38060942/) y el [PDF en ensanut.insp.mx](https://ensanut.insp.mx/encuestas/ensanutcontinua2022/doctos/analiticos/21-Diabetes-ENSANUT2022-14832-72458-2-10-20230619.pdf).
- Contraste interno: la cohorte (diagnóstico previo) es 1 542 de 11 913 adultos, un 12.9 % sin ponderar. Es coherente con el 12.6 % ponderado, pero no comparable en sentido estricto porque no usa factores de expansión.
- Mortalidad: INEGI registró 110 059 defunciones por diabetes mellitus en 2023 ([EDR 2023, INEGI](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2024/EDR/EDR2023_Dtivas.pdf)). En enero–septiembre de 2024, la diabetes estuvo entre las tres primeras causas ([EDR ene–sep 2024, INEGI](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/edr/EDR_En-sep2024.pdf)). Este dato se usa solo como contexto; el código no lo consume.

## 6. Limitaciones

- L1. Sin glucosa, IMC completo ni entidad en el estado (sección 4).
- L2. Desajuste de γ por decisión frente al descuento mensual (sección 2.2).
- L3. Orden fijo de presentación de perfiles. Con C = 100 y 1 542 perfiles hay 0.065 unidades por persona al mes, y las políticas por reglas agotan la capacidad en los primeros perfiles de la cohorte. La cobertura depende del orden, lo que reduce la varianza entre semillas.
- L4. La transición no está calibrada con INEGI. La probabilidad mensual de evento simulada (unos 1 216 eventos por año en 1 542 perfiles) representa «eventos adversos» genéricos, no defunciones. El análisis de sensibilidad (riesgo basal ×0.75 y ×1.25, efecto del contacto ×0.5) muestra que la conclusión comparativa no cambia.
- L5. Las referencias y la regla diagnóstica son supuestos operativos del simulador, no protocolos clínicos.

## 7. Cambios técnicos de V2.14.0

- `src/evaluation/pida.py`: evaluación episódica ligera, IC95, escenarios de robustez, brechas, tabla de criterios y caché con huella de configuración.
- `EntornoSensibilidadTransicion`: con factores 1.0 reproduce exactamente el entorno V2 (prueba automática).
- El entorno V2 lee la cohorte mediante arreglos NumPy en lugar de `iloc`, y los recortes escalares usan `min`/`max` en lugar de `np.clip`.
  - Se verificó que las trayectorias son idénticas paso a paso: observaciones, recompensas, `info` y tabla Q.
  - La velocidad aumentó entre 5 y 12 veces: Q-learning con 1 500 episodios pasó de no terminar en 3 h 40 min (937 episodios) a 20 min localmente.
  - Esto hace viable ejecutar el flujo completo en una sesión de Colab.
- Dashboard V2: nueva sección «Criterios PIDA». `dashboard_data/v2/` contiene las tablas agregadas de la ejecución completa, sin `detalle.csv`.
