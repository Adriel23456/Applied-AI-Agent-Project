# Diccionario de datos

Tablas que produce `src/ptcg_wp/ingest.py` (una por dia) y `src/ptcg_wp/splits.py`.
Se guardan en el dataset privado `adrielchavessalazar/ptcg-wp-tablas` y se reconstruyen con `00_arranque`.

Corpus: 10 dias (2026-06-17 a 2026-07-22), 55 196 partidas (119 empates), 7 540 389 estados,
7 286 386 filas utiles (sin preparacion ni estados resueltos).

## Principios

- Una fila de estados = el tablero visto por el **jugador que actua** en un paso, antes de decidir.
- Solo informacion visible para ese jugador en ese momento. Nunca se usa: contenido de la mano
  del oponente, contenido de los premios, `search_begin_input`, `logs`, pasos futuros, `result`,
  `rewards` ni nombres de agentes.
- Ausencia estructural: indicador + centinela `-1`, sin imputar.
- Prefijo `own_` = jugador que actua; `opp_` = oponente; `diff_` = propio menos oponente.

## Tabla `estados_<dia>.parquet`

### Columnas meta (no entran a X)

| Columna | Descripcion |
|---|---|
| `game_id` | Identificador de la partida (`info.EpisodeId`) |
| `day` | Dia del dataset de Kaggle |
| `step` | Indice del paso dentro de la partida |
| `turn` | Turno del juego (0 = preparacion) |
| `acting_index` | Jugador que actua (0 o 1) |
| `anomalous` | 1 si algun jugador no termino en estado DONE |
| `setup` | 1 si `turn == 0` (preparacion: premios sin repartir) |
| `decided` | 1 si el tablero ya muestra la partida resuelta (un jugador sin premios o sin Pokemon en juego) |
| `y` | Etiqueta: 1 si el jugador que actua gana la partida |

Filtro para modelar: `usable(df)` = `setup == 0` y `decided == 0`.

### Caracteristicas globales del turno (8)

| Columna | Descripcion | Rango observado |
|---|---|---|
| `game_turn` | Numero de turno (publico) | 1 a 285 |
| `turn_action_count` | Acciones ya realizadas en el turno actual | 1 a 83 |
| `energy_attached` | Ya se unio energia en este turno | 0/1 |
| `retreated` | Ya se retiro en este turno | 0/1 |
| `supporter_played` | Ya se jugo un Partidario en este turno | 0/1 |
| `stadium_played` | Ya se jugo un Estadio en este turno | 0/1 |
| `stadium_in_play` | Hay un Estadio en juego | 0/1 |
| `first_player_is_me` | El jugador que actua empezo la partida | 0/1 |

### Caracteristicas por jugador (25 con `own_` y 25 con `opp_`)

| Columna (sin prefijo) | Descripcion | Centinela |
|---|---|---|
| `deck` | Cartas que quedan en el mazo | - |
| `hand` | Tamano de la mano (nunca su contenido) | - |
| `discard` | Cartas en la pila de descarte | - |
| `prizes` | Premios que quedan por tomar (largo de la lista `prize`) | - |
| `bench_n` | Pokemon en la banca | - |
| `active_present` | Hay Pokemon activo | - |
| `active_card` | Id de carta del Pokemon activo (**categoria**, no cantidad) | -1 |
| `active_hp` | Vida actual del activo | -1 |
| `active_max_hp` | Vida maxima del activo | -1 |
| `active_hp_ratio` | `active_hp / active_max_hp` | -1 |
| `active_energies` | Energias unidas al activo | -1 |
| `active_tools` | Herramientas unidas al activo | -1 |
| `active_evolved` | El activo es una evolucion | -1 |
| `active_new` | El activo entro en juego este turno | -1 |
| `bench_hp` | Suma de vida de la banca | - |
| `bench_energies` | Suma de energias de la banca | - |
| `total_hp` | Suma de vida de todos los Pokemon en juego | - |
| `total_energies` | Suma de energias de todos los Pokemon en juego | - |
| `total_tools` | Suma de herramientas de todos los Pokemon en juego | - |
| `damaged` | Pokemon en juego con vida menor a su maximo | - |
| `asleep`, `burned`, `confused`, `paralyzed`, `poisoned` | Condiciones especiales del jugador | - |

Los campos `active_*` valen `-1` en el 3.99 % de las filas utiles (momentos sin Pokemon activo).

### Diferencias propio menos oponente (6)

| Columna | Rango observado |
|---|---|
| `diff_hand` | -35 a 36 |
| `diff_prizes` | -5 a 5 |
| `diff_bench_n` | -8 a 8 |
| `diff_total_hp` | -1950 a 1950 |
| `diff_total_energies` | -52 a 52 |
| `diff_deck` | -44 a 43 |

## Tabla `partidas_<dia>.parquet` (una fila por partida)

| Columna | Descripcion | Uso |
|---|---|---|
| `game_id`, `day` | Identificador y dia | Union con estados |
| `n_steps` | Pasos de la partida | Auditoria |
| `reward_0`, `reward_1` | Recompensa final de cada jugador | Solo etiqueta, **prohibido en X** |
| `status_0`, `status_1` | Estado final de cada jugador | Marca `anomalous` |
| `winner` | 0, 1 o -1 (empate) | Solo etiqueta, **prohibido en X** |
| `agent_0`, `agent_1` | Seudonimo del agente (SHA-256 truncado) | **Prohibido en X** |
| `deck_0`, `deck_1` | Ids de Pokemon puestos en juego en toda la partida | Solo particion, **prohibido en X** |
| `main_0`, `main_1` | Pokemon que mas tiempo fue activo (arquetipo) | Solo particion C, **prohibido en X** |

## Tabla `particiones.parquet` (una fila por partida con ganador)

| Columna | Descripcion |
|---|---|
| `game_id`, `day` | Identificador y dia |
| `split_A` | Partidas nuevas: azar por partida, 60/15/10/15 |
| `split_B` | Cronologico: orden por dia y `game_id`, 60/15/10/15 |
| `split_C` | Arquetipos reservados: 33 Pokemon principales solo en test (15.1 % de partidas) |

Valores: `train` (entrenar), `val` (hiperparametros), `calib` (calibracion), `test` (evaluacion final, una sola vez).
Semilla: `SEED = 2026`.

## Etapas de la partida

Terciles del turno calculados solo con train: **inicio** <= 5, **medio** 6 a 9, **final** > 9
(iguales en los tres escenarios).