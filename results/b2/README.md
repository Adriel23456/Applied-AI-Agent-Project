# B2: regresión logística regularizada

Se seleccionó una sola configuración, `C=0.1`, para A, B y C. Los archivos en `final/escenario_X/` son **tres ajustes de esa misma configuración**, cada uno entrenado con todo el `train` propio del escenario para poder evaluar ese protocolo. No son tres configuraciones seleccionadas ni tres modelos que se deban usar en la aplicación. La elección del único artefacto para la aplicación depende del uso previsto y se hará al integrar el modelo.

Los `.joblib` se recuperaron del ZIP descargado desde Drive y sus metadatos se contrastaron con los CSV de validación, sin volver a entrenar. La [verificación y los hashes](../../docx/03Evidence/28-10-26_VerificacionFinalistasB2B3.json) registran el alcance de esa revisión.

| Escenario | Partidas usadas en `train` | Fracción de `train` | Convergencia |
|---|---:|---:|---|
| A | 33 066 | 100 % | No alcanzada |
| B | 27 643 | 100 % | No alcanzada |
| C | 33 013 | 100 % | No alcanzada |

El ajuste incremental se cerró tras 600 épocas sin alcanzar la tolerancia de gradiente de 0.001. Esa limitación se conserva al interpretar B2. Métricas de `val`, globales y por etapa, en `final/escenario_X/b2_val_X.csv`; la decisión está documentada en `docx/03Evidence/25-10-26_B2SeleccionFinalC.md`.

## Demostración de fuga por fila

`demo_fuga/escenario_X/` contiene las salidas originales de la comparación (corrida `20261029T013037Z`, registrada en cada `registro.json`). Se usó una muestra de 200 partidas de `train` por escenario, `C=0.1`, semilla 2026 y LBFGS; es un diagnóstico pequeño y no reemplaza el B2 final entrenado con SGD.

| Escenario | AUC, división por fila | AUC, división por partida | Partidas compartidas por la división por fila | Partidas compartidas por la división por partida |
|---|---:|---:|---:|---:|
| A | 0.7753 | 0.7400 | 199 | 0 |
| B | 0.8056 | 0.8150 | 200 | 0 |
| C | 0.7884 | 0.6758 | 200 | 0 |

La división por fila compartió partidas entre ajuste y evaluación en los tres escenarios. La dirección de la diferencia de AUC no fue igual en todos: la división por fila dio un AUC menor en B. Las evaluaciones usan particiones distintas y una muestra pequeña; esta demostración identifica la fuga, pero no estima una inflación universal ni reemplaza una comparación emparejada.

## Archivos

```text
results/b2/
├── README.md
├── exploracion_muestra/        # piloto con una muestra de 5000 partidas de train
│   ├── b2_cv_folds.csv         # CV por pliegue y etapa, 9 valores de C (1e-4 a 1e4)
│   ├── b2_cv_summary.csv       # promedio y desviación de esos pliegues por C
│   └── b2_val_finalists.csv    # finalistas del piloto medidas en val
├── seleccion_c/                # CV con TODO train: C=0.1 contra C=1.0
│   ├── b2_cv_A.csv             # pliegues de A (uno por fila, con convergencia)
│   ├── b2_cv_B.csv
│   ├── b2_cv_C.csv
│   └── b2_cv_summary.csv       # resumen de los tres escenarios
├── final/escenario_X/          # ajuste elegido C=0.1 con todo el train de X
│   ├── b2_val_X.csv            # métricas de val, globales y por etapa
│   └── b2_X_C0.1.joblib        # modelo + escalador + metadatos
└── demo_fuga/escenario_X/      # división por fila contra división por partida
    ├── metricas.csv
    ├── solapamiento.csv
    ├── config.json
    └── registro.json
```

El piloto (`exploracion_muestra/`) solo sirvió para acotar el rango de `C`; la decisión se tomó con `seleccion_c/`, que usa todo `train`. Antes de la reorganización estos dos grupos convivían en la misma carpeta y `seleccion_c/b2_cv_summary.csv` se llamaba `b2_cv_summary (1).csv`.
