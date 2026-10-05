# Cumplimiento de la Definición del PIDA (V2.16.0)

Este documento contrasta el estado del proyecto con la Definición del PIDA (versión corregida): MDP restringido, datos, objetivos, criterios de éxito, diccionario de datos y alcance.

La evidencia proviene de la ejecución completa (`PIDA_MODO_PRUEBA=0`, cohorte de 1 542 perfiles, capacidad 100, costos 0/1/3/5) de los notebooks corregidos 03 y 05–10, con el entorno V2.16: orden de atención barajado cada mes y descuento mensual en los tres agentes. Las tablas se publican en `dashboard_data/v2/` y en la sección «Criterios PIDA» del dashboard.

Alcance: todos los resultados comparan políticas dentro de un simulador construido con supuestos explícitos. Son conclusiones metodológicas, no clínicas. No demuestran efectividad clínica, causalidad ni equidad clínica.

## 1. Criterios de éxito (sección 5)

| Dimensión | Umbral PIDA | Resultado | Estado |
|---|---|---|---|
| Validez técnica | 100 % de pruebas aprobadas | 58 de 58 pruebas aprobadas, incluido `check_env` de Gymnasium | Cumple |
| Factibilidad operativa | Cero violaciones de capacidad | 0 en 1 440 episodios (600 base y 840 de robustez) y 150 de sensibilidad | Cumple |
| Comparación | ≥ 3 políticas | 6: Aleatoria, Reglas simples, Reglas escalonadas, Q-learning, DQN y PPO | Cumple |
| Rendimiento | Recompensa media con IC95, n ≥ 100, frente a la mejor referencia | DQN −17 827 [−17 862; −17 793] frente a Reglas simples −18 552 [−18 586; −18 519]; n = 100; IC disjuntos | Cumple |
| Rendimiento aspiracional | ≥ 10 % sobre la mejor regla | +3.9 % | No cumple; se documenta en la sección 2 |
| Prioridad clínica simulada | Cobertura de riesgo alto no inferior a la política por reglas | 8.07 % (DQN) frente a 4.24 % | Cumple |
| Robustez | Resultados en todos los escenarios; mejora en ≥ 80 % (meta) | 7 escenarios: capacidad ×0.5 y ×1.5, costos 0/1/2/3 y 0/1/4/7, riesgo basal ×0.75 y ×1.25, efecto del contacto ×0.5. DQN mejora a la mejor regla en 7 de 7 (+1.8 % a +6.2 %) | Cumple |
| Equidad operativa | Brecha reportada; meta ≤ 10 pp | Brecha máxima entre políticas: sexo 1.44 pp, edad 2.20 pp, entidad federativa 3.00 pp (32 entidades) | Cumple |
| Reproducibilidad | Ejecutable desde cero en Colab | Bootstrap `PROJECT_ROOT`, semillas fijas, manifiesto y huellas de configuración. Ejecución completa local de 03 y 05–10: unos 62 minutos | Pendiente de confirmar en Colab |

Resumen: 7 cumple, 1 no cumple (meta aspiracional) y 1 pendiente de confirmar en Colab.

Recompensa media en el escenario base (100 episodios, semillas 5000–5099):

| Política | Recompensa [IC95] | Cobertura de riesgo alto |
|---|---|---|
| DQN | −17 827 [−17 862; −17 793] | 8.07 % |
| Reglas simples | −18 552 [−18 586; −18 519] | 4.24 % |
| Reglas escalonadas | −18 897 [−18 931; −18 862] | 3.09 % |
| Q-learning | −18 943 [−18 977; −18 909] | 5.03 % |
| Aleatoria | −19 267 [−19 302; −19 232] | 2.20 % |
| PPO | −19 550 [−19 585; −19 514] | 1.28 % |

Notas sobre la medición:
- Los IC95 son de aproximación normal y de bootstrap percentil con 5 000 remuestreos (`src/evaluation/pida.py`). Ambos coinciden.
- Los agentes se entrenan solo en el escenario base. La robustez mide la transferencia de una política fija a condiciones distintas.
- La brecha es el máximo menos el mínimo de la cobertura (contactos ejecutados / decisiones), agregada sobre los episodios. Los grupos de edad usan los mismos cortes que `integral.py` (≤ 44, 45–64, ≥ 65). Las entidades tienen entre 17 y 193 perfiles.
- El mejor agente cambió de Q-learning (V2.15) a DQN. Q-learning y PPO siguen por debajo de Reglas simples.

## 2. Meta aspiracional y sensibilidad

### 2.1 Qué cambió en V2.16 y por qué

La evaluación V2.15 encontró dos fallas de diseño. Ambas correcciones se fijaron antes de ver los resultados y las metas no se ajustaron:

1. **Descuento.** El entorno aplica una decisión por perfil (1 542 por mes y 18 504 por episodio), y γ se aplicaba en cada decisión. La Definición del PIDA define el retorno como Σ γ^t r_t con t = mes. Ahora los agentes usan `descuento="mensual"`: factor 1 entre decisiones del mismo mes y γ = 0.95 al cerrar el mes (`info["fin_mes"]`).
2. **Orden de atención.** El entorno recorría la cohorte en el orden del archivo, agrupado por entidad. La capacidad se agotaba siempre en las primeras entidades y la brecha territorial llegaba a 60–75 pp en todas las políticas (cobertura mínima de 0 %). Ahora el orden se baraja al inicio de cada mes con un generador propio (`semilla + 2`), sin alterar el flujo aleatorio de eventos. La brecha territorial bajó a 0.3–3.0 pp.

### 2.2 El problema sí tiene margen de mejora

La regla diagnóstica «riesgo alto → acción 1 y el resto → 0» obtiene −16 592 [−16 652; −16 531] en 30 episodios comunes: +10.4 % sobre Reglas simples, con 16.3 % de cobertura de riesgo alto. No forma parte del conjunto de referencias del PIDA; solo mide si el margen existe.

La explicación es aritmética. Contactar a una persona de riesgo alto con la acción 1 cuesta 1 unidad y aporta unos 3 puntos por unidad. La acción 2 (Reglas simples) aporta 1.5 puntos por unidad.

### 2.3 Sensibilidad del descuento (Q-learning, 400 episodios, 30 de evaluación)

| Política | Recompensa media [IC95] | Cobertura de riesgo alto | Frente a Reglas simples |
|---|---|---|---|
| Reglas simples | −18 513 [−18 573; −18 453] | 4.24 % | — |
| Q-learning, mensual, γ = 0.95 | −19 173 [−19 236; −19 111] | 4.06 % | −3.6 % |
| Q-learning, por decisión, γ = 0.95 | −18 983 [−19 048; −18 919] | 3.12 % | −2.5 % |
| Q-learning, por decisión, γ = 0.9995 | −19 051 [−19 113; −18 990] | 4.22 % | −2.9 % |
| Diagnóstica: alto → 1 | −16 592 [−16 652; −16 531] | 16.34 % | +10.4 % |

Lectura honesta:
- Con el orden aleatorio, Q-learning tabular no supera a la regla con ningún descuento. Una explicación probable es que la discretización del estado no distingue lo suficiente entre perfiles; no se verificó.
- En V2.15, con orden fijo, γ = 0.9995 daba +1.4 %. Esa ventaja dependía del orden fijo y desaparece al barajarlo.
- DQN, con red neuronal y descuento mensual, sí supera a la regla (+3.9 %), pero queda lejos de la regla diagnóstica (+10.4 %).
- No hay una ablación que separe el efecto del descuento mensual del efecto del orden aleatorio en DQN. Ambos cambios se evalúan juntos.

### 2.4 Siguiente paso sugerido

Entrenar DQN más tiempo (100 000 pasos equivalen a unos 5.4 episodios) y probar PPO con más pasos, manteniendo las metas. Esto queda fuera del alcance de esta entrega.

## 3. MDP restringido (sección 2)

| Elemento PIDA | Implementación V2 | Estado |
|---|---|---|
| Estado: riesgo, score, variables clínicas y demográficas, meses sin contacto, mes, fracción de recursos | Observación de 13 componentes en [0, 1]: edad, sexo, años con diabetes, insulina, depresión, consultas, hospitalizaciones, complicaciones, score, riesgo, meses sin contacto, mes y fracción de recursos restantes | Cumple |
| Acciones 0–3, donde 3 es teleorientación | `Discrete(4)`; 3 = teleorientación. Solo hay tres categorías de riesgo, validadas en el entorno y en el dashboard | Cumple |
| Costo c(a) configurable | `costos_accion`, por defecto 0/1/3/5; se validan no negativos y no decrecientes | Cumple |
| Restricción ∑c ≤ C por mes | Ajuste a la acción más intensa pagable (`_resolver_accion`); 0 violaciones | Cumple |
| T = 12, γ configurable | T = 12 meses; γ = 0.95 aplicado por mes (`descuento="mensual"`) desde V2.16 | Cumple |
| Transición con eventos adversos | Probabilidad paramétrica (riesgo, complicaciones, hospitalización, meses sin contacto) con reducción por acción | Supuesto no calibrado (L4) |

## 4. Diccionario de datos (sección 6): verificación

La verificación se hace en la sección 11 del notebook 10 (`verificacion_diccionario.csv`). Desde V2.16 la cohorte incluye `entidad` (columna real de ENSANUT), que se usa solo para medir equidad; no entra al estado.

| Variable PIDA | Situación en la cohorte | Disponibilidad en ENSANUT 2022 (archivos del proyecto) |
|---|---|---|
| id_persona (hash) | `FOLIO_INT`, el folio público de ENSANUT. No entra al estado ni al dashboard. No está hasheado | Hashearlo es trivial si el comité lo exige |
| edad ≥ 20 | `edad`, mínimo 21 | Adultos |
| sexo | `sexo` (1/2) | Adultos |
| entidad_federativa | `entidad` (1–32), solo para equidad | Adultos: `entidad`, 100 % de cobertura |
| diabetes_diagnosticada | Criterio de inclusión `a0301 = 1` | Adultos |
| glucosa | No incluida | No está en los archivos descargados. `Muestras_Sangre_ENSANUT_2022.sav` solo contiene serología (proteínas N y S en papel filtro). Requiere la base de laboratorio de ENSANUT |
| imc | No incluida | `Antro_Tension`: peso `an01_1` y talla `an04_1`, válidos para 568 de 1 542 perfiles (36.8 %, submuestra antropométrica) |
| comorbilidades | Complicaciones (pie, visual, renal, macrovascular), evento agudo y depresión | La hipertensión diagnosticada (`a0401`) está disponible al 100 %, pero no está incluida |
| score_riesgo, nivel_riesgo | `score_riesgo`, `categoria_riesgo` (bajo, medio, alto) | Derivadas |
| meses_sin_contacto, mes, recursos_restantes | Estado del entorno | Derivadas |
| accion, costo_accion, recompensa, evento_adverso | `info` de cada paso y tablas de evaluación | Derivadas |

Extensión propuesta, que requiere reentrenar: incorporar `entidad` al estado, `a0401` (hipertensión) y, si se acepta la pérdida de cobertura o una imputación documentada, el IMC.

## 5. Datos y contexto (secciones 3 y 7)

- Prevalencia de diabetes ENSANUT 2022: 18.3 % en total (12.6 % diagnosticada y 5.8 % no diagnosticada), en adultos ≥ 20 años; prediabetes 22.1 %. El 18.3 % queda verificado. Fuentes: [Basto-Abreu et al., Salud Pública de México 2023](https://www.saludpublica.mx/index.php/spm/article/view/14832), [PubMed 38060942](https://pubmed.ncbi.nlm.nih.gov/38060942/) y el [PDF en ensanut.insp.mx](https://ensanut.insp.mx/encuestas/ensanutcontinua2022/doctos/analiticos/21-Diabetes-ENSANUT2022-14832-72458-2-10-20230619.pdf).
- Contraste interno: la cohorte (diagnóstico previo) es 1 542 de 11 913 adultos, un 12.9 % sin ponderar. Es coherente con el 12.6 % ponderado, pero no comparable en sentido estricto porque no usa factores de expansión.
- Mortalidad: INEGI registró 110 059 defunciones por diabetes mellitus en 2023 ([EDR 2023, INEGI](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2024/EDR/EDR2023_Dtivas.pdf)). En enero–septiembre de 2024, la diabetes estuvo entre las tres primeras causas ([EDR ene–sep 2024, INEGI](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/edr/EDR_En-sep2024.pdf)). Este dato se usa solo como contexto; el código no lo consume.

## 6. Limitaciones

- L1. Sin glucosa ni IMC completo en el estado; la entidad se usa solo para medir equidad (sección 4).
- L2. La transición no está calibrada con INEGI. La probabilidad mensual de evento simulada (unos 1 200 eventos por año en 1 542 perfiles) representa «eventos adversos» genéricos, no defunciones. El análisis de sensibilidad (riesgo basal ×0.75 y ×1.25, efecto del contacto ×0.5) no cambia la conclusión comparativa.
- L3. Las referencias y la regla diagnóstica son supuestos operativos del simulador, no protocolos clínicos.
- L4. DQN y PPO se entrenan con 100 000 pasos y una sola semilla de entrenamiento.
- Resueltas en V2.16: descuento por decisión (antes L2) y orden fijo de atención (antes L3).

## 7. Cambios técnicos

### 7.1 V2.16.0

- `DiabetesFollowUpEnv(orden_aleatorio=True)`: orden barajado por mes con `default_rng(seed + 2)`; `info["fin_mes"]` e `info["posicion_en_mes"]`; `VERSION = "2.16"` entra en la huella de la caché del notebook 10.
- `factor_descuento` en `src/policies/q_learning.py`; `descuento="mensual"` en Q-learning, DQN (descuento por transición en el replay buffer) y PPO (γ por transición en GAE). Los modelos guardan el modo de descuento; los NPZ antiguos se cargan como `"decision"`.
- Notebook 03: la cohorte conserva `entidad`. `pida.grupos_por_perfil` añade la dimensión `entidad_federativa`, y el criterio de equidad la incluye.
- Notebooks corregidos y de despliegue: la rama por defecto es `main`.
- 10 pruebas nuevas (`tests/test_orden_y_descuento.py` y `tests/test_pida.py`).

### 7.2 Cambios técnicos de V2.14.0

- `src/evaluation/pida.py`: evaluación episódica ligera, IC95, escenarios de robustez, brechas, tabla de criterios y caché con huella de configuración.
- `EntornoSensibilidadTransicion`: con factores 1.0 reproduce exactamente el entorno V2 (prueba automática).
- El entorno V2 lee la cohorte mediante arreglos NumPy en lugar de `iloc`, y los recortes escalares usan `min`/`max` en lugar de `np.clip`.
  - Se verificó que las trayectorias son idénticas paso a paso: observaciones, recompensas, `info` y tabla Q.
  - La velocidad aumentó entre 5 y 12 veces: Q-learning con 1 500 episodios pasó de no terminar en 3 h 40 min (937 episodios) a 20 min localmente.
  - Esto hace viable ejecutar el flujo completo en una sesión de Colab.
- Dashboard V2: nueva sección «Criterios PIDA». `dashboard_data/v2/` contiene las tablas agregadas de la ejecución completa, sin `detalle.csv`.
