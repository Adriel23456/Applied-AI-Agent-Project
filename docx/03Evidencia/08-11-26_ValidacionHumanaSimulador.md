# Validación humana con el simulador (Etapa 3)

Rama: `08AgentValidationAndSimulator`. Cada integrante hizo 5 pruebas distintas: 15 en total, sin repetir ninguna. La dirección esperada se fijó **antes** de las sesiones, con lógica básica del juego (por ejemplo, tener menos premios por tomar acerca a la victoria). El objetivo era comprobar dos cosas: que el simulador funciona en la computadora de cada uno y que la dirección de los cambios tiene sentido de juego. No se mide si el modelo acierta.

## 1. Procedimiento

1. Abrir el simulador en el mismo estado inicial:
   ```powershell
   $env:PYTHONPATH = "src"
   python -m ptcg_agente.simulador --archivo artefactos_agente/agente/ejemplos/partida_87363568.json --paso 37
   ```
   Es el paso 37 de la partida 87363568: turno 6, etapa de medio, le toca actuar al jugador 1. **Probabilidad inicial del jugador 0: 66.1 %.**

   | | Premios por tomar | Mano | Mazo | Descarte | Activo | Banca |
   |---|---|---|---|---|---|---|
   | Jugador 1 | 6 | 4 | 37 | 7 | #119, 70/70 PV, 2 energías | #112 y #119 |
   | Jugador 0 | 5 | 6 | 38 | 4 | #345, 190/190 PV, 3 energías | #756 |

2. Para cada prueba: hacer **solo** ese cambio, anotar la probabilidad del jugador 0 que muestra el simulador y presionar **Deshacer cambios** antes de la siguiente.

El simulador funcionó en las tres computadoras.

## 2. Pruebas

### Adriel

| # | Cambio desde el estado inicial | Dirección esperada | Jugador 0 después | ¿Coincide? |
|---|---|---|---|---|
| A1 | Premios por tomar del jugador 0: de 5 a 4 | Sube | 83.0 % (+16.9) | Sí |
| A2 | Mazo del jugador 1 en 0 | Sube | 80.7 % (+14.6) | Sí |
| A3 | PV del activo del jugador 1 en 10 | Sube | 77.3 % (+11.2) | Sí |
| A4 | Activo del jugador 1 quemado | Sube un poco | 66.1 % (sin cambio) | No: no cambia en absoluto |
| A5 | Vaciar la banca del jugador 0 (quitar #756) | Baja | 50.9 % (−15.2) | Sí |

### Daniel

| # | Cambio desde el estado inicial | Dirección esperada | Jugador 0 después | ¿Coincide? |
|---|---|---|---|---|
| D1 | Premios por tomar del jugador 0: de 5 a 6 | Baja | 55.8 % (−10.3) | Sí |
| D2 | Mazo del jugador 0 en 0 | Baja | 1.7 % (−64.4) | Sí |
| D3 | PV del activo del jugador 0 en 10 | Baja | 25.3 % (−40.8) | Sí |
| D4 | Energías del activo del jugador 0: de 3 a 6 | Sube | Baja. Con las 3 energías en el Pokémon de la banca (#756): 70.6 % (+4.5) | No en el activo; sí en la banca |
| D5 | Activo del jugador 0 dormido | Baja | 66.1 % (sin cambio) | No: no cambia |

### Sebastián

| # | Cambio desde el estado inicial | Dirección esperada | Jugador 0 después | ¿Coincide? |
|---|---|---|---|---|
| S1 | Premios por tomar del jugador 1: de 6 a 5 | Baja | 56.0 % (−10.1) | Sí |
| S2 | Premios por tomar del jugador 1: de 6 a 1 | Baja mucho | 17.0 % (−49.1) | Sí |
| S3 | Agregar 2 Pokémon a la banca del jugador 0 | Sube | 70.2 % (+4.1) | Sí |
| S4 | Activo del jugador 1 paralizado | Sube | 66.1 % (sin cambio) | No: no cambia |
| S5 | **Estado nuevo (sin partida)**, armado igual para los dos: turno 5, le toca al jugador 0, 6 premios, 5 cartas en la mano, 30 en el mazo, 0 en el descarte, activo #743 (140 PV) y nada en la banca | Cerca de 50 % | 60.2 % | En parte: ventaja de 10 puntos para el jugador 0 |

## 3. Resultado

**10 de 15 pruebas tuvieron la dirección esperada.** Las otras 5 se explican abajo.

| Resultado | Pruebas |
|---|---|
| Dirección esperada | A1, A2, A3, A5, D1, D2, D3, S1, S2, S3 |
| Sin ningún cambio (condiciones especiales) | A4 (quemado), D5 (dormido), S4 (paralizado) |
| Dirección inesperada | D4 (energías en el activo) |
| En parte | S5 (estado simétrico: 60.2 % y no cerca de 50 %) |

**Lo que mejor captura el modelo** son los recursos que deciden la partida:
- Los premios por tomar mueven la probabilidad en el sentido correcto para ambos jugadores (A1, D1, S1). Cuando al jugador 1 le queda un solo premio, el jugador 0 cae a 17.0 % (S2).
- Quedarse sin mazo es casi una derrota para el jugador 0 (1.7 %, D2). El mismo cambio en el rival sube al jugador 0 a 80.7 % (A2).
- Un activo con pocos PV baja mucho a su dueño (D3: 25.3 %) y sube al rival (A3: 77.3 %).
- La banca importa: sin banca, perder el activo puede terminar la partida (A5: 50.9 %), y más Pokémon en la banca ayudan (S3: 70.2 %).

**Direcciones inesperadas y explicación:**

1. **Las condiciones especiales casi no mueven la probabilidad en este estado** (A4, D5, S4). Quemado, dormido y paralizado dejaron al jugador 0 exactamente en 66.1 %. Esas condiciones aparecen muy pocas veces en el entrenamiento, y el simulador las marca como "valor poco frecuente". Con tan pocos ejemplos, el modelo rara vez las usa para dividir los datos, y su efecto queda en cero en la mayoría de los estados. No siempre es así: en el estado personalizado de `08-11-26_SimuladorEstadoPersonalizado.png`, que el activo del jugador 1 estuviera **envenenado** sumó +17.5 puntos al jugador 0, y que estuviera **dormido**, +6.6. El efecto existe solo en combinación con otros valores del estado. En D5 hay además una razón de juego: le toca actuar al jugador 1, así que el sueño del activo del jugador 0 todavía no le impide nada.
2. **Más energías en el activo bajan la probabilidad** (D4). Agregar 3 energías al activo del jugador 0 (de 3 a 6) la bajó; agregarlas al Pokémon de la banca la subió a 70.6 %. Es una asociación del modelo, no una causa: 6 energías en un activo es un valor poco común en el entrenamiento, y en las partidas reales acumular energías en el activo puede coincidir con situaciones peores (por ejemplo, un activo que no ha podido atacar). Es un buen ejemplo de por qué las contribuciones SHAP se presentan como asociaciones y no como causas.
3. **Un estado simétrico no da 50 %** (S5). Con los dos jugadores en las mismas condiciones, el jugador 0 quedó en 60.2 %. El estado no es del todo simétrico: el jugador 0 empezó la partida y le toca actuar, y en el juego actuar con todo igual es una ventaja (puede atacar primero en ese turno). El modelo también aprendió esa ventaja de las partidas reales.

**Conclusión:** en los recursos que deciden la partida (premios, mazo, PV y banca), el modelo responde con sentido de juego en las 10 pruebas. Los puntos débiles son las condiciones especiales, que el modelo casi ignora por su poca frecuencia, y algunas asociaciones que no son causales, como las energías en el activo. Los dos se declaran como límites en la rama 09.
