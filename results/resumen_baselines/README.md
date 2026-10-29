# Resumen de B0 a B3 en validación

Este resumen reúne resultados existentes, sin entrenar modelos nuevos. [metricas_val_B0_B3.csv](metricas_val_B0_B3.csv) contiene 48 filas: A/B/C, B0/B1/B2/B3 y métricas globales y por etapa. Cada fila señala su CSV de origen. Los conteos de estados y partidas coinciden entre modelos dentro de cada escenario y etapa; esa comprobación no sustituye una comparación emparejada de predicciones.

| Escenario | Modelo | AUC | Log loss | Brier |
|---|---|---:|---:|---:|
| A | B0 | 0.5000 | 0.6904 | 0.2486 |
| A | B1 | 0.6768 | 0.6421 | 0.2253 |
| A | B2 | 0.7607 | 0.5774 | 0.1975 |
| A | B3 | 0.8029 | 0.5343 | 0.1808 |
| B | B0 | 0.5000 | 0.6929 | 0.2499 |
| B | B1 | 0.6677 | 0.6546 | 0.2300 |
| B | B2 | 0.7281 | 0.6309 | 0.2140 |
| B | B3 | 0.7609 | 0.5727 | 0.1970 |
| C | B0 | 0.5000 | 0.6902 | 0.2485 |
| C | B1 | 0.6714 | 0.6454 | 0.2268 |
| C | B2 | 0.7603 | 0.5786 | 0.1977 |
| C | B3 | 0.8063 | 0.5312 | 0.1794 |

Las filas globales mostradas son de `val`, ponderadas por partida. Las etapas recalculan los pesos entre las partidas presentes en cada etapa. A, B y C responden preguntas diferentes y se informan por separado. Estas son diferencias observadas, sin intervalos de confianza ni prueba emparejada. `calib` y `test` quedan reservados para la etapa final.

## Decisión sobre B1

Al cerrar los entregables de esta rama se adopta la fórmula ya ejecutada:

`score = (opp_prizes - own_prizes) + diff_total_hp / hp_unit + diff_bench_n`

`hp_unit` es el promedio de PV máximos positivos de ambos Pokémon activos, ponderado por partida en `train`. Una regresión logística de un solo predictor ajusta intercepto y pendiente en `train`; no aprende pesos separados para los tres componentes. Se adopta por ser una referencia simple, explícita y basada en recursos observables; sus escalas relativas son convenciones, no una estimación causal. Esta decisión técnica se tomó después de la corrida, dentro del trabajo delegado para cerrar los pendientes. El registro original conserva el estado `propuesta_pendiente_confirmacion` que tenía al ejecutarse y sus métricas de `val` no deben interpretarse como una prueba independiente de esa decisión.

El ajuste de Newton tenía un máximo de seis iteraciones y no guardó si alcanzó la tolerancia. No puede afirmarse convergencia a partir de los archivos disponibles. Los datos originales auditados no tenían `game_id` repetidos entre días; por eso el cálculo de pesos diario es coherente con ese corpus. Si el corpus cambia, debe comprobarse ese invariante antes de repetir B0/B1.

## Fuentes y trazabilidad

- **B0/B1:** [corrida original](../baseline0_1/README.md), semilla 2026, commit `b8ec38bdc2735010ea63faf47e790a59d8581ac8`, con duración por escenario en su `registro.json`. Las métricas y parámetros provienen de esa corrida.
- **B2:** configuración común `C=0.1`, semilla 2026, scikit-learn 1.7.2, 600 épocas. No alcanzó el umbral de convergencia; véase [B2](../baseline2/README.md). Los CSV de ajuste disponibles no registran tiempo de ejecución ni commit de entrenamiento; no se reconstruyen esos valores por inferencia.
- **B3:** bosque `gini`, profundidad 12, mínimo 20 por hoja, 25 árboles y `max_features=0.5`; semilla base 2026, `random_state` efectivo 2030, scikit-learn 1.7.2. La selección común y sus límites se describen en [B3](../baseline3/README.md). Los CSV de ajuste disponibles no registran tiempo de ejecución ni commit de entrenamiento.
- Los tres ajustes de B2 y B3 corresponden a la configuración seleccionada entrenada con el `train` propio de cada escenario para evaluarlo. Sus [metadatos y hashes](../../docx/03Evidence/28-10-26_VerificacionFinalistasB2B3.json) se verificaron sin recalcular predicciones. La decisión del único artefacto para la aplicación queda para la integración final.
- La [demostración de fuga de B2](../baseline2/README.md#demostración-de-fuga-por-fila) contiene registros, métricas y solapamientos de los tres escenarios. La fuga se observa como partidas compartidas entre los lados de la división por fila; la diferencia de AUC cambia de signo entre escenarios.
