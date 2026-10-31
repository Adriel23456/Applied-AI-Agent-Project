# Plan de Desarrollo

Notas de trabajo del equipo. No forma parte de la entrega.

Proyecto de IA Aplicada - Estimación de la probabilidad de victoria en el Pokémon TCG (Track A)
Inteligencia Artificial (IC-6200) - Instituto Tecnológico de Costa Rica

## Estado actual

| Etapa | Rama principal | Peso | Estado |
|---|---|---|---|
| Etapa 1 - Estado del arte y diseño | `stage1` | 30 % | Completa |
| Etapa 2 - Modelado y evaluación | `Stage2` | 45 % | En curso |
| Etapa 3 - Agente y artículo final | `stage3` | 25 % | No iniciada |

---

## Etapa 1 - Completa

### `00TrackConfirmation`

- [x] Track A y tema aprobados por el profesor
- [x] Repositorio operativo (licencia, `.gitignore`, `requirements.txt`, reglas de Git)
- [x] Compilación del artículo en IEEEtran
- [x] Corpus localizado y auditado (10 días, 52 085 partidas, 7 038 378 observaciones)
- [x] Formalización del problema y protocolo experimental

### `01LiteratureReview`

- [x] 21+ artículos revisados en los tres ejes
- [x] Tabla comparativa y apartado de brechas
- [x] Baseline de literatura declarado (AUC 0.78 a 0.80, AAIA'17 Hearthstone)
- [x] Pregunta de investigación, hipótesis H1 a H3 y objetivos
- [x] Prevención de fuga documentada

### `02PaperAndDelivery`

- [x] Artículo preliminar completo
- [x] Declaración de uso de IA
- [x] Entrega en TecDigital

### Pendientes heredados del artículo

- [ ] Poner la URL real del dataset en `ptcg_dataset_2026`

---

## Etapa 2 - En curso

Contexto obligatorio para trabajar: `docx/05AmbienteDeDesarrollo/DiccionarioDeDatos.md`
(sobre todo la sección 10, "Contrato para modelar").

### `03DataCollectionAndEnvironmentSetup` - Completa

- [x] Entorno en Colab reproducible (clon del repo, dependencias fijadas, semilla global, datos en dataset privado de Kaggle)
- [x] Credencial de Kaggle fuera del repositorio
- [x] Ingesta de los 10 días auditados hacia Parquet (55 196 partidas, 7 540 389 estados)
- [x] Extractor de características: una fila por estado del jugador que actúa, perspectiva propio/oponente
- [x] Filtro de campos excluidos por fuga y exclusión de estados ya resueltos
- [x] Tratamiento de ausencia estructural (indicador + centinela, sin imputar)
- [x] Exclusión de empates y marcado de partidas anómalas
- [x] EDA de la tabla y diccionario de datos final
- [x] Cortes de etapa calculados solo con entrenamiento (inicio ≤ 5, medio 6-9, final > 9)
- [x] Particiones de los escenarios A, B y C, agrupadas por partida
- [x] Auditoría y corrección de cobertura de cartas
- [x] Pruebas automáticas de los invariantes de fuga (24)
- [x] `load_scenario` para cargar X, y, partición y etapa en los cuadernos de modelado

### `04MainAIModelTrainingAndDevelopment`

La auditoría de cumplimiento de B0–B3 frente a la sección 10 y el estado de las etapas 04–06 está en `docx/03Evidence/29-10-26_AuditoriaBaselinesB0B3.md`. Cerrar B0–B3 no cierra la evaluación final en test ni los entregables del artículo.

Cuadernos: `02_baselines_B0_B1`, `03_baseline_B2`, `04_baseline_B3` y `05_baseline_B4`. Cada celda que entrena revisa primero sus archivos en el dataset privado de Kaggle: si existen los baja y no entrena; si faltan, entrena y publica (sin interruptores ni Google Drive). B2 y B3 no relanzan búsquedas cerradas. Código: `ptcg_wp.data` (carga y `ScenarioStream`), `ptcg_wp.b0_b1`, `b2`, `b3`, `b4` (escalera) y `ptcg_wp.experiments` (fuga, LightGBM, ablaciones y H2).
Escalera definida en el artículo (Tabla "Escalera de modelos de referencia"). Cada peldaño responde
una pregunta; **B4 es el modelo principal** (potenciación del gradiente, estado del arte en datos tabulares).

- [x] Registro de corridas en el dataset privado de Kaggle `adrielchavessalazar/ptcg-wp-tablas` (rutas `results/...` aplanadas e índice con SHA-256 y commit; ver `results/README.md` en el dataset) (escenario, modelo, configuración, semilla, métricas, duración estimada y trazabilidad de commits). B0/B1 tiene registro de corrida; B2/B3 se reanudaron durante varios commits: duración calendario aproximada de 4 y 3 días, respectivamente, según recuerdo del equipo. No hubo un único commit de entrenamiento ni se conservó tiempo exacto de cómputo; el registro histórico distingue ambos datos.
- [x] Funciones de evaluación comunes: AUC, log loss y Brier, globales y por etapa, con el número de estados y de partidas de cada etapa, cada partida con el mismo peso. Una sola implementación en `ptcg_wp.evaluation` (`metric_rows_codes`, con `metric_rows` para ids en texto y `evaluate_stream` para B2 por lotes) que usan B0–B4, LightGBM, ablaciones y H2. `tests/test_evaluation.py` la compara con scikit-learn (incluidos empates de probabilidad) y comprueba que B3 y B4 llaman a la misma función.
- [x] B0 - probabilidad a priori (prevalencia de train). Piso de referencia; métricas globales y por etapa para A/B/C en `results/b0_b1/`
- [x] B1 - heurística fija de recursos adoptada para esta rama y transformada a probabilidad usando train. Resultados y parámetros en `results/b0_b1/`; el ajuste original no registró convergencia. La decisión posterior queda documentada en `results/resumen/`.
- [x] B2 - regresión logística regularizada (`C=0.1`), ajustada con el `train` de A/B/C y artefactos recuperados en `results/b2/final/`. Se conserva la limitación de convergencia tras 600 épocas.
- [x] Demostración de fuga: B2 por fila contra partida en muestras de 200 juegos por escenario; resultados y solapamiento en `results/b2/demo_fuga/`. La división por fila compartió partidas en A/B/C; su AUC no fue mayor en B.
- [x] B3 - una configuración común de bosque seleccionada por macro-AUC de `val` entre configuraciones idénticas; ajustes con todo el `train` de cada escenario, métricas separadas y artefactos recuperados en `results/b3/final/`. El modelo único para la aplicación se decidirá al integrar el sistema.
- [x] B4 - modelo principal: `HistGradientBoostingClassifier` con búsqueda bayesiana de hiperparámetros (Optuna, TPE, 20 trials) y validación cruzada agrupada por `game_id` sobre las partidas train de A, B y C; parada temprana; reentrenado en cada escenario y medido en `val` (AUC A 0.835, B 0.786, C 0.836). Resultados y modelos en `results/b4/`
- [x] Verificación de implementación: LightGBM con presupuesto de 20 trials y 3 pliegues, una configuración seleccionada en CV y comparación por escenario frente a B4 (regla en `docx/03Evidence/28-10-26_ProtocoloLightGBM.md`). **No cumple la regla: se mantiene B4.** AUC `val` LightGBM/B4: A 0.8346/0.8346, B 0.7849/0.7863, C 0.8352/0.8355. En A y C el intervalo del 95 % de ΔAUC cruza 0; en B queda completo bajo 0 ([−0.0020, −0.0007]) con log loss y Brier mayores. Dos implementaciones independientes de boosting coinciden: el resultado de B4 no depende de la herramienta. Resultados en `results/lightgbm/`.
- [x] Ablaciones por familia de características sobre B4 (configuración del trial 20 fija; `val`, sin intervalos todavía). AUC sin la familia (B4 completo: A 0.8346, B 0.7863, C 0.8355): **recursos y tablero** A 0.7708, B 0.7398, C 0.7708 (caída de 0.05 a 0.06: es la familia esencial); **progreso** A 0.8323, B 0.7845, C 0.8335 (caída ≤ 0.003); **diferenciales** A 0.8361, B 0.7859, C 0.8360 (sin pérdida: son redundantes, el árbol las reconstruye desde los valores propios y del rival). No se cambia B4 por estas cifras: quitar diferenciales sería una selección hecha en `val`. Resultados en `results/b4/ablaciones/`.
- [x] Prueba de H2 en `val`: B4 con las 62 características públicas contra B4 restringido a `game_turn`, `first_player_is_me`, `own_active_card` y `opp_active_card`, con todas las categorías de `train` de los IDs (codificación por bloques sin pérdida, porque HistGradientBoosting admite 255 categorías por columna). AUC restringido/completo: A 0.7333/0.8346, B 0.6139/0.7863, C 0.7433/0.8355; log loss y Brier también peores en los tres. El modelo restringido **no iguala** al estado completo: en `val`, H2 no se refuta. La identidad aporta señal real (AUC 0.73–0.74) y es la que más se degrada en días posteriores (B). Pendiente para el veredicto: comparar por etapa (`inicio`), porque H2 habla de la señal temprana, y confirmarlo en `test`. Los IDs del Pokémon activo son una aproximación a la identidad del mazo, no el mazo completo. La variante de 64 características (estado completo más IDs) es una ablación distinta y no se ejecutó. Resultados en `results/b4/h2/`.
- [x] Evaluación de B0 a B4 en `val` en cada escenario (A, B y C), conservando sus particiones y reportando cada escenario por separado; los hiperparámetros comunes no implican mezclar los datos de `train`. AUC `val` B0/B1/B2/B3/B4: A 0.500/0.677/0.761/0.803/0.835, B 0.500/0.668/0.728/0.761/0.786, C 0.500/0.671/0.760/0.806/0.836. Cada peldaño supera al anterior en los tres escenarios.
- [x] Modelo final exportado, con una función que convierte una observación del juego en probabilidad (para la Etapa 3). Modelo: B4 ajustado con el `train` de A (población más amplia y reciente; B y C miden generalización). `ptcg_wp.predictor.PredictorVictoria` recibe `observation["current"]` del jugador que actúa y devuelve la probabilidad de que gane, con las mismas características y el mismo orden del entrenamiento (`features.extract_features`); en preparación y estados ya decididos devuelve `None`. Exportado en Kaggle como `results/modelo_final/` (`b4_victoria.joblib` y `ficha.json` con origen, SHA-256, versión de scikit-learn y métricas de `val`), sin reentrenar. Verificado: reproduce las métricas de `val` de B4 en A (celda 17 de `05_baseline_B4`) y `tests/test_predictor.py` comprueba que la observación da las mismas características que la tabla de entrenamiento. La calibración y la evaluación en `test` son de `05FinalModelChecks`.

### `05FinalModelChecks`

Cuaderno: `06_evaluacion_final`.

- [ ] Evaluación única sobre `test` en los escenarios A, B y C, reportados por separado
- [ ] Métricas globales y por etapa, con intervalos de confianza por remuestreo de partidas
- [ ] Comparación contra los tres puntos de referencia: B0 (trivial), B2 (razonable) y literatura (AUC 0.78-0.80)
- [ ] Curvas de aprendizaje (25 %, 50 %, 75 % y 100 % de las partidas de train) y diagnóstico de sobreajuste
- [ ] Análisis de errores: predicciones muy seguras y equivocadas, falsos positivos y negativos, por etapa
- [ ] SHAP sobre el modelo final, con hallazgos accionables y revisión de fuga (ninguna variable inesperada debe dominar)
- [ ] Calibración (módulo de grupo de 3): diagramas de fiabilidad y Brier antes y después; recalibración isotónica o de Platt ajustada solo con `calib`; en A y en B
- [ ] Prueba de H3: en el escenario B, comparar cuánto se degradan la calibración (log loss, Brier) y el ordenamiento (AUC)
- [ ] Veredicto sobre H1, H2 y H3
- [ ] README de reproducción, cuaderno final con salidas y declaración de uso de IA
- [ ] Entrega en TecDigital

### `06PendientesDelArticulo`

Las instrucciones exigen que al cerrar la Etapa 2 el artículo tenga escritas la metodología definitiva y los experimentos y resultados.

- [ ] Escribir la sección de metodología definitiva con lo implementado (datos, extractor, particiones, protocolo)
- [ ] Escribir la sección de experimentos y resultados con las salidas de `05FinalModelChecks`
- [ ] Actualizar la tabla del corpus: 55 196 partidas y 7 540 389 estados (no 52 085 y 7 038 378)
- [ ] Premios restantes: se cuentan por el largo de la lista, no "contando las ranuras no vacías" (todas son nulas)
- [ ] Número de turno: el diccionario lo pone a la vez en "Progreso" y en "Agrupación"; queda como característica (`game_turn`) y como meta (`turn`)
- [ ] Escenario B: el 17 jun queda fuera y la asignación es por días completos (train 18-25 jun, val 7 jul, calib 11 jul, test 15 y 22 jul)
- [ ] Escenario C: arquetipos reservados por Pokémon principal (33 principales, 15.1 % de partidas); mide arquetipos nuevos, no cartas nuevas
- [ ] Cobertura efectiva de cartas: A completa; B con cartas nuevas en 0.86-1.20 % de las filas; C en 0.061 % de las filas de test
- [ ] Ids de carta fuera del modelo principal; solo en la ablación de contexto de mazo (H2)
- [ ] "Gana el índice 0" sube porque quien empieza ocupa la posición 0 (0.764 → 1.000), no por la posición
- [ ] Casi ninguna partida termina por premios; se excluyen los estados ya resueltos (0.2 %) y la preparación
- [ ] Poner la URL real del dataset en `ptcg_dataset_2026`
- [ ] Revisar las entradas del Eje C marcadas como VERIFICAR
- [ ] Corregir erratas menores de la Introducción

---

## Etapa 3 - No iniciada

Se detalla al cerrar la Etapa 2.

- [ ] Agente que consume el modelo como evaluador de posiciones de forma verificable
- [ ] Ética del despliegue
- [ ] Artículo final con los resultados de la Etapa 2
- [ ] Demostración funcional