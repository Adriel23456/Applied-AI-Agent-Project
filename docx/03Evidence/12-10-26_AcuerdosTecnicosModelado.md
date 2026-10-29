# Acuerdos técnicos para el modelado de la Etapa 2

**Fecha:** 12 de octubre de 2026  
**Participantes:** integrante que retoma la rama `04MainAIModelTrainingAndDevelopment` y asistente de IA  
**Propósito:** registrar los acuerdos de planificación previos a la implementación de los cuadernos de modelado. Este documento distingue las decisiones acordadas de los detalles que siguen abiertos.

## Decisiones acordadas

### Actualización del 28 de octubre de 2026: selección global de B3 y definición de H2

- Los resultados de A, B y C responden preguntas distintas y se publicarán por separado, sin
  combinar las filas ni presentar un promedio entre escenarios como resultado de desempeño.
- Para elegir **una sola configuración común de B3**, se usará como criterio interno el
  macro-promedio simple del AUC global en `val` de A, B y C. Cada escenario aporta el mismo peso,
  independientemente de su cantidad de partidas. El AUC es la métrica primaria; log loss y Brier
  se revisan y reportan por escenario, sin combinarlos en un puntaje.
- El conjunto de configuraciones comparables se limita a las finalistas con exactamente los mismos
  hiperparámetros evaluadas en `val` para los tres escenarios. El macro-AUC solo decide la
  configuración compartida y no se presenta como estimación de desempeño general. No se requiere
  repetir la búsqueda ni ejecutar el bootstrap emparejado para aplicar esta regla; la selección por
  métricas observadas no demuestra que las diferencias sean estadísticamente significativas.
- En H2, “estado completo” significa las 62 características públicas del estado, sin IDs de carta.
  La versión restringida contiene cuatro entradas: `game_turn`, `first_player_is_me`,
  `own_active_card` y `opp_active_card`. Los IDs activos son una aproximación a la identidad del
  mazo, no su composición completa. La variante de 64 características (estado completo más los
  dos IDs) es una ablación diferente.

### B1: heurística de dominio

- B1 tendrá una regla de puntuación definida por conocimiento del juego; sus pesos no se aprenderán de `y` como en un modelo supervisado general.
- `train` se usará para convertir la puntuación fija en una probabilidad de victoria.
- La propuesta concreta incorporada en `notebooks/02_baselines.ipynb` es `(opp_prizes - own_prizes) + diff_total_hp / hp_unit + diff_bench_n`. `hp_unit` se calcula como el promedio de PV máximos activos positivos observado en `train`, con peso igual por partida; no usa etiquetas ni IDs de carta. Una regresión logística de una variable ajusta solo la pendiente y el intercepto con `train`.
- Esta fórmula y su escala son una propuesta para revisión, no un acuerdo final. Falta confirmarlas antes de interpretar resultados como evidencia final.

### Validación cruzada y selección de configuraciones

- Se usarán cinco pliegues de `GroupKFold`, agrupados por `game_id`, dentro de `train`.
- Optuna evaluará configuraciones con los resultados de esos pliegues. El uso de las tres métricas buscará conservar configuraciones con buenos balances, sin combinarlas mediante pesos arbitrarios.
- La lista finalista será de hasta tres **configuraciones** provenientes de la validación cruzada: la de mejor AUC, la de menor log loss y la de menor Brier. Si una configuración destaca en más de una métrica, se cuenta una sola vez.
- La partición fija `val` se usará solo para comparar esas finalistas. Los pliegues de GroupKFold no son candidatos; son las divisiones que se usan para puntuar cada configuración.
- `test` queda reservado para la evaluación final después de cerrar toda selección.

### Regla para escoger entre finalistas

- AUC es la métrica principal establecida en el artículo. Si una candidata mejora AUC de forma clara, se favorece esa candidata.
- La actualización del 28 de octubre establece el criterio específico para seleccionar una configuración común de B3 entre escenarios. El remuestreo emparejado descrito abajo puede cuantificar incertidumbre, pero no es requisito para aplicar ese criterio ni convierte diferencias observadas en significancia estadística.
- Si las AUC son prácticamente comparables, se favorece la candidata con mejores probabilidades.
- Si log loss y Brier discrepan, se prioriza menor log loss siempre que no haya evidencia clara de deterioro en Brier.
- Para comparar Brier entre dos finalistas en `val`, se remuestrearán las mismas partidas en ambas candidatas en cada repetición. Se calculará la diferencia `Brier_B − Brier_A`: valores positivos indican que B tiene peor Brier.
- Si el intervalo de esa diferencia incluye cero, no se considera demostrado que Brier empeore; si queda completamente por encima de cero, se considera evidencia de deterioro. “Incluye cero” significa que los resultados son compatibles con que no haya diferencia; no demuestra que ambas candidatas sean idénticas.
- Se recomendó usar 1 000 repeticiones del remuestreo. La cantidad de partidas sorteadas en cada repetición será igual al número de partidas de `val`, con reemplazo.
- Para cualquier análisis de incertidumbre que se realice, el nivel de confianza y el tipo de intervalo siguen pendientes. El 95 % se mencionó como opción, no como acuerdo. Las 2 000 repeticiones fueron una confusión; no son la recomendación vigente.

### Peso de partidas y estados

- Cada partida tendrá el mismo peso total en las métricas y durante el entrenamiento. Si una partida aporta más estados, el peso de cada uno se reducirá para que la partida no tenga más influencia solo por ser larga.
- Para una métrica calculada en un subconjunto —por ejemplo, una etapa— la interpretación prevista es dar el mismo peso total a cada partida representada en ese subconjunto. La implementación debe documentar esta regla.
- Los intervalos se calcularán remuestreando partidas completas, conservando juntas las filas de cada partida. Este remuestreo estima variación entre partidas; no corrige la ponderación, que ya se define arriba.
- El artículo advierte que incluso los intervalos que respetan los grupos pueden subestimar la incertidumbre. La limitación deberá conservarse al interpretar resultados.

### B3: bosque aleatorio

- B3 comparará un árbol de decisión y un bosque aleatorio. Cada tipo tendrá su propia búsqueda TPE; AUC, log loss y Brier producirán hasta tres configuraciones finalistas por tipo, sin combinar métricas con pesos arbitrarios.
- Las búsquedas usarán cinco pliegues agrupados por `game_id` dentro de `train`. `val` solo comparará las finalistas, y `test` seguirá reservado.
- Espacio inicial implementado para revisión: árbol (`criterion`, `max_depth`, `min_samples_leaf`, `ccp_alpha`); bosque (`n_estimators`, `criterion`, `max_features`, `max_depth`, `min_samples_leaf`). Los límites y cantidad de pruebas son controles explícitos del cuaderno y deben ajustarse con el piloto antes del ciclo completo.
- Si el costo obliga a submuestrear el bosque, se seleccionarán partidas completas, con semilla fija.
- Se registrarán la semilla, el número de partidas seleccionadas y la proporción que representan de `train`.
- Si el objetivo es entregar una configuración común a A, B y C, la selección final entre las configuraciones idénticas disponibles en los tres escenarios se hará por macro-AUC de `val`, conforme a la actualización del 28 de octubre. Los resultados individuales seguirán visibles por escenario.
- El piloto usa 1 000 partidas completas, dos pliegues (ejecuta uno para medir) y una prueba por métrica/modelo. En modo completo, `max_train_games=None` solicita todo train y una guarda de RAM detiene la ejecución antes de agotar Colab.

### B2: regresión logística regularizada

Actualización de implementación del 18 de octubre: B2 pasa a ajuste incremental
con todos los estados de train. Se conserva el objetivo logístico L2 y se
convierte C a alpha; consultar [B2 con memoria acotada](18-10-26_B2MemoriaAcotada.md)
para el optimizador, la evaluación en disco y las comprobaciones de convergencia.

- B2 usará las 62 características numéricas del modelo principal, sin IDs de carta, dentro de un `Pipeline` con `StandardScaler` y regresión logística con penalización L2.
- La regularización se escogerá mediante búsqueda exhaustiva en cuadrícula logarítmica, no mediante Optuna. Solo se explora un hiperparámetro (`C`), por lo que evaluar cada candidato es más simple y auditable que una búsqueda bayesiana.
- La cuadrícula propuesta es `C = [1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100, 1000, 10000]`. Los valores pequeños imponen una regularización más fuerte; los grandes, una más suave.
- Cada valor se evaluará en cinco pliegues de `GroupKFold` por `game_id`, con peso total igual por partida. Antes de ejecutar todos los escenarios se medirá el costo de tiempo y memoria en una prueba piloto.

### Semillas y reproducibilidad

- Se conserva `SEED = 2026` para las particiones existentes.
- La primera búsqueda de Optuna usará una semilla fija para poder reproducirla.
- Se acordó iniciar con semillas fijas y considerar repeticiones con semillas distintas según el presupuesto y los requisitos del artículo. El número y alcance exactos de las repeticiones aún deben quedar definidos.

### Parada temprana de B4

- La parada temprana deberá respetar partidas completas; no se permitirá una reserva aleatoria de filas que pueda colocar estados de una misma partida en entrenamiento y vigilancia.
- Se usa la opción de scikit-learn que admite datos de vigilancia externos para `HistGradientBoostingClassifier`. Se fija `scikit-learn==1.7.2`, pues esta API incorpora `X_val` e `y_val` desde la versión 1.7; Colab debe reinstalar `requirements.txt` y reiniciar el runtime antes de B4.
- La partición de vigilancia se formará por `game_id` dentro de los datos de entrenamiento de la ronda correspondiente. El pliegue reservado para evaluar esa ronda se mantendrá aparte.

### Búsqueda de B4

- Se usará Optuna con TPE, con un espacio de búsqueda acotado y límites tanto de cantidad de pruebas como de tiempo.
- El espacio inicial propuesto contiene cuatro controles: `learning_rate`, `max_leaf_nodes`, `min_samples_leaf` y `l2_regularization`; la cantidad de árboles se manejará mediante parada temprana.
- El piloto ejecuta una prueba por métrica y dos pliegues para medir tiempo y RAM con el corpus completo. El modo completo inicia con diez pruebas por métrica y cinco pliegues; el límite de tiempo debe fijarse a partir de la medición piloto, antes de la ejecución costosa.

## Decisiones pendientes

1. Confirmar o ajustar la fórmula propuesta de B1 y su interpretación de escala antes de usar sus resultados como evidencia final.
2. Elegir el nivel de confianza y el tipo de intervalo para las comparaciones emparejadas de AUC y Brier. El criterio acordado es tratar una diferencia cuyo intervalo incluya cero como empate práctico o ausencia de deterioro claro, según la métrica; esto no prueba equivalencia.
3. Elegir el nivel de confianza y la cantidad de remuestreos para los intervalos. El 95 % y las 2 000 repeticiones se mencionaron solo como ejemplos recomendados, no como acuerdos.
4. Definir el límite de tiempo de Optuna para B4 después de la prueba piloto.
5. Cerrar el protocolo de LightGBM: alcance de su búsqueda, presupuesto comparable con B4 y criterio para considerar que supera claramente al modelo principal.
6. Definir cuántas repeticiones con distintas semillas se harán y si repetirán solo el ajuste final o también la búsqueda completa.

## Fuentes internas y técnicas

- `docx/01SeguimientoDeTareas/PlanDeDesarrollo.md`: pendientes de las ramas 04 y 05.
- `docx/05AmbienteDeDesarrollo/DiccionarioDeDatos.md`, sección 10: contrato obligatorio para modelar.
- `docx/02Papers/00MainPaper/sec/04metodologia.tex`: protocolo, métricas, baselines, calibración e intervalos propuestos.
- [Documentación de `GroupKFold` en scikit-learn 1.6.1](https://scikit-learn.org/1.6/modules/generated/sklearn.model_selection.GroupKFold.html).
- [Documentación de `HistGradientBoostingClassifier` en scikit-learn 1.7.2](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html). La API documenta `X_val` e `y_val` desde la versión 1.7.
- [Documentación de Optuna](https://optuna.readthedocs.io/en/stable/).
- [Documentación de LightGBM `LGBMClassifier`](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMClassifier.html).

Este registro recoge acuerdos de planificación de la conversación del equipo. Cuando se cierren los detalles pendientes, deben reflejarse en las configuraciones, los cuadernos y, cuando cambien el protocolo, en el artículo.
