# Resultados de B0 y B1

Corrida `20261029T005435Z`. Ejecutada con semilla 2026 y commit `b8ec38bdc2735010ea63faf47e790a59d8581ac8`; el árbol de trabajo de Colab estaba limpio. Se ajustó usando `train` y se evaluó en `val`, por separado en A, B y C. No se usaron `calib` ni `test`.

Cada partida tiene peso total uno en ajuste y en métricas; en cada etapa los pesos se recalculan entre las partidas representadas. Las métricas globales y por etapa, con cantidad de estados y partidas, están en `metricas_B0_B1.csv`. La configuración y parámetros ajustados están en `ajustes_B0_B1.csv`; el registro completo está en `registro.json`.

## Métricas globales de `val`

| Escenario | Modelo | AUC | Log loss | Brier | Partidas |
|---|---|---:|---:|---:|---:|
| A | B0 | 0.5000 | 0.6904 | 0.2486 | 8255 |
| A | B1 | 0.6768 | 0.6421 | 0.2253 | 8255 |
| B | B0 | 0.5000 | 0.6929 | 0.2499 | 5191 |
| B | B1 | 0.6677 | 0.6546 | 0.2300 | 5191 |
| C | B0 | 0.5000 | 0.6902 | 0.2485 | 8239 |
| C | B1 | 0.6714 | 0.6454 | 0.2268 | 8239 |

Los escenarios responden a protocolos distintos: A partidas nuevas, B días posteriores y C arquetipos reservados. Se reportan individualmente; no se promedian.

## Ajustes

| Escenario | Prevalencia B0 en `train` | `hp_unit` de B1 | Intercepto B1 | Pendiente B1 |
|---|---:|---:|---:|---:|
| A | 0.5367 | 169.95 | 0.1359 | 0.1425 |
| B | 0.5491 | 163.19 | 0.1882 | 0.1600 |
| C | 0.5384 | 164.71 | 0.1340 | 0.1362 |

B0 predice la prevalencia de victoria observada en `train`. B1 usa la puntuación adoptada `(opp_prizes - own_prizes) + diff_total_hp / hp_unit + diff_bench_n` y una transformación logística de un predictor, ajustada con `train`.

**Decisión posterior:** se adopta esta fórmula como B1 para la rama 04. La decisión se tomó al cerrar los entregables; el `registro.json` original conserva su estado de propuesta para reflejar fielmente lo que se sabía al ejecutar la corrida. El ajuste tuvo un máximo de seis iteraciones de Newton y no registró un indicador de convergencia; esa limitación acompaña sus resultados. Véase [la decisión y el resumen](../resumen_baselines/README.md).

## Duración

| Escenario | Segundos |
|---|---:|
| A | 44.78 |
| B | 37.99 |
| C | 40.98 |

Total por escenario: 123.74 segundos. Los tiempos registrados son solo de los ajustes/evaluaciones por escenario, no incluyen instalación o descarga de datos.
