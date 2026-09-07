# Eje B — Qué responde cada paper y qué hay que garantizar al escribir

**Adriel S. Chaves Salazar · Eje B: técnicas y evaluación**

---

## Antes de nada: una advertencia sobre precisión

Este documento y los resúmenes por paper contienen **anclas de sección** (`[§3.1]`, `[Tabla V]`). Sirven para encontrar rápido dónde el paper dice cada cosa.

**Verifique cada ancla contra el PDF publicado antes de citarla en el artículo.** La numeración de secciones puede diferir entre la versión de preprint y la publicada, y una atribución equivocada es tan penalizable como una referencia inventada.

**El contenido de las afirmaciones sí es fiable** — sale del texto de cada paper. **La ubicación exacta hay que confirmarla.** Es media hora de trabajo para los once y elimina el riesgo por completo.

---

## Parte 1 — Qué responde cada paper

### Los 7 principales

---

#### 1. Borisov et al. 2024 — *¿Qué familia de modelos sirve para datos tabulares?*

**La idea general.** Es un survey que revisa toda la literatura de deep learning para datos tabulares, la organiza en una taxonomía, y después hace algo que el campo no tenía: **compara esos métodos contra los clásicos bajo un protocolo idéntico**, sobre cinco datasets.

**La respuesta que da.** Los ensembles de árboles con boosting siguen obteniendo los mejores puntajes en todos los datasets menos el más grande. La pregunta de si el deep learning actual es beneficioso para datos tabulares **se responde en general de forma negativa**, en particular para datasets heterogéneos pequeños.

**Lo que aporta que nadie más aporta.** La **taxonomía** de los tres enfoques de deep learning tabular —transformación de datos, arquitecturas especializadas, regularización— y el único benchmark del bundle que reporta **AUC**, que es nuestra métrica principal.

**Su rol en nuestro artículo.** Es el survey del Eje B. Sostiene la justificación técnica del track.

---

#### 2. Grinsztajn et al. 2022 — *¿Por qué ganan los árboles?*

**La idea general.** Construyen un benchmark de 45 datasets y después hacen lo que ningún otro paper había hecho: **deforman los datos a propósito** —los suavizan, les quitan columnas, los rotan— para descubrir qué propiedad de los datos tabulares le da ventaja a los árboles.

**Las tres respuestas que da.**

1. Las funciones objetivo tabulares **son irregulares**, y las redes están sesgadas hacia funciones suaves. Los árboles aprenden funciones constantes por tramos y no tienen ese sesgo.
2. Los datos tabulares tienen **muchas columnas no informativas**, y las redes tipo MLP no las toleran bien.
3. Las columnas tabulares **significan algo individualmente**. Un modelo invariante por rotación desperdicia esa información.

**Lo que aporta que nadie más aporta.** El **mecanismo**. Borisov constata que los árboles ganan; este explica por qué, y las tres razones son verificables contra nuestro dominio.

**Su rol en nuestro artículo.** Responde la parte del enunciado que pide **los supuestos bajo los que funcionan los métodos**.

---

#### 3. Brill et al. 2026 — *¿Qué tan difícil es estimar probabilidad de victoria?*

**La idea general.** Como la probabilidad verdadera de victoria es inobservable en la vida real, **inventan un juego tan simple que se puede calcular exactamente**: una caminata aleatoria con reglas de fútbol. Con la verdad conocida, miden qué tan lejos queda un estimador entrenado sobre datos correlacionados.

**Las respuestas que da.**

- Cuando las filas del mismo partido comparten el mismo resultado, **el sesgo y la varianza del estimador se inflan**.
- El **tamaño de muestra efectivo** del dataset de fútbol es el 56 % del nominal — están ajustando con la mitad de los datos que sugiere el conteo de jugadas.
- Conviene usar **todas** las filas pese a la dependencia: revelan la estructura del espacio de covariables.
- El sesgo es **peor al principio del partido**.
- Los intervalos de confianza por bootstrap **subcubren**, incluso el que agrupa por partido.

**Lo que aporta que nadie más aporta.** Es **el único paper del bundle sobre nuestra tarea exacta**, con nuestra misma estructura de datos. Y declara explícitamente que su resultado aplica a cualquier dataset donde el resultado es el desenlace final de una unidad y las observaciones son las unidades que llevan a él.

**Su rol en nuestro artículo.** Ancla del argumento de dependencia. Justifica el conteo por episodios y el bootstrap agrupado.

---

#### 4. Figueiredo & Mendes 2024 — *¿Cuánto infla las métricas una partición mal hecha?*

**La idea general.** En datasets de imágenes extraídas de video, los fotogramas de una misma escena son casi idénticos. Los autores comparan repartirlos al azar contra agruparlos por escena, y **miden la diferencia en las métricas reportadas**.

**La respuesta que da.** El split aleatorio infla el desempeño entre **14 % y 40 %** según la métrica, frente a la partición agrupada de referencia. Y la inflación crece de forma ordenada conforme aumenta la fuga: más fuga, más inflación.

**Lo que aporta que nadie más aporta.** Brill mide el daño **hacia adentro** —sesgo, varianza—. Este lo mide **hacia afuera**: cuánto sube el número que uno publica. Son complementarios.

**Su rol en nuestro artículo.** Da la magnitud esperada de la inflación y respalda presentar evidencia medida por cada vector de riesgo en la §9.2.

---

#### 5. Silva Filho et al. 2023 — *¿Cómo se evalúa la calidad de una probabilidad?*

**La idea general.** Un survey completo de calibración: qué es, cómo se mide, qué métodos existen para corregirla.

**Las respuestas que da.**

- Un modelo calibrado es aquel cuyas probabilidades predichas **coinciden con las frecuencias observadas**.
- Las reglas de puntuación propias —Brier, log-loss— **se descomponen** en un componente de calibración y uno de refinamiento.
- Los estimadores de calibración basados en binning **dependen del número y tipo de cajas**, con un compromiso sesgo-varianza.
- Existen métodos de recalibración post-hoc con supuestos distintos: Platt, isotónica, beta.
- La recalibración **debe ajustarse sobre datos no vistos en entrenamiento**.

**Lo que aporta que nadie más aporta.** La **descomposición**. Es lo que convierte nuestra lista de métricas en un argumento: ninguna métrica sola distingue las dos formas de fallar.

**Su rol en nuestro artículo.** Segundo survey del bundle. Ancla del bloque de calibración y sustento formal de la §15.

---

#### 6. Niculescu-Mizil & Caruana 2005 — *¿Estará calibrado nuestro modelo?*

**La idea general.** Examinan las probabilidades de diez algoritmos sobre ocho problemas binarios, describen la distorsión característica de cada familia, y evalúan dos métodos de corrección.

**Las respuestas que da.**

- Los métodos de máximo margen —**incluido boosting**— empujan las probabilidades lejos de 0 y 1, produciendo **distorsión sigmoidea**.
- Naive Bayes distorsiona en sentido contrario.
- **Redes neuronales, bagged trees y regresión logística ya están bien calibrados**, y recalibrarlos puede perjudicarlos.
- Los métodos que promedian tienen dificultad estructural para predecir cerca de los extremos.
- Con menos de ~1.000 casos de calibración, Platt supera a la isotónica; **con 1.000 o más, la isotónica siempre iguala o supera a Platt**.
- **El ranking de modelos cambia** antes y después de calibrar.

**Lo que aporta que nadie más aporta.** Una **predicción concreta y falsable sobre nuestro B4**. Sin este paper, la calibración es una preocupación genérica; con él, es específica del modelo que vamos a usar.

**Su rol en nuestro artículo.** Justifica medir calibración en nuestros modelos concretos, y da el criterio para elegir el método de corrección.

---

#### 7. Xenopoulos et al. 2022 — *¿Importa la calibración en la práctica, en un juego?*

**La idea general.** Entrenan modelos de probabilidad de victoria de ronda en CSGO sobre tres entornos de habilidad distinta, y **prueban cada modelo en los tres**, midiendo log loss y ECE.

**Las respuestas que da.**

- Los modelos están **bien calibrados en sus respectivos entornos**.
- El modelo entrenado en el entorno casual tuvo **mayor log loss y estuvo menos calibrado** en los entornos profesionales.
- **La importancia de las características difiere entre niveles de habilidad.**
- Eligen su ventana de datos porque **no hubo actualizaciones a los mapas ni a las armas**.

**Lo que aporta que nadie más aporta.** Es el **puente entre el bloque metodológico y el dominio**: demuestra que la preocupación por la calibración no es teórica, y que en un juego competitivo real la calibración se degrada bajo cambio de población mientras el log loss apenas se mueve.

**Su rol en nuestro artículo.** Precedente de dominio para medir ECE, y evidencia empírica para el protocolo temporal de la §13.2.

---

### Los 4 adicionales

| Paper | Qué responde | Rol |
|---|---|---|
| **Hodge et al. 2021** | ¿Se ha hecho predicción de victoria en vivo en un juego? | Precedente de dominio. Aporta el split cronológico y el problema de los parches. **Eje A — Daniel lo defiende con profundidad** |
| **Saravanan & Guzdial 2024** | ¿Por qué cambia la población de estrategias con el tiempo? | Formaliza el metajuego. **Es Pokémon Showdown, no el juego de cartas.** Eje A/C |
| **Ojeda et al. 2023** | ¿Qué método de recalibración usar? | Instrumental. Se cita en la metodología |
| **Dimitriadis et al. 2021** | ¿Cómo medir calibración sin artefactos de binning? | Instrumental. Se cita al describir las curvas |

---

## Parte 2 — Qué hay que garantizar escribir, siempre

Cada regla nace de un paper concreto. **Si alguna se rompe, el artículo dice algo que la literatura citada contradice.**

---

### 🔴 Reglas de honestidad — romperlas es una atribución incorrecta

#### R1. Nunca reportar el conteo de filas solo

**Siempre:** *"7.038.378 snapshots provenientes de 52.085 episodios."*
**Nunca:** *"un dataset de 7 millones de observaciones."*

**Por qué.** Brill muestra que cuando las filas de una misma unidad comparten el desenlace, el tamaño de muestra efectivo es una fracción del nominal — 56 % en su caso de fútbol. Reportar solo las filas transmite una idea falsa de cuánta evidencia hay.

**Fuente:** Brill et al. 2026.

---

#### R2. Declarar la brecha de dominio de los análogos

**Siempre que citemos Figueiredo:** decir que es **visión por computadora**, detección de objetos en video.
**Siempre que citemos Brill:** decir que es un **estudio de simulación** calibrado sobre fútbol americano.
**Siempre que citemos Saravanan:** decir que es **Pokémon Showdown, el videojuego, no el juego de cartas**.

**Por qué.** Son análogos metodológicos. Presentarlos como resultados sobre datos de juegos de cartas es atribuir a un paper algo que no dice.

**Matiz importante:** Brill **sí declara explícitamente** que su resultado aplica a cualquier dataset donde grupos de observaciones comparten el desenlace. Eso significa que **no tenemos que argumentar la transferencia** — pero sí tenemos que decir de dónde viene el estudio.

---

#### R3. Nunca afirmar que nadie mide calibración

**Nunca:** *"ningún trabajo previo evalúa la calidad de las probabilidades."*
**Sí:** *"la calibración se ha medido en predicción de victoria en esports [Xenopoulos], pero no en juegos de cartas coleccionables ni bajo cambio temporal de la población."*

**Por qué.** Xenopoulos mide ECE explícitamente. Afirmar el vacío absoluto sería contradicho por un paper de nuestra propia bibliografía.

**Fuente:** Xenopoulos et al. 2022.

---

#### R4. El baseline de literatura no es directamente comparable

**Siempre:** declarar que el número de referencia viene de **Hearthstone**, otro juego, con otras reglas, y que sirve como orden de magnitud y no como cifra a batir.

**Por qué.** El enunciado exige declarar qué diferencias de protocolo impedirían una comparación justa. Y Hodge da el precedente de cómo se hace: publica una tabla comparativa de 16 trabajos **y advierte en la nota al pie que los datasets varían y que comparar exactitud requiere cautela**.

**Fuente:** Hodge et al. 2021.

---

#### R5. Declarar el incumplimiento de las versiones del motor

**Siempre en la §13.2:** decir que nuestro dataset abarca **seis versiones del motor**, y que eso confunde la deriva temporal con el cambio técnico.

**Por qué.** Tres papers de dominio controlaron explícitamente esa variable: Hodge declara que durante su recolección no hubo cambios en las mecánicas centrales; Xenopoulos elige su ventana porque no hubo actualizaciones de mapas ni armas; Saravanan toma tres meses antes y después de un evento identificable. **Es una práctica estándar del dominio que nosotros no podemos cumplir**, y omitirlo sería ocultar una limitación conocida.

**Fuentes:** Hodge 2021, Xenopoulos 2022, Saravanan & Guzdial 2024.

---

### 🟡 Reglas de argumento — romperlas debilita la defensa técnica

#### R6. Justificar el track con literatura, nunca con opinión

**Siempre:** la elección de modelos tabulares clásicos se sostiene sobre **Borisov** (el resultado y la taxonomía) y **Grinsztajn** (el mecanismo).

**Nunca:** *"elegimos árboles porque funcionan bien con datos tabulares"* sin cita.

**Por qué.** El enunciado dice literalmente que aquí se justifica técnicamente el track **con literatura, no con opinión**.

---

#### R7. Declarar la excepción de los datasets grandes, y responderla

**Siempre:** mencionar que Borisov encuentra que en el dataset más grande —11 millones de muestras, casi todas variables continuas— un modelo neuronal supera a los clásicos, y responder con nuestra distinción: **nuestras filas no son observaciones independientes**, salen de 52.085 episodios, y nuestras variables son heterogéneas.

**Por qué.** Si alguien conoce el paper, esa es la objeción. Declararla nosotros y responderla vale más que omitirla.

**Fuente:** Borisov et al. 2024.

---

#### R8. Declarar los criterios de exclusión de Grinsztajn

**Siempre:** al citar Grinsztajn, mencionar que su benchmark excluye datasets con datos faltantes, categóricas de más de 20 valores, datos no i.i.d., y datasets deterministas de juegos.

**Y responder cada uno:**

| Ellos excluyen | Nuestra respuesta |
|---|---|
| Juegos deterministas | Nuestro resultado **no** es determinista dado el estado: depende del orden del mazo, la mano oculta y las decisiones futuras. Por eso estimamos una probabilidad |
| Datos no i.i.d. | Nuestra unidad independiente es el **episodio**, no la fila. Por eso agrupamos |
| Datos faltantes | Los tenemos, y es una diferencia de régimen que declaramos |
| Categóricas de alta cardinalidad | Las tenemos. Los propios autores lo listan como trabajo futuro |

**Por qué.** El criterio de exclusión de juegos es la objeción más directa que puede recibir el Eje B.

**Fuente:** Grinsztajn et al. 2022.

---

#### R9. Reportar siempre discriminación y calibración por separado

**Siempre:** AUC y ECE juntos, en cada protocolo, sin promediarlos ni elegir uno.

**Por qué, con dos razones independientes:**

- **Formal:** las reglas de puntuación propias se descomponen en calibración y refinamiento. El AUC solo mide el orden; el ECE solo la calibración. Ninguna sola distingue las dos formas de fallar.
- **Empírica:** en Xenopoulos, el modelo del entorno casual evaluado fuera de su entorno subió su log loss de 0,456 a 0,470 mientras su ECE pasó de 0,004 a 0,033. **La calibración se degradó mucho más que la discriminación.**

**Fuentes:** Silva Filho 2023, Xenopoulos 2022.

---

#### R10. No poner papers metodológicos en la tabla comparativa

**Van en la tabla:** Hodge, Xenopoulos, Saravanan — resuelven una tarea sobre un dataset y reportan una métrica.

**No van:** Borisov, Grinsztajn, Brill, Figueiredo, Silva Filho, Niculescu-Mizil, Ojeda, Dimitriadis.

**Por qué.** Las columnas obligatorias incluyen dataset, métrica principal y resultado reportado. Un survey de calibración no tiene esos campos, y llenarlos obligaría a inventar valores.

---

### 🟢 Reglas de anticipación — escribirlas antes de tener los resultados

#### R11. Anticipar que el split agrupado dará métricas peores y más ruidosas

**Siempre en la §13.1 o en la discusión:** declarar que se espera menor desempeño y mayor varianza con la partición agrupada, y que **eso es el comportamiento correcto**, no un protocolo mal calibrado.

**Por qué.** Figueiredo lo documenta: con las técnicas de menor fuga, las pérdidas de entrenamiento son más altas y la varianza entre corridas es mayor.

**Y por qué escribirlo antes:** porque cuando lleguen los números en la Etapa 2, la tentación de aflojar el protocolo va a ser real. Dejarlo escrito protege la decisión.

**Fuente:** Figueiredo & Mendes 2024.

---

#### R12. Anticipar que recalibrar no mejorará el AUC

**Siempre en la §15:** declarar que la recalibración actúa sobre el componente de calibración y **no se espera que mejore el AUC**.

**Por qué.** Se sigue de la descomposición: el AUC mide orden, y una recalibración monótona no cambia el orden. Si no está anticipado, un AUC que no se mueve va a leerse como que la recalibración no sirvió.

**Fuente:** Silva Filho 2023.

---

#### R13. Medir calibración antes de decidir recalibrar

**El pipeline no puede ser** entrenar → recalibrar → evaluar.
**Tiene que ser** entrenar → medir calibración → decidir → volver a medir.

**Por qué.** Niculescu-Mizil muestra que recalibrar un modelo ya bien calibrado puede perjudicarlo, y predice que la regresión logística —nuestro B2— estará bien calibrada de fábrica. Aplicar recalibración de forma uniforme empeoraría ese modelo.

**Y reportar las dos mediciones**, porque el ranking de modelos cambia entre antes y después de calibrar.

**Fuente:** Niculescu-Mizil & Caruana 2005.

---

## Parte 3 — Lo que queda pendiente

Tres cosas abiertas, en orden de urgencia.

**🔴 Falta el conjunto de calibración.** Nuestra §13.1 define tres particiones. Silva Filho y Niculescu-Mizil exigen, cada uno por su lado, que la recalibración se ajuste sobre datos no vistos en entrenamiento. Hay que decidir entre una cuarta partición o validación cruzada agrupada por `episode_id`, **antes** de empezar la Etapa 2.

**🟡 Hay una tensión sin resolver entre Niculescu-Mizil y Ojeda.** El primero recomienda regresión isotónica cuando hay más de 1.000 casos de calibración; el segundo recomienda calibración logística y beta, que son métodos paramétricos. Puede que Ojeda evalúe sobre todo **transferencia a poblaciones externas** —que es la situación de nuestra §13.2— y que ahí los paramétricos transfieran mejor. Media hora leyendo su sección de resultados lo resuelve.

**🟢 Verificar las anclas de sección.** Como se dijo al inicio: el contenido es fiable, la ubicación hay que confirmarla contra el PDF publicado antes de citarla.