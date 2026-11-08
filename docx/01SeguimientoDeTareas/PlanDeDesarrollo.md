# Plan de Desarrollo

Notas de trabajo del equipo. No forma parte de la entrega.

Proyecto de IA Aplicada - Estimación de la probabilidad de victoria en el Pokémon TCG (Track A)
Inteligencia Artificial (IC-6200) - Instituto Tecnológico de Costa Rica

## Estado actual

| Etapa | Rama principal | Peso | Estado |
|---|---|---|---|
| Etapa 1 - Estado del arte y diseño | `Stage1` | 30 % | Completa (`v1.0.0`, `v1.0.1`) |
| Etapa 2 - Modelado y evaluación | `Stage2` | 45 % | Completa (`v2.0.0`) |
| Etapa 3 - Agente y artículo final | `Stage3` | 25 % | En curso |

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

- [x] Poner la URL real del dataset en `ptcg_dataset_2026`

---

## Etapa 2 - Completa

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

### `04MainAIModelTrainingAndDevelopment` - Completa

La auditoría de cumplimiento de B0–B3 frente a la sección 10 y el estado de las etapas 04–06 está en `docx/03Evidencia/29-10-26_AuditoriaBaselinesB0B3.md`. Cerrar B0–B3 no cierra la evaluación final en test ni los entregables del artículo.

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
- [x] Verificación de implementación: LightGBM con presupuesto de 20 trials y 3 pliegues, una configuración seleccionada en CV y comparación por escenario frente a B4 (regla en `docx/03Evidencia/28-10-26_ProtocoloLightGBM.md`). **No cumple la regla: se mantiene B4.** AUC `val` LightGBM/B4: A 0.8346/0.8346, B 0.7849/0.7863, C 0.8352/0.8355. En A y C el intervalo del 95 % de ΔAUC cruza 0; en B queda completo bajo 0 ([−0.0020, −0.0007]) con log loss y Brier mayores. Dos implementaciones independientes de boosting coinciden: el resultado de B4 no depende de la herramienta. Resultados en `results/lightgbm/`.
- [x] Ablaciones por familia de características sobre B4 (configuración del trial 20 fija; `val`, sin intervalos todavía). AUC sin la familia (B4 completo: A 0.8346, B 0.7863, C 0.8355): **recursos y tablero** A 0.7708, B 0.7398, C 0.7708 (caída de 0.05 a 0.06: es la familia esencial); **progreso** A 0.8323, B 0.7845, C 0.8335 (caída ≤ 0.003); **diferenciales** A 0.8361, B 0.7859, C 0.8360 (sin pérdida: son redundantes, el árbol las reconstruye desde los valores propios y del rival). No se cambia B4 por estas cifras: quitar diferenciales sería una selección hecha en `val`. Resultados en `results/b4/ablaciones/`.
- [x] Prueba de H2 en `val`: B4 con las 62 características públicas contra B4 restringido a `game_turn`, `first_player_is_me`, `own_active_card` y `opp_active_card`, con todas las categorías de `train` de los IDs (codificación por bloques sin pérdida, porque HistGradientBoosting admite 255 categorías por columna). AUC restringido/completo: A 0.7333/0.8346, B 0.6139/0.7863, C 0.7433/0.8355; log loss y Brier también peores en los tres. El modelo restringido **no iguala** al estado completo: en `val`, H2 no se refuta. La identidad aporta señal real (AUC 0.73–0.74) y es la que más se degrada en días posteriores (B). Pendiente para el veredicto: comparar por etapa (`inicio`), porque H2 habla de la señal temprana, y confirmarlo en `test`. Los IDs del Pokémon activo son una aproximación a la identidad del mazo, no el mazo completo. La variante de 64 características (estado completo más IDs) es una ablación distinta y no se ejecutó. Resultados en `results/b4/h2/`.
- [x] Evaluación de B0 a B4 en `val` en cada escenario (A, B y C), conservando sus particiones y reportando cada escenario por separado; los hiperparámetros comunes no implican mezclar los datos de `train`. AUC `val` B0/B1/B2/B3/B4: A 0.500/0.677/0.761/0.803/0.835, B 0.500/0.668/0.728/0.761/0.786, C 0.500/0.671/0.760/0.806/0.836. Cada peldaño supera al anterior en los tres escenarios.
- [x] Modelo final exportado, con una función que convierte una observación del juego en probabilidad (para la Etapa 3). Modelo: B4 ajustado con el `train` de A (población más amplia y reciente; B y C miden generalización). `ptcg_wp.predictor.PredictorVictoria` recibe `observation["current"]` del jugador que actúa y devuelve la probabilidad de que gane, con las mismas características y el mismo orden del entrenamiento (`features.extract_features`); en preparación y estados ya decididos devuelve `None`. Exportado en Kaggle como `results/modelo_final/` (`b4_victoria.joblib` y `ficha.json` con origen, SHA-256, versión de scikit-learn y métricas de `val`), sin reentrenar. Verificado: reproduce las métricas de `val` de B4 en A (celda 17 de `05_baseline_B4`) y `tests/test_predictor.py` comprueba que la observación da las mismas características que la tabla de entrenamiento. La calibración y la evaluación en `test` son de `05FinalModelChecks`.

### `05FinalModelChecks` - Completa

Cuaderno: `06_evaluacion_final`. Protocolo: `docx/03Evidencia/02-11-26_ProtocoloEvaluacionFinal.md`. Diagnóstico: `docx/03Evidencia/02-11-26_DiagnosticoFinalModelChecks.md`. Resultados e interpretación: `docx/03Evidencia/04-11-26_ResultadosEvaluacionFinal.md`.

Ejecutado en Colab (CPU + RAM alta) el 2 y 3 de noviembre de 2026, con el protocolo congelado antes de abrir `test`. Antes de `test` pasaron las barreras del cuaderno: 109 pruebas, reproducción exacta de las métricas de `val` publicadas (log loss y Brier ≤ 4.4e-16, AUC ≤ 4.8e-7) y revisión de fuga aprobada. Los 51 archivos de resultados están en el dataset de Kaggle bajo `evaluacion_final/`, verificados con SHA-256. Intervalos: percentil 95 % con 1000 remuestreos de partidas, individuales por escenario.

- [x] Evaluación única sobre `test` en los escenarios A, B y C, reportados por separado. AUC de B4: A 0.833 [0.827, 0.838], B 0.789 [0.784, 0.795], C 0.787 [0.782, 0.793]; log loss 0.494, 0.551 y 0.550; Brier 0.166, 0.188 y 0.188. En C el AUC baja de 0.836 en `val` a 0.787 en `test`, como se esperaba: `val` de C son arquetipos conocidos y `test` son arquetipos reservados. Resultados en `evaluacion_final/test/`.
- [x] Métricas globales y por etapa, con intervalos de confianza por remuestreo de partidas. AUC de B4 inicio / medio / final: A 0.684 / 0.828 / 0.937, B 0.630 / 0.774 / 0.915, C 0.623 / 0.787 / 0.919. Archivos `evaluacion_final/test/metricas_X.csv`.
- [x] Comparación contra los tres puntos de referencia: B0 (trivial), B2 (razonable) y literatura (AUC 0.78-0.80). La escalera B0 < B1 < B2 < B3 < B4 se mantiene en `test` en los tres escenarios y todas las diferencias de B4 frente a B0–B3 tienen intervalos que excluyen 0 (frente a B2: +0.071, +0.043 y +0.036 de AUC). Se cumple el criterio del artículo (III-D): el límite inferior de B4 supera al superior de B1 en A, B y C. Literatura, solo como orden de magnitud: la etapa final de A llega a 0.937 [0.932, 0.941] y la banda 0.78 se alcanza desde el turno 7. Archivos `comparaciones_X.csv` y `referencias.json`.
- [x] Curvas de aprendizaje (25 %, 50 %, 75 % y 100 % de las partidas de train) y diagnóstico de sobreajuste. El último 25 % suma ≤ 0.004 de AUC en `val`; la brecha `train − val` es estable (≈ 0.034 en A y C; ≈ 0.09 en B, por el cambio temporal): no hay sobreajuste creciente y más partidas aportarían poco. El 100 % reproduce el AUC de `val` de B4. Archivos en `evaluacion_final/curvas/`.
- [x] Análisis de errores: predicciones muy seguras y equivocadas, falsos positivos y negativos, por etapa. Al inicio hay más falsos positivos (0.22–0.25) que negativos (0.15–0.17): el modelo sobreestima la victoria temprano. Las predicciones muy seguras y equivocadas son menos del 1 % de los estados y más frecuentes fuera de la población (B y C); la precisión de las predicciones seguras sube de 0.80–0.90 en inicio a 0.96–0.98 en final. Archivos en `evaluacion_final/errores/`.
- [x] SHAP sobre el modelo final, con hallazgos accionables y revisión de fuga (ninguna variable inesperada debe dominar). Revisión de fuga aprobada antes de abrir `test`: ninguna columna prohibida, la característica principal concentra 0.113 y la mejor característica sola llega a AUC 0.690. Por familia: recursos y tablero 72.8 %, diferenciales 20.9 %, progreso 6.3 %; dominan la diferencia de premios, los descartes y el mazo. Hallazgos accionables en la sección 6 del documento de resultados. Archivos en `evaluacion_final/shap/`.
- [x] Calibración (módulo de grupo de 3): diagramas de fiabilidad y Brier antes y después; recalibración isotónica o de Platt ajustada solo con `calib`; en A y en B. B4 ya está calibrado en A (ECE 0.002) y no se corrige. En B, B4 es sobreconfiado (ECE 0.037) y la isotónica ajustada en `calib` lo baja a 0.018 en `test` (log loss 0.551 → 0.547). Recalibrar B3 en B empeoró `test`: una corrección ajustada el 11 de julio no se transfirió a los días 15 y 22. El modelo final para la Etapa 3 queda sin calibrador. Archivos en `evaluacion_final/calibracion/`.
- [x] Prueba de H3: en el escenario B, comparar cuánto se degradan la calibración (log loss, Brier) y el ordenamiento (AUC). Diseño emparejado sobre las 1 405 partidas que son `test` en A y en B, con la descomposición calibración/discriminación del protocolo. La calibración se degrada (ΔMCB del log loss 0.008), pero el ordenamiento se degrada entre 3.5 y 4.9 veces más (ΔDSC 0.030); el contraste queda bajo 0 en log loss y en Brier. La comparación ingenua de caídas relativas (23 % contra 9 %) habría dicho lo contrario por un efecto de escala. Archivos en `evaluacion_final/hipotesis/`.
- [x] Veredicto sobre H1, H2 y H3. **H1 sostenida** en A, B y C: el AUC en inicio supera claramente 0.5 y, en la cohorte de partidas que llegan a las tres etapas, sube unos 0.32 hasta final. **H2 no sostenida en general:** refutada en A, donde en inicio B4 (0.684) y el modelo de solo turno e identidad de los activos (0.682) no se distinguen, y sostenida en B (+0.041) y C (+0.088); el estado completo aporta cuando cambia la población. **H3 refutada:** bajo cambio temporal el ordenamiento se degrada más que la calibración. Archivo `evaluacion_final/veredicto.json`.
- [x] README de reproducción, cuaderno final con salidas y declaración de uso de IA. Sección de reproducción en `README.md`, `notebooks/06_evaluacion_final.ipynb` con salidas e interpretación, y `docx/03Evidencia/01UsoDeIA/Etapa2UsoDeIA.md` completa.

### `06PendientesDelArticulo` - Completa

Las instrucciones exigen que al cerrar la Etapa 2 el artículo tenga escritas la metodología definitiva y los experimentos y resultados.

- [x] Escribir la sección de metodología definitiva con lo implementado (datos, extractor, particiones, protocolo)
- [x] Escribir la sección de experimentos y resultados con las salidas de `05FinalModelChecks`
- [x] Declarar en el artículo las desviaciones del protocolo de evaluación: una sola semilla (IV-F); sin coeficientes de B2 ni importancia por permutación agrupada (IV-E); variante de 64 características no ejecutada (IV-D1); escenario C por arquetipos y no por mazos
- [x] Actualizar la tabla del corpus: 55 196 partidas y 7 540 389 estados (no 52 085 y 7 038 378)
- [x] Premios restantes: se cuentan por el largo de la lista, no "contando las ranuras no vacías" (todas son nulas)
- [x] Número de turno: el diccionario lo pone a la vez en "Progreso" y en "Agrupación"; queda como característica (`game_turn`) y como meta (`turn`)
- [x] Escenario B: el 17 jun queda fuera y la asignación es por días completos (train 18-25 jun, val 7 jul, calib 11 jul, test 15 y 22 jul)
- [x] Escenario C: arquetipos reservados por Pokémon principal (33 principales, 15.1 % de partidas); mide arquetipos nuevos, no cartas nuevas
- [x] Cobertura efectiva de cartas: A completa; B con cartas nuevas en 0.86-1.20 % de las filas; C en 0.061 % de las filas de test
- [x] Ids de carta fuera del modelo principal; solo en la ablación de contexto de mazo (H2)
- [x] "Gana el índice 0" sube porque quien empieza ocupa la posición 0 (0.764 → 1.000), no por la posición
- [x] Casi ninguna partida termina por premios; se excluyen los estados ya resueltos (0.2 %) y la preparación
- [x] Poner la URL real del dataset en `ptcg_dataset_2026`
- [x] Revisar las entradas del Eje C marcadas como VERIFICAR
- [x] Corregir erratas menores de la Introducción
- [x] Entrega en TecDigital

---

## Etapa 3 - En curso

Entrega: fin de la semana 16. Objetivo: convertir el modelo en un componente que alguien pueda usar a través de un agente, validar ese agente y cerrar el artículo.

Contexto obligatorio para trabajar: el modelo final es B4 entrenado en A, expuesto en `ptcg_wp.predictor.PredictorVictoria` y publicado en Kaggle como `results/modelo_final/` (`b4_victoria.joblib` y `ficha.json`). Las condiciones de uso que dejó la Etapa 2 están en la sección 4 de la bitácora (`docx/03Evidencia/00BitacoraDeTrabajo/`) y en `docx/03Evidencia/04-11-26_ResultadosEvaluacionFinal.md`.

### Cómo se cubre la rúbrica

| Criterio | Puntos | Rama |
|---|---|---|
| Integración del agente (consumo verificable, registros o demostración) | 8 | `07MultiAgentIntegration` |
| Validación del agente (escenarios, casos límite, errores del modelo) | 5 | `08AgentValidationAndSimulator` |
| Ética, sesgos y privacidad (riesgos de despliegue, mitigaciones, límites) | 3 | `09EthicsPaperAndDocumentation` |
| Artículo científico (estructura completa, discusión con XAI, conclusiones) | 5 | `09EthicsPaperAndDocumentation` |
| Defensa individual | 4 | `10DefenseAndShowcase` |

### Reglas de la etapa

- El modelo no se reentrena ni se recalibra. El agente consume el modelo final tal como quedó en la Etapa 2, verificado por SHA-256 contra `ficha.json`.
- El agente nunca recibe ni pide información oculta (mano rival, contenido de los premios). Solo usa la observación pública del jugador que actúa, igual que el modelo.
- Toda cifra que el agente dé al usuario sale de una herramienta y queda en el registro de invocaciones. El agente no inventa probabilidades.
- La lógica vive en `src/ptcg_wp/` y se prueba con `pytest`; los cuadernos y las interfaces solo la ejecutan.
- Las claves de API se tratan igual que el token de Kaggle: nunca en cuadernos, archivos versionados ni conversaciones.
- Una decisión de diseño o un protocolo de validación se escribe en `docx/03Evidencia/` antes de ejecutarse.

### `07MultiAgentIntegration`

Integración del modelo en una arquitectura multiagente con *tool calling*, consumible desde Claude Desktop y Claude Code y desde un orquestador propio en Python. Código en `src/ptcg_agente/` (separado del código de entrenamiento de `src/ptcg_wp/`). Arquitectura: `docx/03Evidencia/07-11-26_ArquitecturaDelAgente.md`. Instalación y uso: `docx/05AmbienteDeDesarrollo/GuiaDelAgente.md`.

**Diseño**
- [x] Documento de arquitectura en `docx/03Evidencia/`: roles, herramientas, flujo de una consulta, formato de los registros y cómo se verifica cada respuesta
- [x] Decisión del LLM: Claude con la membresía del equipo, sin clave de API: Claude Desktop y Claude Code a través de un servidor MCP, y Claude Code sin interfaz (`claude -p`) en el orquestador; el LLM de prueba solo existe en `tests/`

**Capa de herramientas** (`src/ptcg_agente/herramientas/`, un archivo por herramienta, independiente del LLM)
- [x] Carga del modelo final desde Kaggle con verificación de SHA-256 (índice del dataset) y de la versión de scikit-learn contra `ficha.json` (`artefactos.py`, `modelo.py`)
- [x] `estimar_probabilidad`: observación pública → probabilidad de victoria, etapa de la partida y advertencias (o `None` en preparación y estados resueltos)
- [x] `explicar_prediccion`: contribuciones SHAP del estado (las más fuertes a favor y en contra), traducidas a lenguaje natural en términos de premios, descartes, mazo y tablero
- [x] `evaluar_partida`: recorre una repetición completa y devuelve la curva de probabilidad por turno con sus puntos de giro
- [x] `comparar_estados`: probabilidad de dos o más estados alternativos de la misma posición (por ejemplo, después de dos jugadas posibles)
- [x] `revisar_dominio`: detecta entradas fuera del dominio de entrenamiento (cartas no vistas, valores fuera de rango, formato inválido, preparación o estado resuelto)
- [x] `describir_modelo`: ficha del modelo, métricas en `test` y límites declarados
- [x] Perfil del dominio (`agente/dominio.json`) y repeticiones de ejemplo publicados en Kaggle (partes 1 y 2 del cuaderno `07_agente`): 4 357 908 filas `train` de A, 33 066 partidas, cortes de etapa [5, 9] y 362 cartas activas; 4 partidas de `test` de A del 22 de julio

**Arquitectura multiagente** (`src/ptcg_agente/agentes/`)
- [x] **Planificador:** interpreta la consulta del usuario y decide qué herramientas llamar y en qué orden; llamada propia a Claude sin herramientas, plan JSON con esquema y validado por Python (`agentes/planificador.py`, subagente `planificador-ptcg`)
- [x] **Ejecutor:** invoca las herramientas con entradas validadas y devuelve resultados estructurados (`herramientas.llamar`)
- [x] **Verificador:** comprueba la coherencia antes de responder: probabilidad en [0, 1], suma de SHAP igual al logit, cifras de la respuesta iguales a las de las herramientas, advertencia obligatoria en turnos tempranos y fuera de dominio (`agentes/verificador.py` y herramienta `verificar_respuesta`)
- [x] **Redactor:** respuesta final para un usuario no técnico, con la probabilidad, su explicación y sus límites; llamada propia a Claude que solo ve resultados aprobados, con reintento ante problemas del verificador y plantilla de respaldo (`agentes/redactor.py`, subagente `redactor-ptcg`)
- [x] Registro de invocaciones en JSONL: fecha, agente, herramienta, entrada resumida, salida, duración, SHA-256 del modelo y commit (`registro.py`)

**Exposición**
- [x] Servidor MCP del proyecto (`servidor_mcp.py`), registrado para Claude Code en `.mcp.json` y documentado para Claude Desktop
- [x] Orquestador en Python con *tool calling* (planificador, ejecutor, verificador y redactor), ejecutable desde terminal (`python -m ptcg_agente.orquestador`) y desde un cuaderno (`08_agente_orquestador`)
- [x] Subagentes de Claude Code (`.claude/agents/`) y comando `/consulta-ptcg` que los encadena
- [x] Pruebas del orquestador con un LLM de prueba: validación del plan, reintento del redactor, plan por defecto, plantilla y registro de los cuatro agentes
- [x] Cuaderno `07_agente` ejecutado en Colab con sus salidas (dominio, ejemplos y verificación con partidas reales)

**Verificación**
- [x] Pruebas de cada herramienta con observaciones sintéticas: misma probabilidad que `PredictorVictoria` (`tests/test_agente.py`)
- [x] Misma probabilidad que `PredictorVictoria` en cada estado de partidas reales (parte 3 del cuaderno `07_agente`): 642 estados de 4 partidas, diferencia máxima 0.0 y 642/642 resultados verificados
- [x] Pruebas del verificador: detecta probabilidades fuera de rango, SHAP que no suma, cifras inventadas, advertencias omitidas y promesas de certeza
- [x] Prueba del servidor MCP de punta a punta con un cliente MCP real por stdio
- [x] Evidencia del flujo completo con Claude Code: `docx/03Evidencia/08-11-26_RegistroSesionClaudeCode.jsonl` y `.png` (consulta sobre la partida 87406956; el verificador rechazó un primer borrador y aprobó el corregido)
- [ ] Evidencia del orquestador en Python (registro de una corrida con planificador, ejecutor, verificador y redactor)

### `08AgentValidationAndSimulator`

Validación del agente frente a escenarios normales, casos límite, entradas inesperadas y errores del modelo, y un simulador gráfico que el agente puede abrir para que un humano manipule un estado y vea la probabilidad cambiar en tiempo real.

**Protocolo de validación** (escrito antes de ejecutar)
- [ ] Protocolo en `docx/03Evidencia/`: escenarios, entradas, comportamiento esperado y criterio de aprobación de cada uno
- [ ] Escenarios normales: estados de partidas de `test` de A en inicio, medio y final
- [ ] Casos límite: preparación, estado resuelto, banca vacía, mazo en cero, un premio por tomar, turno 1, partidas muy largas
- [ ] Entradas inesperadas: JSON mal formado, tipos incorrectos, campos faltantes, cartas no vistas, valores imposibles, observación del jugador que espera
- [ ] Datos fuera del dominio de entrenamiento: estados de B (días posteriores) y C (arquetipos reservados), y estados sintéticos alejados de la distribución
- [ ] Errores del modelo: predicciones muy seguras y equivocadas del análisis de errores de la Etapa 2; qué dice el agente y si advierte la incertidumbre
- [ ] Consultas adversas al LLM: pedir la mano rival, pedir certeza absoluta, instrucciones inyectadas dentro de los datos de la partida

**Ejecución y análisis**
- [ ] Batería automática de escenarios con resultados guardados (aprobado o fallido por caso)
- [ ] Métricas del agente: herramienta correcta por consulta, cifras de la respuesta iguales a las herramientas, advertencias emitidas cuando corresponden, rechazos correctos fuera de dominio y latencia
- [ ] Análisis de fragilidad: qué pasa cuando el modelo se equivoca y el agente confía en él, qué detecta el verificador y qué no
- [ ] Resultados documentados en `docx/03Evidencia/`

**Simulador gráfico** (`src/ptcg_wp/simulador/`)
- [ ] Aplicación web local que muestra un estado de partida de forma gráfica: activos, banca, premios, mano, mazo, descartes y energías de ambos jugadores
- [ ] Edición del estado por el usuario (premios, PV, banca, cartas en mazo y descarte, energías) con la probabilidad de victoria actualizada en tiempo real por el modelo final
- [ ] Reproducción de partidas reales del corpus turno a turno, con la curva de probabilidad y los puntos de giro
- [ ] Panel con las contribuciones SHAP del estado actual y las advertencias del verificador
- [ ] Herramienta del agente `abrir_simulador` para lanzarlo con un estado o una partida dados
- [ ] Validación humana: sesiones de cada integrante con el simulador, registrando si la dirección de los cambios de probabilidad tiene sentido de juego
- [ ] Pruebas del simulador (la probabilidad mostrada coincide con la del predictor) y capturas o grabación como evidencia

### `09EthicsPaperAndDocumentation`

Ética del despliegue, artículo final y documentación completa del repositorio.

**Ética, sesgos y privacidad**
- [ ] Riesgos concretos de despliegue: uso para obtener ventaja en competencias, confianza excesiva en la probabilidad, sesgo hacia el meta de agentes automáticos, mal uso en apuestas
- [ ] Datos sensibles involucrados: nombres de agentes (seudonimizados), licencia CC0 del corpus, información oculta que el sistema no usa
- [ ] Mitigaciones aplicadas y verificables en el código: verificador, advertencias, revisión de dominio, sin información oculta, registros
- [ ] Límites declarados del sistema

**Artículo final**
- [ ] Secciones nuevas: arquitectura del agente y validación del agente, con sus resultados
- [ ] Sección de ética reescrita con foco en el despliegue
- [ ] Discusión y conclusiones actualizadas con el agente, conservando los hallazgos de XAI
- [ ] Introducción y trabajos relacionados pulidos, sin reescribirlos
- [ ] Resumen, objetivos y contribuciones alineados con el trabajo completo
- [ ] Revisión completa del documento en formato IEEE: figuras, tablas, referencias, compilación sin errores

**Documentación**
- [ ] `README.md`, `GuiaDeAmbiente.md` y `notebooks/EjecucionDeLosCuadernos.md` con cómo ejecutar el agente, el servidor MCP y el simulador
- [ ] `HerramientasDeDesarrollo.md`, `ReglasGit.md` (ramas de la Etapa 3) y `Contenido.md` actualizados
- [ ] Declaración de uso de IA de la Etapa 3 (`docx/03Evidencia/01UsoDeIA/Etapa3UsoDeIA.md`)
- [ ] Bitácora de trabajo con la Etapa 3

### `10DefenseAndShowcase`

Preparación de la defensa individual, video demostrativo y entrega final.

**Defensa**
- [ ] Guía de defensa en `docx/`: respuestas a las tres preguntas garantizadas (por qué este dataset y qué limitaciones se asumieron; cómo se previno la fuga; qué significa el resultado frente al baseline de literatura)
- [ ] Preguntas probables por cada parte del proyecto (datos, baselines, B4, evaluación, calibración, SHAP, agente, validación, ética), para que cada integrante pueda responder sobre todo
- [ ] Ensayo de la defensa con los tres integrantes

**Video**
- [ ] Guion y orden de escenas: problema, datos, prevención de fuga, resultados principales, SHAP, agente en ejecución, simulador y límites
- [ ] Grabación de la demostración en ejecución (consulta al agente, registros, simulador)
- [ ] Video editado y enlazado desde el `README.md`

**Entrega**
- [ ] Prueba de clon limpio siguiendo solo el `README.md`
- [ ] Historial con commits de los tres integrantes en la Etapa 3
- [ ] PR `Stage3` → `master` con 1 aprobación, etiqueta `v3.0.0` y release
- [ ] Entrega en TecDigital