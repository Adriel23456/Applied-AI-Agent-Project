# Protocolo de evaluación final (`05FinalModelChecks`)

Fecha: 2 de noviembre de 2026.
Participantes: Sebastián Hernández Bonilla y asistente de IA (Claude). El equipo debe revisarlo antes de ejecutar.
Estado: **propuesto para congelar.** Se considera congelado cuando su commit llega a `05FinalModelChecks`, siempre antes de ejecutar la celda de `test` de `notebooks/06_evaluacion_final.ipynb`. La celda registra ese commit en `registro.json`.
Al escribir este documento no se había calculado ninguna predicción ni métrica sobre `calib` o `test`.

## 1. Qué se evalúa

| Referencia | Modelo | Artefacto en el dataset de Kaggle |
|---|---|---|
| B0 | Prevalencia de `train` | `b0_b1/ajustes_B0_B1.csv` |
| B1 | Heurística de recursos | `b0_b1/ajustes_B0_B1.csv` |
| B2 | Regresión logística `C=0.1` | `b2/final/escenario_X/b2_X_C0.1.joblib` |
| B3 | Bosque común (trial 1) | `b3/final/escenario_X/b3_X_B3_bosque_log_loss.joblib` |
| B4 | HistGradientBoosting, trial 20 (**modelo principal**) | `b4/final/escenario_X/b4_auc_CVtrial20.joblib` |
| H2 | B4 restringido a cuatro entradas | `b4/h2/escenario_X/h2_restringido.joblib` |

Cada modelo se evalúa con el ajuste de su propio escenario. No se reentrena ningún modelo para `test`. Las únicas excepciones de ajuste son los calibradores (solo `calib`) y las curvas de aprendizaje (solo `train`, medidas en `val`).

Los resultados de A, B y C se reportan por separado. Nunca se promedian ni se mezclan sus filas.

## 2. Orden y barreras

`test` se usa una sola vez. Ninguna decisión puede depender de sus números. Por eso el orden del cuaderno es:

1. Este protocolo.
2. Verificación de carga: las predicciones de B0 a B4 y H2 sobre `val` deben reproducir las métricas ya publicadas. Log loss y Brier a 1e-9 y AUC a 1e-6. B3 se tolera hasta 1e-3 solo en AUC, porque tiene empates exactos y su bosque paralelo cambia el último bit de algunas filas según el lote; que sus predicciones son las mismas lo prueban log loss y Brier.
3. SHAP y revisión de fuga sobre `val`.
4. Calibración: ajuste y decisión solo con `calib`.
5. Curvas de aprendizaje sobre `val`.
6. **Evaluación única en `test`.**
7. Calibración medida en `test`, hipótesis, análisis de errores y veredictos.

Esto cambia a propósito el orden sugerido en el cuaderno, que dejaba SHAP para después de `test`. La revisión de fuga solo sirve de barrera si ocurre antes de abrirlo. La celda de `test` no corre si falta la decisión de calibración o las curvas, o si la revisión de fuga no aprobó. Si la revisión falla, se detiene el trabajo y se avisa al equipo; `test` sigue intacto.

Una vez publicadas, las predicciones de `test` quedan en Kaggle y la celda ya no vuelve a predecir. Si se detecta un error después de abrir `test`, se documenta y se reporta como tal. No se ajusta nada para mejorar el resultado.

## 3. Métricas e intervalos

- AUC (principal), log loss y Brier, globales y por etapa, con `n_estados` y `n_partidas`. Cada partida pesa lo mismo; dentro de una etapa los pesos se recalculan. Las cifras puntuales vienen de `ptcg_wp.evaluation.metric_rows_codes`.
- Intervalos: percentil del 95 %, 1000 remuestreos de partidas completas con reemplazo, semilla 2026. Cierra el pendiente 3 de `12-10-26_AcuerdosTecnicosModelado.md`.
- Las comparaciones son emparejadas: los modelos reciben las mismas multiplicidades de partida en cada réplica.
- Los intervalos son individuales por escenario, no simultáneos. No incorporan la incertidumbre de la búsqueda ni la del ajuste, y según Brill et al. pueden ser optimistas. Esta limitación acompaña cada conclusión.

### Referencias

- **B0 (trivial) y B2 (razonable):** diferencia emparejada `B4 − referencia` en AUC, log loss y Brier.
- **B1 (criterio interno de éxito, Sección III-D del artículo):** se cumple si B4 supera a B1 en AUC en test y los intervalos de ambos no se solapan.
- **Literatura (AUC 0.78–0.80):** es un orden de magnitud, no un umbral, porque el juego, la población y la partición difieren. Se reporta si el AUC de B4 en la etapa `final` del escenario A alcanza la banda y el primer turno en que el AUC puntual llega a 0.78.

## 4. Calibración

Se aplica en A y en B a B2, B3 y B4.

- Se mide antes y después: Brier, log loss, ECE con 10 intervalos de igual masa y descomposición CORP (Dimitriadis et al.) en error de calibración (MCB), discriminación (DSC) e incertidumbre (UNC). La versión PAV se calcula con `sklearn.isotonic`, por lo que se usa la medida reproducible y no solo el ECE.
- Método principal: regresión isotónica, como fija el artículo. Se reporta Platt como contraste, por la recomendación de Ojeda et al. para poblaciones externas.
- Los calibradores se ajustan **solo con `calib`**, con pesos 1/n por partida.
- Decisión de corregir: como pide el artículo, se mide antes de decidir. Con validación cruzada de 5 pliegues agrupada por partida dentro de `calib`, se comparan sin corrección, isotónica y Platt por log loss. La elección queda en `decision_calibracion.json` antes de abrir `test`. Todas las variantes se reportan en `test`; verlas allí no cambia la elección.

## 5. Curvas de aprendizaje

- Fracciones 25, 50, 75 y 100 % de las partidas de `train` de cada escenario. Los subconjuntos son anidados y se sortean por partida con semilla 2026.
- Mismo protocolo que B4 final: trial 20, vigilancia del 15 % por partida, paciencia 30, tope 4000 y reajuste con el subconjunto. El 100 % reutiliza el modelo final.
- Se miden en `val` y en una muestra fija de hasta 5000 partidas del subconjunto de `train`. `test` no participa.
- Diagnóstico de sobreajuste: brecha `train − val` por fracción y si el AUC de `val` sigue subiendo entre 75 y 100 %.

## 6. SHAP y revisión de fuga

- Modelo: B4 de A (`modelo_final/`). Datos: muestra de partidas de `val` de A, por partida y con semilla 2026.
- Se reporta la importancia media absoluta por característica, global y por etapa, con cada partida con el mismo peso. También por familia (progreso, recursos y tablero, diferenciales).
- La revisión aprueba si se cumplen las tres condiciones:
  1. Ninguna columna meta, de carta o prohibida está entre las características del modelo.
  2. Ninguna característica concentra más del 50 % de la importancia total.
  3. Ninguna característica sola alcanza AUC ≥ 0.85 en `val`, en ninguno de los dos sentidos (el criterio de la sección 6 del diccionario de datos).
- El 50 % es un límite de revisión, no un resultado científico: su cruce obliga a investigar antes de seguir.

## 7. Hipótesis

Las reglas siguen los criterios de la Sección I-E del artículo y no fijan umbrales numéricos de mejora. Se decide por escenario y se usa B4 sin recalibrar.

### H1: señal temprana que crece con la partida

Modelo B4 en A, B y C.

- (a) En la etapa `inicio`, el límite inferior del intervalo del AUC es mayor que 0.5.
- (b) En la cohorte de partidas con estados en las tres etapas, el intervalo de `AUC final − AUC inicio` queda por encima de 0. Usar la misma cohorte es el control de duración: las partidas cortas nunca llegan a `final`, así que comparar etapas con todas las partidas mezclaría duración y progreso.

Resultado: **sostenida** si (a) y (b) se cumplen en el escenario; **debilitada** en otro caso.

### H2: la señal temprana no se explica solo por turno e identidad

Modelo B4 contra H2 restringido, en la etapa `inicio` de A, B y C.

- **Sostenida** si el intervalo de `AUC B4 − AUC H2` queda por encima de 0.
- **Refutada** si el restringido iguala o supera a B4: el intervalo incluye 0 o queda por debajo.

Se reporta además la comparación global, log loss, Brier y la fracción de estados con ids no vistos en `train`. Los ids del activo aproximan la identidad del mazo; no son el mazo completo.

### H3: bajo cambio temporal, las probabilidades se degradan antes y más que el ordenamiento

**Por qué no basta comparar caídas de AUC y de log loss.** Están en escalas distintas. La habilidad en log loss crece aproximadamente con el cuadrado de la separación entre clases, y el AUC de forma casi lineal, de modo que una caída relativa de log loss mayor que la de AUC aparece aunque la calibración sea perfecta. Compararlas directamente favorecería a H3 sin evidencia. Se usa la descomposición de la Figura 6 del artículo, que deja ambas magnitudes en las mismas unidades:

`puntaje = MCB − DSC + UNC`

Sobre las mismas partidas UNC es igual, así que el deterioro del puntaje se reparte exactamente entre calibración (sube MCB) y ordenamiento (baja DSC).

**Diseño emparejado.** Se usan las partidas de `test` de A jugadas el 15 y el 22 de julio, que también son `test` de B. Sobre esas mismas partidas se comparan dos modelos que no las vieron: el de A, entrenado con todos los días, y el de B, entrenado solo con días anteriores. Así el cambio medido viene del entrenamiento y no de la composición del conjunto evaluado.

Para cada puntaje `s` (log loss y Brier):

- `ΔMCB_s = MCB_s(B) − MCB_s(A)`: calibración perdida.
- `ΔDSC_s = DSC_s(A) − DSC_s(B)`: ordenamiento perdido.
- `C_s = ΔMCB_s − ΔDSC_s`.

Resultado, con intervalos emparejados del 95 %:

- **Sostenida** si, en log loss y en Brier, el intervalo de `ΔMCB_s` y el de `C_s` quedan por encima de 0.
- **Refutada** si, en log loss y en Brier, el intervalo de `C_s` queda por debajo de 0.
- **No concluyente** en cualquier otro caso.

Para responder directamente al plan se reportan también `ΔAUC`, `Δlog loss` y `ΔBrier` del mismo diseño, con su pérdida relativa de habilidad frente a una moneda justa, como descripción y sin decidir con ella. Se reporta la serie por día del modelo de B (7, 11, 15 y 22 de julio) para el "antes", y la comparación completa `test` A contra `test` B como referencia no emparejada.

**Limitaciones.** A entrena con más partidas que B (33 066 contra 27 643); las curvas de aprendizaje indican cuánto pesa eso. Calendario y versión del motor siguen confundidos. La versión PAV ajusta sobre el propio conjunto evaluado, por lo que MCB tiene un sesgo positivo pequeño, igual en ambos modelos.

## 8. Análisis de errores

Se ejecuta después de `test`, es exploratorio y no cambia ningún modelo. Por escenario y etapa, con B4 sin recalibrar:

- Falsos positivos y negativos con umbral 0.5, solo para describir.
- Muy seguras y equivocadas: `p ≥ 0.9` con derrota y `p ≤ 0.1` con victoria.
- Perfil de esas filas frente a las seguras y acertadas, por diferencia estandarizada de características.

## 9. Desviaciones declaradas frente al artículo

| Artículo | Implementado | Motivo |
|---|---|---|
| Cada experimento se repite con varias semillas (IV-F) | Una semilla; se conserva el pendiente 6 de los acuerdos del 12 de octubre | Costo. Las réplicas de `test` remuestrean partidas, no ajustes, así que no miden la variación por semilla |
| Instrumentos de explicabilidad: coeficientes, permutación agrupada, ablaciones y SHAP (IV-E) | Ablaciones (rama 04) y SHAP; coeficientes y permutación agrupada no están en el plan | Queda para decidir en `06PendientesDelArticulo` |
| Ablación del bloque de contexto de mazo (IV-D1) | H2 restringido; la variante de 64 características no se ejecutó | Documentado en el plan |
| Escenario C reserva mazos | Reserva arquetipos por Pokémon principal | Documentado en el diccionario |

## 10. Almacenamiento

Los resultados se generan en celdas de `notebooks/06_evaluacion_final.ipynb` bajo `evaluacion_final/` y se publican en `adrielchavessalazar/ptcg-wp-tablas` con `store.asegurar`. No se versionan en Git. El cuaderno con salidas sí se versiona, como evidencia de la entrega.
