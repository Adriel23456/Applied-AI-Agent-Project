# Resultados de los modelos

Esta carpeta es la **copia de trabajo** de los resultados. La copia oficial vive en el dataset
privado de Kaggle del equipo, `adrielchavessalazar/ptcg-wp-tablas`, junto a las tablas procesadas.
En Colab los resultados se bajan a `/content/resultados/` con la misma estructura de carpetas, y
solo los archivos que una celda necesita (`ptcg_wp.store.listo`).

## Nombres en Kaggle

Kaggle no guarda subcarpetas, así que cada ruta se aplana: `results/` + ruta con `/` cambiado por `__`.

| Ruta aquí | Archivo en Kaggle |
|---|---|
| `b4/final/escenario_A/b4_auc_CVtrial20.joblib` | `results__b4__final__escenario_A__b4_auc_CVtrial20.joblib` |
| `b0_b1/metricas_B0_B1.csv` | `results__b0_b1__metricas_B0_B1.csv` |

`results__indice.csv` lista cada archivo del dataset (tablas y resultados) con su ruta, tamaño,
SHA-256, fecha y commit. Cada descarga se compara contra ese SHA-256.

## Estructura

| Carpeta | Qué contiene | Cuaderno que la produce |
|---|---|---|
| `b0_b1/` | B0 (prevalencia) y B1 (heurística de recursos): métricas de `val` y parámetros | `02_baselines_B0_B1` |
| `b2/exploracion_muestra/` | Piloto de B2 con 5000 partidas: 9 valores de `C` | (histórico) |
| `b2/seleccion_c/` | CV de B2 con todo `train`: `C=0.1` contra `C=1.0` | (histórico) |
| `b2/final/escenario_X/` | B2 elegido (`C=0.1`) ajustado con todo `train` de X: métricas de `val` y `.joblib` | `03_baseline_B2` |
| `b2/demo_fuga/escenario_X/` | Demostración de fuga: división por fila contra por partida | `03_baseline_B2` |
| `b3/busqueda/` | CV con Optuna de árbol y bosque; finalistas de B y C | (histórico) |
| `b3/final/escenario_X/` | Bosque elegido ajustado con todo `train` de X: métricas de `val` y `.joblib` | `04_baseline_B3` |
| `b4/busqueda/` | Búsqueda única de B4 (Optuna, 20 trials): pruebas, finalista y estudio | `05_baseline_B4` |
| `b4/final/escenario_X/` | B4 final (tope 4000) por escenario: métricas de `val`, manifiesto y `.joblib` | `05_baseline_B4` |
| `b4/historico_tope_2000/escenario_X/` | Registro de la corrida con tope 2000 (sin modelos) | (histórico) |
| `resumen/` | Tabla comparativa B0–B3 en `val` y registro histórico de B2/B3 | (manual) |

Carpetas que crearán los experimentos pendientes de `05_baseline_B4`: `lightgbm/`,
`b4/ablaciones/escenario_X/` y `b4/h2/escenario_X/`.

Reglas de nombres: carpetas en minúscula; `escenario_A|B|C` para todo lo que depende del escenario;
`busqueda/` para la selección de hiperparámetros, `final/` para el modelo elegido ajustado con todo
`train`; sin carpetas con fecha (la fecha y el commit van dentro de `registro.json` y del índice);
sin duplicados `(1)`, `(2)`. Los nombres de archivo son los que escribe el código de `src/ptcg_wp`,
para que una corrida nueva produzca exactamente los mismos nombres.

## Correspondencia con la estructura anterior

| Antes | Ahora |
|---|---|
| `baseline0_1/20261029T005435Z/*` | `b0_b1/*` |
| `baseline2/b2_cv_folds.csv`, `b2_cv_summary.csv`, `b2_val_finalists.csv` | `b2/exploracion_muestra/` (mismos nombres) |
| `baseline2/b2_cv_A.csv`, `_B`, `_C` | `b2/seleccion_c/` |
| `baseline2/b2_cv_summary (1).csv` | `b2/seleccion_c/b2_cv_summary.csv` |
| `baseline2/b2_val_X.csv` | `b2/final/escenario_X/b2_val_X.csv` |
| `baseline2/evaluacion/escenario_X/b2_X_C0.1.joblib` | `b2/final/escenario_X/b2_X_C0.1.joblib` |
| `baseline2/demo_fuga/20261029T013037Z/escenario_X/` | `b2/demo_fuga/escenario_X/` |
| `baseline3/b3_cv_X.csv` | `b3/busqueda/b3_cv_X.csv` |
| `baseline3/b3_cv_A (1).csv` | eliminado (copia idéntica de `b3_cv_A.csv`) |
| `baseline3/b3_candidatas.csv` | `b3/busqueda/b3_candidatas_B.csv` |
| `baseline3/b3_candidatas (1).csv` | `b3/busqueda/b3_candidatas_C.csv` |
| `baseline3/b3_candidatas (2).csv` | eliminado (copia idéntica de la de C) |
| `baseline3/b3_val_X.csv` | `b3/final/escenario_X/b3_val_X.csv` |
| `baseline3/evaluacion/escenario_X/*.joblib` | `b3/final/escenario_X/` |
| `baseline4/busqueda/` | `b4/busqueda/` |
| `baseline4/final_4000/` | `b4/final/` |
| `baseline4/registro_tope_2000/` | `b4/historico_tope_2000/` |
| `resumen_baselines/` | `resumen/` (columna `archivo_fuente` y rutas del JSON actualizadas) |
