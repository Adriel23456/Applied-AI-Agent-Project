# Resultados de la evaluación final (`05FinalModelChecks`)

Fecha: 4 de noviembre de 2026.
Participantes: Sebastián Hernández Bonilla y asistente de IA (Claude) en la redacción; Adriel S. Chaves Salazar en la ejecución.

**Fuente única de las cifras:** las salidas guardadas de `notebooks/06_evaluacion_final.ipynb` (commit `c16afe5`) y los archivos `evaluacion_final/` del dataset de Kaggle. Aquí no se recalculó nada. Las reglas de decisión son las de `02-11-26_ProtocoloEvaluacionFinal.md`.

**Comprobación pendiente:** la procedencia de `test`. Hay que confirmar en `evaluacion_final/test/registro_{A,B,C}.json` y en el índice del dataset:

- `protocolo_sha256 = 365fcceaff8bd188580b45705cb0303d321041af329eb6d9faa459b65b20a94f`;
- el commit es `b6e6607` o `71c952b`;
- `working_tree_dirty = false`;
- las publicaciones de `test/` y `curvas/` son posteriores a 2026-11-03T04:30Z.

Mientras eso no se confirme, estas cifras se tratan como resultados por validar.

Todos los intervalos son percentiles del 95 % con 1000 remuestreos de partidas. Son individuales por escenario, no simultáneos, y no incluyen la incertidumbre de la búsqueda ni del ajuste.

## 1. Verificación previa

- Las 109 pruebas pasaron en Colab.
- Las predicciones del cuaderno reproducen las métricas de `val` publicadas por las ramas anteriores: log loss y Brier con diferencia ≤ 4.4e-16, y AUC ≤ 4.8e-7. En B3 la diferencia de AUC fue ≤ 3.3e-7, así que el efecto de los empates en su AUC es despreciable con los datos reales.
- La revisión de fuga se aprobó antes de abrir `test` (sección 6).

## 2. Desempeño en `test` y comparación con las referencias

AUC global (intervalo):

| Modelo | A | B | C |
|---|---|---|---|
| B0 | 0.5000 | 0.5000 | 0.5000 |
| B1 | 0.6829 [0.6738, 0.6914] | 0.7180 [0.7112, 0.7256] | 0.7051 [0.6969, 0.7131] |
| B2 | 0.7615 [0.7544, 0.7682] | 0.7459 [0.7395, 0.7530] | 0.7512 [0.7446, 0.7578] |
| B3 | 0.8037 [0.7981, 0.8091] | 0.7707 [0.7652, 0.7773] | 0.7673 [0.7613, 0.7734] |
| **B4** | **0.8327 [0.8270, 0.8379]** | **0.7889 [0.7839, 0.7945]** | **0.7872 [0.7817, 0.7930]** |

Otras cifras de B4:

| | A | B | C |
|---|---|---|---|
| Log loss | 0.4944 | 0.5509 | 0.5501 |
| Brier | 0.1660 | 0.1877 | 0.1880 |
| AUC inicio / medio / final | 0.6835 / 0.8275 / 0.9365 | 0.6298 / 0.7738 / 0.9149 | 0.6227 / 0.7872 / 0.9187 |

**Comparación emparejada (AUC de B4 menos la referencia):**

| Referencia | A | B | C |
|---|---|---|---|
| B0 | +0.3327 | +0.2889 | +0.2872 |
| B1 | +0.1499 [0.1415, 0.1591] | +0.0709 [0.0650, 0.0762] | +0.0821 [0.0755, 0.0889] |
| B2 | +0.0712 [0.0664, 0.0760] | +0.0430 [0.0385, 0.0473] | +0.0360 [0.0318, 0.0401] |
| B3 | +0.0291 [0.0265, 0.0315] | +0.0182 [0.0152, 0.0207] | +0.0198 [0.0176, 0.0221] |

Ninguna diferencia, en ninguna métrica ni escenario, tiene un intervalo que incluya 0. B4 también es mejor en log loss y en Brier. La escalera se mantiene en `test`: cada peldaño supera al anterior en los tres escenarios.

- **Criterio interno del artículo (III-D):** se cumple en los tres escenarios. El límite inferior del AUC de B4 queda sobre el superior de B1: A 0.8270 > 0.6914, B 0.7839 > 0.7256, C 0.7817 > 0.7131.
- **Literatura (AUC 0.78–0.80, orden de magnitud):** en la etapa final de A, B4 llega a 0.9365 [0.9320, 0.9407]. La curva por turno pasa de 0.58 en el turno 1 a 0.78 en el turno 7, el primero que alcanza la banda, y ronda 0.92 desde el turno 15. No es una comparación estricta: juego, población, partición y construcción del vector son distintos (Sección III-C).
- **De `val` a `test`:** A pasa de 0.8346 a 0.8327 y B de 0.7863 a 0.7889. En C el AUC baja de 0.8355 a 0.7872. Es lo esperado: `val` de C son partidas al azar de arquetipos conocidos y `test` son arquetipos reservados. Es una diferencia descriptiva entre conjuntos distintos, no una prueba emparejada.

## 3. Curvas de aprendizaje y sobreajuste

AUC en `val` según la fracción de partidas de `train`:

| Escenario | 25 % | 50 % | 75 % | 100 % |
|---|---|---|---|---|
| A | 0.8188 | 0.8281 | 0.8314 | 0.8346 |
| B | 0.7788 | 0.7843 | 0.7848 | 0.7863 |
| C | 0.8221 | 0.8295 | 0.8318 | 0.8355 |

Brecha de AUC `train − val`, de 25 % a 100 %: A 0.037 → 0.034, B 0.091 → 0.088, C 0.044 → 0.034.

- **Más datos ayudan poco.** El último 25 % suma 0.0032 en A, 0.0015 en B y 0.0037 en C. Ampliar el corpus traería ganancias marginales.
- **No hay sobreajuste creciente.** En A y C la brecha es estable, entre 0.03 y 0.04, y no aumenta con los datos. El AUC de `train` se mide en las mismas 5000 partidas usadas para entrenar, así que la brecha incluye el optimismo normal de medir dentro de la muestra.
- **La brecha de B no es sobreajuste.** Es de unos 0.09 y no cambia con el tamaño: viene del cambio temporal entre los días de `train` y `val`. Agregar partidas del periodo temprano no la reduce (+0.0015).

## 4. Calibración

Los métodos se eligieron dentro de `calib`, con validación cruzada por partida y antes de abrir `test`:

- **A:** B2 Platt, B3 Platt, B4 sin corrección.
- **B:** B2 isotónica, B3 Platt, B4 isotónica.

Resultados en `test`, antes → después del método elegido:

| Escenario y modelo | Log loss | Brier | ECE | Lectura |
|---|---|---|---|---|
| A · B4 (sin corrección) | 0.4944 | 0.1660 | 0.0020 | Ya calibrado; la isotónica empeora un poco (log loss 0.4951) |
| A · B3 (Platt) | 0.5340 → 0.5308 | 0.1806 → 0.1797 | 0.0298 → 0.0079 | Mejora |
| A · B2 (Platt) | 0.5783 → 0.5781 | 0.1973 → 0.1975 | 0.0112 → 0.0158 | Sin efecto útil |
| B · B4 (isotónica) | 0.5509 → 0.5467 | 0.1877 → 0.1865 | 0.0367 → 0.0179 | Mejora; el AUC no cambia (0.7889 → 0.7888) |
| B · B3 (Platt) | 0.5643 → 0.5683 | 0.1934 → 0.1947 | 0.0127 → 0.0338 | **Empeora** |
| B · B2 (isotónica) | 0.6013 → 0.5999 | 0.2053 → 0.2063 | 0.0363 → 0.0442 | Mixto |

Lectura:

- **Dentro de su población, B4 sale calibrado.** No se observa la distorsión que Niculescu-Mizil y Caruana describen para el boosting.
- **Con cambio temporal, B4 se vuelve sobreconfiado.** En el diagrama de B, donde predice cerca de 0.87 se observa alrededor de 0.80. La isotónica ajustada el 11 de julio corrige buena parte en los días 15 y 22.
- **Recalibrar con un día intermedio no es fiable en general:** a B3 lo empeoró en `test`. Corregir la probabilidad bajo deriva es frágil y depende del modelo.
- **Platt no tuvo ventaja sobre la isotónica en B4 de B** (log loss 0.5469 contra 0.5467), así que la recomendación de Ojeda et al. no se distingue aquí.
- **Para la Etapa 3:** el modelo final (B4 de A) se usa sin calibrador, como decidió `calib`.

## 5. Análisis de errores

Las tasas son la fracción de todos los estados del grupo, con cada partida pesando lo mismo. El umbral para falso positivo y negativo es 0.5, y "muy segura" significa p ≥ 0.9 o p ≤ 0.1.

| Escenario | Falsos positivos / negativos (global) | En la etapa inicio | Muy seguras y equivocadas (p ≥ 0.9 con derrota / p ≤ 0.1 con victoria) | Acierto de las muy seguras: global, inicio, final |
|---|---|---|---|---|
| A | 0.139 / 0.117 | 0.218 / 0.153 | 0.0053 / 0.0043 | 0.958, 0.898, 0.977 |
| B | 0.164 / 0.129 | 0.244 / 0.161 | 0.0089 / 0.0058 | 0.930, 0.797, 0.965 |
| C | 0.165 / 0.132 | 0.247 / 0.167 | 0.0083 / 0.0060 | 0.933, 0.829, 0.964 |

- **Al inicio el modelo sobreestima la victoria de quien actúa.** Los falsos positivos superan a los falsos negativos en los tres escenarios, y la diferencia se cierra en la etapa final.
- **Los errores muy seguros son raros** (menos del 1 % de los estados), pero su frecuencia sube fuera de la población de entrenamiento. En la etapa inicio de B, solo el 80 % de las predicciones muy seguras acierta.
- **Perfil de los errores muy seguros frente a los aciertos muy seguros.** Las diferencias son pequeñas, nunca mayores que 0.3 desviaciones estándar, así que ninguna característica sola los explica.
  - En A tienen menos energías unidas (2.68 contra 3.33).
  - En B y C quedan más premios propios por tomar (4.4 contra 3.9 en B) y hay menos descartes: son estados menos avanzados.
  - En C ocurren en turnos más tempranos (9.1 contra 10.5).
- **Implicación:** una probabilidad extrema en los primeros turnos merece menos confianza, sobre todo fuera de la población de entrenamiento.

## 6. SHAP y revisión de fuga

Modelo B4 de A (`modelo_final/`), sobre una muestra de partidas completas de `val` de A.

- **Por familia:** recursos y tablero 72.8 %, diferenciales 20.9 %, progreso 6.3 %.
- **Principales características:**

  | Característica | Fracción |
  |---|---|
  | `diff_prizes` | 0.113 |
  | `own_discard` | 0.082 |
  | `opp_discard` | 0.077 |
  | `own_prizes` | 0.047 |
  | `opp_active_max_hp` | 0.044 |
  | `own_active_max_hp` | 0.044 |
  | `opp_deck` | 0.039 |
  | `opp_prizes` | 0.034 |
  | `own_active_evolved` | 0.031 |

- **Por etapa:** el peso de `diff_prizes` sube de 0.057 en inicio a 0.136 en medio y 0.149 en final, y el de `own_prizes` de 0.035 a 0.074. Al inicio dominan los descartes (0.104 y 0.093).
- **Revisión de fuga, aprobada:**
  - ninguna columna prohibida;
  - la característica más importante concentra 0.113, por debajo del límite de 0.5;
  - la mejor característica sola llega a un AUC de 0.690 (`diff_prizes`), por debajo de 0.85.

  Las variables dominantes son información pública del tablero.

**Hallazgos accionables:**

1. **El modelo evalúa por balance de recursos.** Premios, descartes y mazo explican la mayor parte de la predicción. Las explicaciones que muestre el agente de la Etapa 3 pueden expresarse en esos términos.
2. **Quedarse sin mazo es la señal más fuerte cuando aparece.** Con `opp_deck` muy bajo, la contribución llega a unos +4 a +6 en logit. Coincide con que casi ninguna partida termina por premios (sección 7 del diccionario). Un agente que use este evaluador tenderá a valorar el agotamiento del mazo rival. Es legítimo por reglas, y conviene comprobarlo en la Etapa 3.
3. **Los descartes funcionan como contador del material perdido.** Un descarte propio alto resta y uno rival alto suma.
4. **Un activo rival con muchos PV máximos aumenta la probabilidad propia, y el efecto inverso aparece en el activo propio.** Es una hipótesis, no un resultado verificado: puede reflejar el valor en premios de los Pokémon "ex", que entregan dos premios y que solo se reconocen por sus PV máximos (sección 7 del diccionario). Una característica explícita de "premios que entrega el activo" es una extensión candidata. No se implementa en la Etapa 2.
5. **El progreso pesa poco (6.3 %).** El aumento de la capacidad predictiva con la partida (H1) no se explica por contar turnos, sino por cómo cambia el tablero.

## 7. Hipótesis

### H1: sostenida en A, B y C

| | A | B | C |
|---|---|---|---|
| AUC en inicio, todas las partidas | 0.6835 [0.6742, 0.6912] | 0.6298 [0.6223, 0.6384] | 0.6227 [0.6145, 0.6312] |
| Partidas en la cohorte | 6 839 | 8 269 | 7 412 |
| Cohorte: inicio → medio → final | 0.6195 → 0.7943 → 0.9365 | 0.5896 → 0.7385 → 0.9149 | 0.5907 → 0.7560 → 0.9187 |
| Final − inicio | 0.3170 [0.3075, 0.3268] | 0.3253 [0.3158, 0.3351] | 0.3280 [0.3182, 0.3374] |

La señal temprana supera claramente al azar, y crece con la partida incluso dentro de la cohorte de partidas que llegan a las tres etapas, lo que controla la duración.

### H2: mixta, refutada en el escenario principal

| Escenario | AUC B4 en inicio | AUC H2 en inicio | Diferencia [IC] | Resultado |
|---|---|---|---|---|
| A | 0.6835 | 0.6816 | 0.0018 [−0.0076, 0.0112] | **Refutada** |
| B | 0.6298 | 0.5892 | 0.0406 [0.0314, 0.0505] | Sostenida |
| C | 0.6227 | 0.5347 | 0.0879 [0.0767, 0.0989] | Sostenida |

- **En A**, dentro de la población conocida, la señal temprana del estado completo **no se distingue** de la del modelo con solo turno, primer jugador e identidad de los Pokémon activos. Al inicio, lo que el modelo sabe equivale al emparejamiento y al orden de turno. Con la regla del artículo, H2 queda refutada en el protocolo principal.
- **Más adelante el estado completo domina:** en la etapa final de A, H2 vale 0.7694 y B4 0.9365.
- **En B y C la identidad pierde valor y el estado no.** Con un periodo nuevo o arquetipos nuevos, el modelo restringido cae a 0.589 y 0.535 en inicio, mientras B4 se mantiene en 0.630 y 0.623. El aporte del estado aparece al cambiar la población. No es un artefacto evidente de ids desconocidos: el diccionario reporta cartas activas no vistas en ≤ 1.2 % de las filas en B y 0.061 % en C. La fracción exacta en `test` está en `registro_{B,C}.json` y debe citarse al confirmarla.
- **Límite:** los ids de los activos aproximan la identidad del mazo, pero no la describen completa.

### H3: refutada

**Diseño emparejado:** 1 405 partidas que son `test` en A y en B (días 15 y 22 de julio). El modelo de A, que no tiene brecha temporal, se compara con el de B, entrenado solo con días anteriores.

| Medida (B − A) | Valor | IC |
|---|---|---|
| ΔAUC | −0.0270 | [−0.0331, −0.0210] |
| Δlog loss | +0.0377 | [0.0300, 0.0452] |
| ΔBrier | +0.0139 | [0.0110, 0.0168] |
| Calibración perdida (ΔMCB), log loss | 0.0083 | [0.0049, 0.0118] |
| Ordenamiento perdido (ΔDSC), log loss | 0.0295 | [0.0233, 0.0358] |
| Contraste, log loss | −0.0212 | [−0.0279, −0.0152] |
| Calibración perdida (ΔMCB), Brier | 0.0024 | [0.0015, 0.0034] |
| Ordenamiento perdido (ΔDSC), Brier | 0.0116 | [0.0091, 0.0140] |
| Contraste, Brier | −0.0092 | [−0.0117, −0.0070] |

- **La calibración sí se degrada,** pero el ordenamiento pierde entre 3.5 y 4.9 veces más en las mismas unidades del puntaje. H3 queda refutada: aquí no se reproduce la asimetría que reportan Guo et al. y Xenopoulos et al.
- **La comparación directa habría dicho lo contrario.** La habilidad en log loss cae 22.9 % y la de AUC 8.9 %. Esa diferencia es un efecto de escala, y es la razón por la que el protocolo decide con la descomposición.
- **No hay un "antes" visible.** Por día, el modelo de B no empeora de forma progresiva:

  | Día | AUC | MCB del log loss |
  |---|---|---|
  | 7 jul | 0.7863 | 0.0104 |
  | 11 jul | 0.7752 | 0.0137 |
  | 15 jul | 0.7917 | 0.0056 |
  | 22 jul | 0.7856 | 0.0069 |

- **El tamaño de entrenamiento explica poco.** A entrena con 33 066 partidas y B con 27 643. En las curvas, pasar de 75 a 100 % suma ≤ 0.004 de AUC, muy por debajo de 0.027.

## 8. Limitaciones

- Una sola semilla. La variación por ajuste no está medida.
- Los intervalos no son simultáneos y pueden ser optimistas (Brill et al.).
- Calendario y versión del motor siguen confundidos en B.
- La población es de agentes automáticos de una franja de puntuación, en diez días.
- Del plan de explicabilidad del artículo (IV-E) no se ejecutaron los coeficientes de B2 ni la importancia por permutación agrupada.
- Los estados ya resueltos y la preparación están excluidos.
- La procedencia de `test` está pendiente de la confirmación indicada arriba.

## 9. Texto propuesto para `PlanDeDesarrollo.md`

Se marca **después** de confirmar la procedencia de `test`.

- [ ] **Evaluación única en `test`.** A, B y C por separado. B4: AUC A 0.833, B 0.789, C 0.787. Resultados en `evaluacion_final/test/`.
- [ ] **Métricas globales y por etapa.** Intervalos de 1000 remuestreos de partidas, en `evaluacion_final/test/metricas_X.csv`.
- [ ] **Comparación con las referencias.** B4 supera a B0, B1, B2 y B3 en los tres escenarios, con intervalos que excluyen 0. La etapa final de A llega a 0.936, por encima de la banda de literatura (orden de magnitud). Se cumple el criterio de B1 (III-D). Archivos `comparaciones_X.csv` y `referencias.json`.
- [ ] **Curvas de aprendizaje.** El último 25 % suma ≤ 0.004 de AUC en `val`. Brecha `train − val` estable (A y C ≈ 0.034; B ≈ 0.09, por el cambio temporal). Sin sobreajuste creciente. Archivos en `evaluacion_final/curvas/`.
- [ ] **Errores.** Al inicio hay más falsos positivos que negativos. Los errores muy seguros son menos del 1 %, más frecuentes fuera de la población. Archivos en `evaluacion_final/errores/`.
- [ ] **SHAP.** Revisión de fuga aprobada. Dominan premios, descartes y mazo; hallazgos en `docx/03Evidencia/04-11-26_ResultadosEvaluacionFinal.md`. Archivos en `evaluacion_final/shap/`.
- [ ] **Calibración.** B4 calibrado en A (ECE 0.002, sin corrección). En B, la isotónica baja el ECE de 0.037 a 0.018. Recalibrar B3 en B empeoró `test`. Archivos en `evaluacion_final/calibracion/`.
- [ ] **H3.** Refutada: ΔDSC del log loss 0.0295 frente a ΔMCB 0.0083, con el contraste bajo 0 en log loss y en Brier. Archivos en `evaluacion_final/hipotesis/`.
- [ ] **Veredicto.** H1 sostenida en A, B y C. H2 refutada en A y sostenida en B y C. H3 refutada. Archivo `evaluacion_final/veredicto.json`.
- [ ] **README, cuaderno y declaración de IA.** Se marca cuando no quede ningún `[COMPLETAR]` en la declaración.