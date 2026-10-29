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

Cuadernos: `02_baselines_B0_B1`, `03_baseline_B2`, `04_baseline_B3` y `05_baseline_B4`. Cada uno presenta un baseline; B2 y B3 no relanzan búsquedas cerradas. B4 presenta los resultados versionados sin relanzar el entrenamiento cerrado.
Escalera definida en el artículo (Tabla "Escalera de modelos de referencia"). Cada peldaño responde
una pregunta; **B4 es el modelo principal** (potenciación del gradiente, estado del arte en datos tabulares).

- [ ] Registro de cada ejecución en `results/` (escenario, modelo, configuración, semilla, métricas, tiempo, commit)
- [ ] Funciones de evaluación comunes: AUC, log loss y Brier, globales y por etapa, con el número de partidas de cada etapa
- [ ] B0 - probabilidad a priori (prevalencia de train). Piso de referencia
- [ ] B1 - heurística de dominio sobre diferencias de recursos (premios, PV, Pokémon en juego), llevada a probabilidad ajustando solo con train
- [ ] B2 - regresión logística regularizada en un `Pipeline` (escalado ajustado solo con train). Referencia "razonable" de la rúbrica
- [ ] Demostración de inflación: B2 con partición por fila contra partición por partida, midiendo cuántas partidas quedan en ambos lados
- [ ] B3 - árbol de decisión y bosque aleatorio. Para elegir una configuración única común, comparar finalistas con los mismos hiperparámetros en A/B/C por macro-AUC de `val`; después ajustar esa configuración usando el `train` propio de cada escenario y reportar sus métricas por separado.
- [x] B4 - modelo principal: `HistGradientBoostingClassifier` con búsqueda bayesiana de hiperparámetros (Optuna, TPE, 20 trials) y validación cruzada agrupada por `game_id` sobre las partidas train de A, B y C; parada temprana; reentrenado en cada escenario y medido en `val` (AUC A 0.835, B 0.786, C 0.836). Resultados y modelos en `results/baseline4/`
- [ ] Verificación de implementación: LightGBM con la misma búsqueda y el mismo protocolo; si no supera a B4 de forma clara, se reporta y se mantiene B4
- [ ] Ablaciones por familia de características (progreso, recursos y tablero, diferenciales) sobre B4
- [ ] Prueba de H2: comparar B4 con las 62 características públicas del estado contra B4 restringido a `game_turn`, `first_player_is_me`, `own_active_card` y `opp_active_card`. Los IDs del Pokémon activo son una aproximación a la identidad del mazo, no el mazo completo. La variante de 64 características (estado completo más IDs) es una ablación distinta.
- [ ] Evaluación de B0 a B4 en cada escenario (A, B y C), conservando sus particiones y reportando cada escenario por separado; cuando aplique, los hiperparámetros comunes no implican mezclar los datos de `train`.
- [ ] Modelo final exportado, con una función que convierte una observación del juego en probabilidad (para la Etapa 3). Modelos de B4 ya versionados en `results/baseline4/final_4000/`; falta la función de observación a probabilidad

### `05FinalModelChecks`

Cuaderno: `04_evaluacion_xai_calibracion`.

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
