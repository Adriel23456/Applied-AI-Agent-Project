# Validación humana con el simulador (Etapa 3)

Rama: `08AgentValidationAndSimulator`. El procedimiento está escrito **antes** de las sesiones. Cada integrante completa su tabla. El objetivo es comprobar si la dirección de los cambios de probabilidad tiene sentido de juego. No se mide si el modelo acierta.

## 1. Procedimiento

1. Abrir el simulador con el mismo estado para los tres:
   ```powershell
   $env:PYTHONPATH = "src"
   python -m ptcg_agente.simulador --archivo artefactos_agente/agente/ejemplos/partida_87363568.json --paso 37
   ```
   Es el paso 37 de la partida 87363568: turno 6, etapa de medio, le toca actuar al jugador 1. Es el mismo estado de la consulta A-04 de la validación N2.
2. Para cada cambio de la tabla:
   1. Anotar la **dirección esperada** (sube, baja o casi igual) **antes** de hacerlo.
   2. Hacer el cambio y anotar la probabilidad antes y después.
   3. Presionar **Restaurar el estado del paso** antes del siguiente cambio.
3. Hacer 3 cambios libres, elegidos por cada integrante, con el mismo registro. Al menos uno debe partir de **Estado nuevo (sin partida)**.
4. Tomar una captura de pantalla de un cambio que haya dado una dirección inesperada (o de cualquiera, si todos tuvieron sentido) y guardarla como `docx/03Evidencia/DD-MM-AA_SimuladorNombre.png`.

En "¿Tiene sentido?" se responde **Sí**, **No** o **Dudoso**, con una frase si no es Sí. El simulador siempre muestra la probabilidad de que gane el **jugador 0** (azul); todas las direcciones se refieren a esa cifra.

## 2. Cambios definidos

| # | Cambio | Dirección esperada por el protocolo |
|---|---|---|
| 1 | Quitar un premio por tomar al jugador 0 (le falta uno menos) | Sube |
| 2 | Agregar un premio por tomar al jugador 0 | Baja |
| 3 | Quitar un premio por tomar al jugador 1 | Baja |
| 4 | Mazo del jugador 0 en 0 | Baja |
| 5 | Mazo del jugador 1 en 0 | Sube |
| 6 | PV del activo del jugador 0 en 10 | Baja |
| 7 | PV del activo del jugador 1 en 10 | Sube |
| 8 | Vaciar la banca del jugador 0 | Baja |
| 9 | Agregar 3 energías al activo del jugador 0 | Sube |
| 10 | Agregar 2 Pokémon a la banca del jugador 0 | Sube |

## 3. Registro por integrante

### Adriel

Probabilidad inicial del jugador 0: ____ %

| # | Cambio | Esperada | Antes | Después | ¿Tiene sentido? | Comentario |
|---|---|---|---|---|---|---|
| 1 | Quitar un premio al jugador 0 | | | | | |
| 2 | Agregar un premio al jugador 0 | | | | | |
| 3 | Quitar un premio al jugador 1 | | | | | |
| 4 | Mazo del jugador 0 en 0 | | | | | |
| 5 | Mazo del jugador 1 en 0 | | | | | |
| 6 | PV del activo del jugador 0 en 10 | | | | | |
| 7 | PV del activo del jugador 1 en 10 | | | | | |
| 8 | Vaciar la banca del jugador 0 | | | | | |
| 9 | 3 energías más al activo del jugador 0 | | | | | |
| 10 | 2 Pokémon más en la banca del jugador 0 | | | | | |
| L1 | *(libre)* | | | | | |
| L2 | *(libre)* | | | | | |
| L3 | *(libre)* | | | | | |

### Daniel

Probabilidad inicial del jugador 0: ____ %

| # | Cambio | Esperada | Antes | Después | ¿Tiene sentido? | Comentario |
|---|---|---|---|---|---|---|
| 1 | Quitar un premio al jugador 0 | | | | | |
| 2 | Agregar un premio al jugador 0 | | | | | |
| 3 | Quitar un premio al jugador 1 | | | | | |
| 4 | Mazo del jugador 0 en 0 | | | | | |
| 5 | Mazo del jugador 1 en 0 | | | | | |
| 6 | PV del activo del jugador 0 en 10 | | | | | |
| 7 | PV del activo del jugador 1 en 10 | | | | | |
| 8 | Vaciar la banca del jugador 0 | | | | | |
| 9 | 3 energías más al activo del jugador 0 | | | | | |
| 10 | 2 Pokémon más en la banca del jugador 0 | | | | | |
| L1 | *(libre)* | | | | | |
| L2 | *(libre)* | | | | | |
| L3 | *(libre)* | | | | | |

### Sebastián

Probabilidad inicial del jugador 0: ____ %

| # | Cambio | Esperada | Antes | Después | ¿Tiene sentido? | Comentario |
|---|---|---|---|---|---|---|
| 1 | Quitar un premio al jugador 0 | | | | | |
| 2 | Agregar un premio al jugador 0 | | | | | |
| 3 | Quitar un premio al jugador 1 | | | | | |
| 4 | Mazo del jugador 0 en 0 | | | | | |
| 5 | Mazo del jugador 1 en 0 | | | | | |
| 6 | PV del activo del jugador 0 en 10 | | | | | |
| 7 | PV del activo del jugador 1 en 10 | | | | | |
| 8 | Vaciar la banca del jugador 0 | | | | | |
| 9 | 3 energías más al activo del jugador 0 | | | | | |
| 10 | 2 Pokémon más en la banca del jugador 0 | | | | | |
| L1 | *(libre)* | | | | | |
| L2 | *(libre)* | | | | | |
| L3 | *(libre)* | | | | | |

## 4. Resultado

*Se completa después de las tres sesiones.*

- Cambios definidos con dirección igual a la esperada: __ de 30.
- Cambios definidos que el equipo juzgó con sentido de juego: __ de 30.
- Cambios libres con sentido de juego: __ de 9.
- Direcciones inesperadas y explicación (por ejemplo, una asociación del modelo que no es causal, o un estado editado que quedó fuera del dominio):
