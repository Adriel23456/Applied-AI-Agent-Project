# Qué estamos haciendo y por qué

**Proyecto:** Estimación de probabilidad de victoria desde el estado de juego en Pokémon TCG
**Curso:** IC-6200 Inteligencia Artificial · II Semestre 2026 · Track A
**Equipo:** Adriel S. Chaves Salazar · Daniel Duarte Cordero · Sebastián Hernández Bonilla

> Este documento explica el proyecto desde cero. No asume que usted sepa de aprendizaje automático. Asume que sabe programar, que entiende A\* y Dijkstra, y que ha visto la idea de darle pesos a distintos factores para puntuar algo. Con eso alcanza.

---

## 1. La idea en una frase

Le mostramos a un programa **una foto de una partida de Pokémon TCG a la mitad del juego** y el programa responde: *"el jugador que estoy viendo tiene un 68 % de probabilidad de ganar esta partida"*.

Eso es todo. No jugamos. No decidimos qué carta poner. Solo miramos el tablero y estimamos quién va ganando.

---

## 2. El puente con lo que usted ya sabe

Esta es la parte que hace que todo lo demás encaje.

### A\* y su heurística

En A\* usted tiene una función `h(n)` que estima cuánto falta desde el nodo `n` hasta la meta. Usted **la escribe a mano**: distancia Manhattan, distancia euclidiana, lo que sea que se le ocurra que aproxime bien.

Esa función tiene un nombre general: **función de evaluación**. Mira un estado y le pone un número que dice qué tan bueno es.

### El problema con escribirla a mano

En un laberinto la distancia Manhattan funciona porque el dominio es simple. En Pokémon TCG, ¿cómo escribiría usted `h(estado)`?

Podría intentar algo como:

```
puntaje = 3*(premios_que_me_faltan_menos) + 2*(mis_HP) + 1*(cartas_en_mano) - ...
```

Y ahí aparecen dos preguntas que no puede responder:

1. **¿De dónde salen esos números?** ¿Por qué 3 y no 5? Los estaría inventando.
2. **¿Se le olvidó algo?** ¿Importa tener energías acumuladas? ¿Importa cuántas cartas quedan en el mazo? ¿Importa el envenenamiento?

### Lo que hacemos en vez de eso

**No escribimos la función. La aprendemos de datos.**

Le damos al programa medio millón de situaciones reales de partidas donde **ya sabemos quién ganó**, y el programa encuentra solo qué combinación de pesos predice mejor el resultado.

> **Un modelo de aprendizaje automático supervisado es exactamente eso: una función de evaluación cuyos pesos se calculan a partir de ejemplos en vez de escribirse a mano.**

Si alguna vez ajustó pesos de fitness a ojo hasta que "se veía bien", esto es lo mismo — pero el ajuste lo hace un algoritmo de optimización sobre millones de ejemplos, en vez de usted sobre cinco pruebas.

---

## 3. Los datos: qué son exactamente

### De dónde salen

The Pokémon Company organiza una competencia en Kaggle donde programadores suben **bots** que juegan Pokémon TCG. Esos bots juegan entre sí miles de partidas al día, y Kaggle publica los mejores replays de cada día como un dataset.

Nosotros **no participamos en esa competencia**. Solo usamos los replays que publican.

### Qué hay adentro de un replay

Cada partida es un archivo JSON. Simplificando su estructura:

```
{
  "rewards": [1, -1],          ← quién ganó: jugador 0 ganó, jugador 1 perdió
  "steps": [
     {  paso 0: estado del tablero + qué decidió cada bot  },
     {  paso 1: estado del tablero + qué decidió cada bot  },
     {  paso 2: ...  },
     ...
  ]
}
```

Y dentro de cada paso, el estado del tablero visto por cada jugador incluye:

| Zona | Qué guarda |
|---|---|
| `active` | El Pokémon activo: HP actual, HP máximo, energías, herramientas |
| `bench` | Los Pokémon en banca, con sus mismos datos |
| `hand` | Las cartas en mano (las suyas; las del rival aparecen ocultas) |
| `prize` | Cuántas cartas premio quedan por tomar |
| `deck` | Cuántas cartas quedan en el mazo |
| `discard` | Qué se ha descartado |
| Estados alterados | Dormido, quemado, confundido, paralizado, envenenado |
| Globales | Turno actual, estadio en juego, si ya jugó supporter |

### Los dos hechos que hacen viable el proyecto

**Hecho 1: el resultado viene incluido.** El campo `rewards` dice quién ganó. Esto significa que **no tenemos que etiquetar nada a mano**. Normalmente la parte más cara de un proyecto de ML es conseguir etiquetas; aquí vienen gratis.

**Hecho 2: cada partida da cientos de ejemplos.** Un replay no es un ejemplo — es una secuencia de estados. Si una partida tuvo 140 pasos, sacamos ~140 ejemplos de esa sola partida.

Con 52.085 partidas auditadas, eso da **7.038.378 ejemplos**.

---

## 4. Cómo convertimos un replay en filas de una tabla

Aquí está la transformación central del proyecto. Va con un ejemplo.

### Paso 1: cortar la partida en fotos

Tomamos cada paso de la partida y lo tratamos como una **foto congelada** del tablero. A cada foto la llamamos un **snapshot**.

```
Partida de 140 pasos  →  ~140 snapshots
```

### Paso 2: convertir cada foto en números

Un snapshot es un objeto JSON anidado. Un modelo de ML no come JSON: come **una fila de números**. Así que extraemos:

```
snapshot JSON  →  [turno=12, mis_premios=3, sus_premios=5, mi_HP=180,
                   su_HP=90, mis_cartas_mano=4, mis_energias=2,
                   estoy_envenenado=0, diferencia_premios=-2, ...]
```

Cada uno de esos números se llama una **característica** (o *feature*). Tenemos 34 campos disponibles en el 100 % de los snapshots, más las combinaciones que derivamos de ellos (por ejemplo, `diferencia_de_premios = mis_premios - sus_premios`).

### Paso 3: pegarle la respuesta

A cada fila le agregamos una columna final con la respuesta que ya conocemos:

```
[turno=12, premios=3, HP=180, ...]  →  y = 1   (este jugador ganó)
[turno=12, premios=5, HP=90,  ...]  →  y = 0   (este jugador perdió)
```

### Resultado

Una tabla gigante:

| turno | mis_premios | sus_premios | mi_HP | ... | **ganó** |
|---|---|---|---|---|---|
| 3 | 6 | 6 | 180 | ... | 1 |
| 4 | 6 | 5 | 180 | ... | 1 |
| 5 | 5 | 5 | 120 | ... | 1 |
| ... | ... | ... | ... | ... | ... |

**7 millones de filas.** Esa tabla es todo nuestro proyecto. Todo lo que sigue opera sobre ella.

---

## 5. Qué significa "entrenar un modelo"

Vamos con el modelo más simple que vamos a usar, porque es el que se entiende sin matemáticas pesadas.

### Regresión logística = sus pesos de fitness, pero calculados

El modelo tiene esta forma:

```
puntaje = w1*turno + w2*mis_premios + w3*sus_premios + w4*mi_HP + ... + b
probabilidad_de_ganar = squash(puntaje)
```

Donde `squash()` es una función que aplasta cualquier número real al rango 0–1, para que la salida sea una probabilidad.

**Los `w` son exactamente los pesos de fitness que usted ajustaría a mano.** La diferencia es cómo se obtienen:

| | Cómo se obtienen los pesos |
|---|---|
| Fitness a mano | Usted prueba valores hasta que "se ve bien" |
| Regresión logística | Un optimizador busca los pesos que minimizan el error sobre 7 millones de ejemplos |

El "entrenamiento" es literalmente eso: un bucle de optimización que ajusta los `w` para que las predicciones se parezcan lo más posible a las respuestas conocidas.

### Los modelos más complejos

Después probamos modelos que capturan cosas que una suma ponderada no puede. Por ejemplo, una interacción del tipo *"tener pocas cartas en mano es malo, pero solo si además me quedan pocos premios"* — eso una suma lineal no lo expresa.

| Modelo | Qué agrega |
|---|---|
| Árbol de decisión | Una cadena de `if/else` aprendida automáticamente |
| Random Forest | Muchos árboles votando, para reducir el sobreajuste |
| Gradient Boosting | Árboles que se corrigen unos a otros en secuencia |

**Ninguno de estos es una red neuronal.** Ese es el punto del Track A: son métodos clásicos, interpretables, y la literatura muestra que sobre datos tabulares como los nuestros suelen ganarle al deep learning.

---

## 6. El problema que puede arruinar todo: data leakage

Esta es la parte que más cuenta para la nota, y la que el profesor señaló como el reto central del tema.

### El error concreto

La forma normal de dividir datos es:

```
70 % de las filas → entrenar el modelo
30 % de las filas → probar si funciona
```

Aplicado a nuestra tabla, **eso está mal**, y así de mal:

Suponga la partida #4231, que produjo 140 filas. Al repartir filas al azar, unas 98 caen en entrenamiento y unas 42 en prueba. Pero **las filas del turno 12 y del turno 13 de la misma partida son casi idénticas** — cambió una carta, nada más.

Entonces el modelo, al ser evaluado, está viendo situaciones que prácticamente ya vio durante el entrenamiento. **No está prediciendo: está recordando.**

Lo medimos: con un reparto aleatorio, **el 99,995 % de las partidas termina con filas en ambos lados.**

### Por qué es tan peligroso

Porque **las métricas mejoran**. Un proyecto con leakage reporta números excelentes. Nadie sospecha nada, y el modelo no sirve para nada porque memorizó en lugar de aprender.

Por eso el curso lo penaliza con −15 puntos.

### La solución

**Dividimos por partida completa, nunca por fila.**

```
Partidas 1 a 36.000     → todas sus filas van a entrenamiento
Partidas 36.001 a 44.000 → todas sus filas van a validación
Partidas 44.001 a 52.085 → todas sus filas van a prueba
```

Ninguna partida puede tener filas en dos conjuntos. Y escribimos una prueba automática que **falla** si eso pasa.

### El segundo tipo de trampa: campos prohibidos

El JSON trae un campo llamado `visualize` que contiene **el mazo completo del rival, en orden**. Un jugador real jamás vería eso.

Si se lo damos al modelo, sus predicciones serían buenísimas — y completamente inválidas, porque estaría usando información que en el momento real de la decisión no existía.

Por eso hay una **lista negra** de campos prohibidos: `visualize`, el resultado final, los nombres de los bots, el identificador de partida, y cualquier cosa que ocurra después del instante que estamos evaluando.

---

## 7. Cómo sabemos si funcionó

### Contra qué comparamos

Decir "mi modelo acierta el 75 %" no significa nada sin un punto de referencia. Por eso construimos una escalera:

| Nivel | Qué es | Qué demuestra si le ganamos |
|---|---|---|
| **B0** | Responder siempre la clase más común | Que el modelo aprendió *algo*. Si no le gana a esto, hay un error |
| **B1** | Una regla simple del juego: *"va ganando quien tiene menos premios pendientes"* | Que hace falta ML y no basta el sentido común del juego |
| **B2** | Regresión logística | Que la relación es lineal, o que no lo es |
| **B3** | Random Forest | Que hay interacciones que el modelo lineal no capta |
| **B4** | Gradient Boosting | Cuánto compra la complejidad extra |

**B1 es el más importante de todos.** Si una regla de tres líneas iguala a nuestro mejor modelo, el proyecto tiene que decirlo — y eso también es un resultado válido.

### Las métricas

**AUC** es la métrica principal. Mide qué tan bien el modelo *ordena*: si toma un caso ganador y uno perdedor al azar, ¿le da mayor probabilidad al ganador? 0,5 es azar puro; 1,0 es perfecto.

**Pero el AUC no basta**, y esta es una de las brechas que atacamos.

El AUC solo mira el orden, no los números. Un modelo puede ordenar perfecto y aun así decir "95 % seguro" cuando la realidad es 60 %. Eso se llama estar **mal calibrado**.

Como nuestro modelo va a servir de *evaluador de posiciones* —alguien va a leer el "68 %" y creerle— **el número tiene que significar lo que dice.** Por eso reportamos también Log Loss, Brier Score y curvas de calibración.

### El número de la literatura

Nadie ha hecho esto en Pokémon TCG. Pero **sí se hizo en Hearthstone**, otro juego de cartas, en el AAIA'17 Data Mining Challenge: baseline oficial de AUC ≈ 0,7846 y mejor solución ≈ 0,8019.

Eso nos da una idea del orden de magnitud de lo que es un buen resultado en este tipo de tarea. **No es un número a batir** — es otro juego, con otras reglas — y así se declara explícitamente en el artículo.

---

## 8. El pipeline completo

```
1. Descargar los replays JSON de Kaggle
                ↓
2. Parsear cada JSON y extraer los snapshots
                ↓
3. Convertir cada snapshot en una fila de números (34 campos + derivadas)
                ↓
4. Pegarle la etiqueta: ¿ganó o perdió este jugador?
                ↓
5. Guardar la tabla completa en formato columnar (una sola vez)
                ↓
6. Dividir POR PARTIDA en entrenamiento / validación / prueba
                ↓
7. Entrenar B0, B1, B2, B3, B4 sobre entrenamiento
                ↓
8. Elegir el mejor usando validación (el conjunto de prueba NO se toca)
                ↓
9. Medir una sola vez sobre prueba: AUC, Log Loss, calibración
                ↓
10. Analizar qué características pesaron más y cómo cambia
    la predicción conforme avanza la partida
```

El paso 5 importa por una razón práctica: parsear los JSON toma horas (son 182 GB). Se hace **una sola vez** y se guarda la tabla resultante; después todo el trabajo corre sobre la tabla.

---

## 9. Por qué esto es investigación y no un ejercicio

Un ejercicio sería: *"entrené un modelo y da 0,80 de AUC"*.

Nuestra pregunta es otra:

> **¿Cuánta información sobre el desenlace contiene un estado aislado de Pokémon TCG, cómo cambia esa información conforme avanza la partida, y cuánto de eso sobrevive cuando el modelo enfrenta partidas, mazos y periodos que nunca vio?**

Eso trae tres cosas que un ejercicio no tiene:

**Primero, es refutable.** Puede que en los turnos tempranos el modelo no le gane al azar. Ese sería un resultado negativo y **también respondería la pregunta**.

**Segundo, medimos por turno.** No solo "¿acierta?" sino "¿a partir de qué momento de la partida empieza a acertar?". Esa curva es la contribución principal.

**Tercero, probamos tres formas de generalizar**, cada una responde algo distinto:

| Protocolo | Pregunta que responde |
|---|---|
| Partidas nuevas | ¿Generaliza a partidas que no vio? |
| Datos de días posteriores | ¿Sobrevive cuando cambian los mazos y los bots? |
| Mazos nunca vistos | ¿Aprendió a leer el tablero, o memorizó qué mazos ganan? |

El tercero es el más filoso. Si el modelo solo aprendió *"el mazo X gana mucho"*, no está leyendo el tablero — está memorizando el metajuego. Reservar mazos completos para prueba lo delata.

---

## 10. Qué NO estamos haciendo

Aclarar esto evita confusiones, sobre todo porque otro grupo del curso trabaja con Pokémon usando aprendizaje por refuerzo.

| No hacemos | Por qué |
|---|---|
| Un bot que juegue | No decidimos acciones. Solo evaluamos estados |
| Aprendizaje por refuerzo | No hay agente que interactúe con un entorno. Aprendemos de partidas ya jugadas, sin tocar nada |
| Competir en Kaggle | Usamos los datos, no participamos |
| Predecir la jugada óptima | Predecimos el desenlace, no la acción |
| Generalizar a humanos | Son partidas entre bots de la franja alta. El modelo no aplica a jugadores humanos y lo declaramos |

**La diferencia con el otro grupo, en una línea:** ellos entrenan un agente que *juega*; nosotros entrenamos un evaluador que *observa*.

---

## 11. Dónde entra el "agente inteligente" de la Etapa 3

El curso exige que en la etapa final la solución quede consumida por un agente inteligente. El acoplamiento es directo:

```
Estado de la partida
        ↓
  extractor de características (el mismo del entrenamiento)
        ↓
  nuestro modelo → P(victoria | estado) = 0.68
        ↓
  agente inteligente → "vas ganando por poco; tu ventaja
                        está en la diferencia de premios"
```

El agente **consume** el predictor como una herramienta. No lo entrena, no lo mejora, no lo sustituye. Nuestro proyecto no se convierte en RL en ninguna etapa.

---

## 12. Estado actual

**Hecho:**
- Auditoría completa del dataset: 52.085 partidas, 7.038.378 snapshots, 34 campos presentes en el 100 % de los snapshots, cero duplicados.
- Medición del riesgo de leakage: el 99,995 % de las partidas se contamina con un reparto aleatorio.
- Lista negra de campos prohibidos, definida y verificada.
- Revisión de literatura repartida en tres ejes, uno por integrante.

**Pendiente:**
- Construir la tabla final de entrenamiento.
- Entrenar los baselines B0 a B4.
- Evaluar bajo los tres protocolos.

**No se ha entrenado ningún modelo todavía.** El trabajo actual es cerrar el diseño del dataset antes de modelar — y ese orden es intencional: modelar primero y diseñar después es exactamente como se termina con leakage.

---

## Glosario mínimo

| Término | Qué es |
|---|---|
| **Snapshot** | Una foto del tablero en un instante. Nuestra unidad de dato |
| **Feature** | Un número extraído del snapshot. Una columna de la tabla |
| **Etiqueta** | La respuesta conocida: ¿ganó o perdió? |
| **Entrenar** | Ajustar los pesos del modelo para que sus predicciones se acerquen a las etiquetas |
| **Baseline** | Modelo simple de referencia contra el cual comparamos |
| **AUC** | Qué tan bien ordena el modelo. 0,5 = azar, 1,0 = perfecto |
| **Calibración** | Si dice 70 %, ¿gana el 70 % de las veces? |
| **Data leakage** | Darle al modelo información que en el momento real no tendría |
| **Episodio** | Una partida completa. Nuestra unidad estadísticamente independiente |