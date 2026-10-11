# Diccionario de datos y contrato de uso

Documento de referencia de la tabla de estados de la Etapa 2. Explica qué es cada fila, qué
información contiene y cuál no, qué se verificó, cómo están hechas las particiones y qué reglas
debe respetar cualquier modelo que se entrene con estos datos.

Código que produce todo lo descrito: `src/ptcg_wp/features.py`, `ingest.py`, `splits.py`, `data.py`.
Datos procesados: dataset privado de Kaggle `adrielchavessalazar/ptcg-wp-tablas`.

---

## 1. Resumen en un minuto

- **Una fila = una foto del tablero** vista por el jugador que tiene que decidir en ese momento.
- **Etiqueta `y`:** 1 si ese jugador termina ganando la partida.
- **Solo información que ese jugador puede ver** en ese instante. La mano del oponente, los premios
  boca abajo, el orden de los mazos y el resultado nunca se usan (y hay pruebas automáticas que lo garantizan).
- **Corpus:** 10 días, 55 077 partidas con ganador, 7 286 386 filas útiles.
- **La unidad independiente es la partida, no la fila.** Toda partición, validación cruzada e
  intervalo de confianza se agrupa por `game_id`.
- **Listo para modelar:** `load_scenario(...)` entrega X, y, partición y etapa por fila.

---

## 2. Qué es una fila

El motor del concurso (`cabt`, reglas del Pokémon TCG estándar adaptadas) registra cada partida como
una lista de pasos. En cada paso hay dos vistas, una por jugador:

- el jugador `ACTIVE` es el que debe elegir una acción;
- el jugador `INACTIVE` espera y su vista va un paso atrasada (98.8 % idéntica a su vista anterior,
  medido en el artículo).

**Se toma solo la vista del jugador `ACTIVE`**, antes de que elija su acción. Cada paso produce como
máximo una fila. Una partida produce en promedio unas 137 filas (una por acción atómica: jugar una
carta, unir una energía, atacar, etc.), y todas comparten la misma etiqueta.

Cada fila se escribe desde la perspectiva de ese jugador:

- `own_*` = el jugador que actúa ("yo");
- `opp_*` = su oponente;
- `diff_*` = yo menos el oponente.

Así el modelo compara recursos en lugar de aprender "el jugador de la posición 0 gana más".

### Ejemplo de lectura

En un tablero donde el oponente tiene a Darkrai ex activo con 140 PV y dos Pokémon en la banca
(170 y 140 PV), y yo tengo un activo con 30 PV y un Pokémon de 30 PV en la banca, la fila diría:

| Columna | Valor | Lectura |
|---|---|---|
| `own_active_hp` | 30 | Mi activo está a 30 PV |
| `opp_active_hp` | 140 | El activo rival tiene 140 PV |
| `opp_active_max_hp` | 180 (por ejemplo) | Su vida máxima (si está dañado, `opp_damaged` suma 1) |
| `own_bench_n` / `opp_bench_n` | 1 / 2 | Pokémon en cada banca |
| `opp_total_hp` | 450 | 140 + 170 + 140 |
| `diff_total_hp` | -390 | Voy muy abajo en vida total en juego |
| `opp_active_energies` | número de energías unidas al Darkrai | Qué tan listo está para atacar |

Nota: las capturas de Pokémon TCG Pocket sirven como ilustración, pero ese juego tiene otras reglas
(3 puntos, banca de 3). Este corpus sigue el TCG estándar: 6 premios, mazo de 60 cartas
(47 en el mazo tras repartir mano y premios), banca normal de 5 que algunas cartas amplían (se
observaron hasta 8).

---

## 3. Qué se ve y qué no

| Información | ¿La usa el modelo? | Cómo viene en el JSON | Verificado |
|---|---|---|---|
| Pokémon activo y banca de ambos (id, PV, PV máx., energías, herramientas, evolución) | Sí | Objetos completos | Sí |
| Tamaño de mano, mazo y descarte de ambos | Sí | Enteros y listas | Sí |
| Premios que quedan a cada jugador | Sí (cantidad) | Lista de `null` (el largo es la cantidad) | Sí |
| Condiciones especiales, estadio, banderas del turno | Sí | Booleanos | Sí |
| Número de turno y acciones del turno | Sí | Enteros | Sí |
| **Contenido** de la mano propia | No (solo el tamaño) | Lista de cartas | Decisión de diseño |
| Contenido de la mano del oponente | **Nunca** | `null` | Sí: siempre nulo |
| Contenido de los premios | **Nunca** | Lista de `null` | Sí: siempre nulo |
| `search_begin_input` (estado completo codificado para búsqueda) | **Nunca** | Texto codificado | Puede contener información oculta |
| `logs` (historial de jugadas) | No | Lista de eventos | Fuera del alcance (estado aislado) |
| `result` del estado | **Nunca** | Siempre con valor (constante) | No informa nada |
| `rewards`, ganador, nombres de agentes | **Nunca en X** | Nivel de partida | Prohibidos por código |

Las pruebas `tests/test_fuga.py` llenan la mano rival y los premios con cartas reales, cambian
`result` y `rewards`, y cortan los pasos futuros: en todos los casos **X no cambia**.

---

## 4. Corpus

| Día | Partidas | Empates | Estados | Filas útiles | Gana el índice 0 |
|---|---|---|---|---|---|
| 2026-06-17 | 7 819 | 28 | 801 704 | 764 512 | 0.507 |
| 2026-06-18 | 6 532 | 11 | 783 197 | 751 526 | 0.495 |
| 2026-06-19 | 5 426 | 15 | 748 776 | 724 005 | 0.515 |
| 2026-06-20 | 5 178 | 10 | 741 313 | 718 034 | 0.509 |
| 2026-06-22 | 5 062 | 9 | 738 992 | 716 089 | 0.511 |
| 2026-06-25 | 5 495 | 5 | 751 230 | 725 807 | 0.512 |
| 2026-07-07 | 5 202 | 11 | 762 035 | 738 245 | 0.534 |
| 2026-07-11 | 5 018 | 10 | 745 837 | 723 223 | 0.542 |
| 2026-07-15 | 4 825 | 14 | 720 923 | 699 208 | 0.555 |
| 2026-07-22 | 4 639 | 6 | 746 382 | 725 737 | 0.559 |
| **Total** | **55 196** | **119** | **7 540 389** | **7 286 386** | |

- Las cifras superan a las de la auditoría del artículo (52 085 partidas, 7 038 378 observaciones):
  Kaggle siguió agregando episodios a esos días después de la auditoría. El artículo debe usar estas.
- **"Gana el índice 0" sube con el tiempo** porque en los días tardíos el jugador que empieza ocupa
  casi siempre la posición 0 (el artículo mide 0.5089 → 0.9991). Es la ventaja de empezar, no una
  ventaja de la posición. Por eso las filas usan perspectiva propio/oponente y `first_player_is_me`.

---

## 5. Tablas y columnas

### 5.1 `estados_<dia>.parquet`: 73 columnas (9 meta + 64 características)

#### Columnas meta (nunca entran a X)

| Columna | Descripción |
|---|---|
| `game_id` | Identificador de la partida (`info.EpisodeId`). **Clave de agrupación** |
| `day` | Día del dataset de Kaggle |
| `step` | Índice del paso dentro de la partida |
| `turn` | Turno del juego (0 = preparación). Se usa para las etapas |
| `acting_index` | Posición (0 o 1) del jugador que actúa |
| `anomalous` | 1 si algún jugador no terminó en `DONE` (0 partidas en el corpus) |
| `setup` | 1 si `turn == 0`: preparación, premios aún sin repartir |
| `decided` | 1 si el tablero ya muestra la partida resuelta: un jugador sin premios por tomar o sin Pokémon en juego |
| `y` | Etiqueta: 1 si el jugador que actúa gana la partida |

**Filtro único para modelar:** `usable(df)` = `setup == 0` y `decided == 0`.
Excluye 239 778 filas de preparación y 14 225 filas ya resueltas.

#### Familia "Progreso del turno" (8)

| Columna | Descripción | Rango observado |
|---|---|---|
| `game_turn` | Número de turno (público) | 1 a 285 |
| `turn_action_count` | Acciones ya hechas en este turno | 1 a 83 |
| `energy_attached` | Ya unió su energía del turno | 0/1 |
| `retreated` | Ya se retiró este turno | 0/1 |
| `supporter_played` | Ya jugó un Partidario este turno | 0/1 |
| `stadium_played` | Ya jugó un Estadio este turno | 0/1 |
| `stadium_in_play` | Hay un Estadio en juego | 0/1 |
| `first_player_is_me` | El jugador que actúa empezó la partida | 0/1 |

#### Familia "Recursos y tablero", por jugador (25 con `own_` y 25 con `opp_`)

| Columna (sin prefijo) | Descripción | Centinela -1 |
|---|---|---|
| `deck` | Cartas que quedan en el mazo | No |
| `hand` | Tamaño de la mano (nunca su contenido) | No |
| `discard` | Cartas en el descarte | No |
| `prizes` | Premios que quedan por tomar (0 a 6) | No |
| `bench_n` | Pokémon en la banca | No |
| `active_present` | Hay Pokémon activo (indicador de ausencia) | No |
| `active_card` | Id de carta del activo. **Contexto de mazo: excluido del modelo principal** | Sí |
| `active_hp` | PV actuales del activo | Sí |
| `active_max_hp` | PV máximos del activo | Sí |
| `active_hp_ratio` | `active_hp / active_max_hp` | Sí |
| `active_energies` | Energías unidas al activo | Sí |
| `active_tools` | Herramientas unidas al activo | Sí |
| `active_evolved` | El activo es una evolución | Sí |
| `active_new` | El activo entró en juego este turno | Sí |
| `bench_hp` | Suma de PV de la banca | No |
| `bench_energies` | Suma de energías de la banca | No |
| `total_hp` | Suma de PV de todos sus Pokémon en juego | No |
| `total_energies` | Suma de energías de todos sus Pokémon en juego | No |
| `total_tools` | Suma de herramientas en juego | No |
| `damaged` | Pokémon en juego con PV por debajo de su máximo | No |
| `asleep`, `burned`, `confused`, `paralyzed`, `poisoned` | Condiciones especiales | No |

**Ausencia estructural:** cuando no hay Pokémon activo (por ejemplo, justo después de un KO y antes
de subir otro), `active_present = 0` y los campos `active_*` valen -1. Pasa en el 3.99 % de las filas
útiles. No se imputa: es una situación real del juego y los árboles la aprovechan.

#### Familia "Diferenciales" (6)

| Columna | Rango observado |
|---|---|
| `diff_hand` | -35 a 36 |
| `diff_prizes` | -5 a 5 |
| `diff_bench_n` | -8 a 8 |
| `diff_total_hp` | -1950 a 1950 |
| `diff_total_energies` | -52 a 52 |
| `diff_deck` | -44 a 43 |

**Modelo principal:** 62 características (todas menos `own_active_card` y `opp_active_card`).
**Ablación de contexto de mazo (H2):** 64 características (`include_cards=True`).

### 5.2 `partidas_<dia>.parquet`: una fila por partida (14 columnas)

| Columna | Descripción | Uso |
|---|---|---|
| `game_id`, `day` | Identificador y día | Unión con estados |
| `n_steps` | Pasos de la partida | Auditoría y regla de cobertura |
| `reward_0`, `reward_1` | Recompensa final de cada posición | Solo etiqueta. **Prohibido en X** |
| `status_0`, `status_1` | Estado final de cada posición | Marca `anomalous` |
| `winner` | 0, 1 o -1 (empate) | Solo etiqueta. **Prohibido en X** |
| `agent_0`, `agent_1` | Seudónimo del agente (SHA-256 truncado, nunca el nombre real) | **Prohibido en X** |
| `deck_0`, `deck_1` | Ids de Pokémon que cada jugador puso en juego en toda la partida | Solo partición. **Prohibido en X** |
| `main_0`, `main_1` | Pokémon que más tiempo fue activo (arquetipo de mazo) | Solo escenario C. **Prohibido en X** |

### 5.3 `particiones.parquet`: una fila por partida con ganador

| Columna | Descripción |
|---|---|
| `game_id`, `day` | Identificador y día |
| `split_A`, `split_B`, `split_C` | `train`, `val`, `calib`, `test` o `fuera` (no se usa en ese escenario) |

---

## 6. Validez de los datos: qué se verificó

| Verificación | Resultado |
|---|---|
| JSON corruptos | Se omiten y se reportan (0 tras la descarga completa) |
| `game_id` repetidos entre días | 0 |
| Empates con filas de estado | 0 (los 119 empates se excluyen completos) |
| Partidas anómalas (status distinto de `DONE`) | 0 |
| El `yourIndex` de la vista coincide con el jugador `ACTIVE` | 100 % en la partida de prueba |
| Premios fuera de 0-6 | 0 filas |
| Mazo, mano o banca negativos | 0 filas |
| PV del activo mayor que su máximo | 0 filas |
| Columnas constantes | Ninguna (las condiciones especiales son raras pero no constantes) |
| AUC de cada característica por sí sola | Máximo 0.68 (`diff_prizes`, en sentido inverso). Ninguna sobre 0.85: sin señales de fuga |
| Prevalencia de `y` en filas útiles | 0.517 (mayor que 0.5 porque el ganador tiene más pasos propios) |

---

## 7. Qué NO capturan los datos (limitaciones declaradas)

- **No hay nombres, tipos, ataques ni debilidades de las cartas:** solo ids numéricos. No se puede
  saber, por ejemplo, si el activo es un Pokémon "ex" (que entrega 2 premios al caer) más que por su
  PV máximo, que el modelo sí ve.
- **El tipo de energía** no se distingue: solo cuántas hay.
- **La composición de la mano propia** no se usa (solo su tamaño), aunque el jugador la ve.
  Es una extensión posible, declarada.
- **El historial** (`logs`) no se usa: el modelo evalúa un estado aislado, como fija el artículo.
- **Casi ninguna partida termina por premios** (1 de 300 en la muestra): terminan sin Pokémon en
  juego, sin mazo o por tiempo. Los premios pesan menos aquí que en el juego humano.
- **El tiempo de calendario y la versión del motor están confundidos:** el escenario B mide su efecto
  conjunto, sin separarlos.

---

## 8. Particiones, cobertura y etapas

| Escenario | Cómo se parte | Pregunta | Proporciones |
|---|---|---|---|
| A | Partidas al azar | ¿Generaliza a partidas nuevas? | 60/15/10/15 |
| B | Días completos en orden: train 18 al 25 jun, val 7 jul, calib 11 jul, test 15 y 22 jul. El 17 jun queda fuera (arranque parcial) | ¿Se sostiene en días posteriores? | Por días (ver reporte de la celda 8) |
| C | Test = partidas con alguno de los 33 Pokémon principales reservados; el resto al azar | ¿Lee el estado o memoriza mazos? | 60/15/10/15 aprox. |

**Cobertura de cartas (regla del artículo).** Toda carta que estuvo activa en el corpus debe aparecer
en train. En A y C, si falta alguna, se mueve a train la partida más corta que la contiene (en C nunca
se mueve una partida reservada). En B no se mueve nada, porque rompería la cronología: se reporta la
cobertura efectiva (antes de la corrección, a lo sumo 0.58 % de filas con una carta no vista).
El reporte exacto lo imprime la celda 8 de `00_arranque`.

**Escenario C mide arquetipos nuevos, no cartas nuevas:** las cartas de un mazo reservado también
aparecen en otros mazos de train.

**Etapas de la partida:** terciles del turno calculados **solo con train** de cada escenario.
Con los datos actuales: inicio ≤ 5 turnos, medio 6 a 9, final > 9 (iguales en A, B y C).

---

## 9. ¿Alcanzan los datos?

Sí, y sobran para lo que pide la etapa.

- **La cantidad que importa es el número de partidas, no de filas:** las filas de una misma partida
  están correlacionadas. Train del escenario A tiene unas 33 000 partidas (4.36 M filas), y val,
  calib y test tienen entre 5 500 y 8 300 partidas cada uno. Cada etapa de la partida queda con
  miles de partidas en todos los subconjuntos.
- **El antecedente de literatura** (Hearthstone, AAIA'17) trabajó con un volumen comparable o menor.
- **La curva de aprendizaje es la prueba formal:** si el AUC deja de subir al pasar de 25 % a 100 %
  de las partidas de train, más días no ayudarían.
- **Agregar días tiene costo:** unas 12 horas de procesamiento más por cada 10 días y más deriva de
  población (los mazos de días lejanos son casi disjuntos). Si hiciera falta, basta agregarlos a
  `configs/dias.yaml` y reconstruir.

---

## 10. Contrato para modelar (obligatorio en los cuadernos 02 en adelante)

1. **Cargar siempre con `load_scenario`**, que aplica `usable` y entrega partición y etapa:

```python
   from ptcg_wp.data import load_scenario
   states, feats, split, stage = load_scenario("/content/datos", "A")
   tr, va = split == "train", split == "val"
   X_tr, y_tr, g_tr = states.loc[tr, feats], states.loc[tr, "y"], states.loc[tr, "game_id"]
```

2. **Todo preprocesamiento va dentro de un `Pipeline` de scikit-learn** ajustado solo con train.
3. **Validación cruzada siempre agrupada por partida** (`GroupKFold` con `groups=g_tr`). Nunca `KFold`
   ni `StratifiedKFold` a secas.
4. **`val`** elige hiperparámetros, **`calib`** ajusta la recalibración, **`test` se usa una sola vez**
   al final de cada escenario.
5. **Los ids de carta no entran al modelo principal.** Solo en la ablación de contexto de mazo
   (`include_cards=True`), para probar H2.
6. **Métricas:** AUC (principal), log loss y Brier, globales y por etapa (`stage`), cada una con su
   número de partidas.
7. **Los escenarios se reportan por separado**, nunca promediados.
8. **Semilla:** `SEED = 2026` (en `ptcg_wp.splits`).

---

## 11. Cómo trabajar: cuadernos y celdas

### Todo el equipo, en cada sesión (unos 2 minutos)

En `notebooks/00_arranque.ipynb`, en un servidor de Colab (CPU, RAM alta):

| Celda | Qué hace | Resultado esperado |
|---|---|---|
| 2 | Clona o actualiza el repo (poner en `BRANCH` la rama de trabajo) | Sin errores |
| 3 | Pruebas automáticas | `24 passed` |
| 4 | Token de Kaggle (cada uno usa el suyo) | Lista de datasets |
| 6 | Baja las 21 tablas del dataset del equipo (`CONSTRUIR = False`) | `OK: estan los 10 dias` |
| 7 | Verificación | 55 196 partidas, 7 540 389 estados |

Después, en el mismo servidor, se abre el cuaderno de trabajo (`01_exploracion`, `02_baselines`...).

### Solo quien publica (al cambiar `features.py`, `ingest.py`, `splits.py` o los días)

| Celda | Qué hace |
|---|---|
| 6 con `CONSTRUIR = True` | Reconstruye desde los JSON de Kaggle (borrar antes los Parquet si cambió el extractor) |
| 8 | Regenera `particiones.parquet` e imprime el reporte de cobertura |
| 9 con `CREAR = False` | Publica una nueva versión del dataset con el commit en el mensaje |

### Cuadernos

| Cuaderno | Contenido |
|---|---|
| `00_arranque` | Ambiente, datos, verificación, particiones y publicación |
| `01_exploracion` | Inspección del JSON crudo (parte A), auditoría de la tabla (parte B), particiones, etapas y cobertura (parte C) |
| `02_baselines` | B0 (a priori), B1 (heurística), B2 (regresión logística) y demostración de inflación por fila vs. por partida |
| `03_modelo_principal` | B3, B4 y búsqueda de hiperparámetros con validación agrupada |
| `04_evaluacion_xai_calibracion` | Prueba final, SHAP, curvas, errores y calibración |

---

## 12. Pruebas automáticas (24)

| Archivo | Qué garantiza |
|---|---|
| `tests/test_fuga.py` (13) | La información oculta, `result`, `rewards` y los pasos futuros no cambian X; empates excluidos; `setup` y `decided` correctos; ids de carta fuera del modelo principal; columnas prohibidas bloqueadas |
| `tests/test_particiones.py` (10) | Una partición por partida; reproducible con la semilla; A con proporciones correctas; B por días completos, en orden y sin el primer día; C sin principales reservados fuera de test; cobertura de cartas en train; etapas |
| `tests/test_datos.py` (1) | `load_scenario` filtra filas útiles y asigna partición, etapa y características correctas |