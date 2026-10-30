# Resultados de B3: árbol y bosque aleatorio

B3 compara un árbol de decisión (`B3_arbol`) con un bosque aleatorio
(`B3_bosque`). Este README resume las finalistas y los resultados disponibles
en A, B y C. No se ejecutó una nueva búsqueda ni se usó `test` para esta
comparación.

## Configuración global seleccionada para B3

La finalista por menor log loss de CV usa estos hiperparámetros en los tres
escenarios:

| Hiperparámetro | Valor |
|---|---:|
| `criterion` | `gini` |
| `max_depth` | 12 |
| `min_samples_leaf` | 20 |
| `n_estimators` | 25 |
| `max_features` | 0.5 |

En los CSV de validación aparece como `seleccionada_por=log_loss`, `trial=1`.
La misma configuración se evaluó en los tres escenarios.

## Resultados en `val`

Las métricas son globales, calculadas sobre las partidas de validación de cada
escenario. Se muestran por separado, según el contrato de modelado.

| Escenario | Partidas de `val` | AUC | Log loss | Brier |
|---|---:|---:|---:|---:|
| A | 8 255 | 0.8029 | 0.5343 | 0.1808 |
| B | 5 191 | 0.7609 | 0.5727 | 0.1970 |
| C | 8 239 | 0.8063 | 0.5312 | 0.1794 |

### Comparación de finalistas del bosque por escenario

Cada celda muestra la métrica de `val` de la finalista escogida en CV por la
métrica de la fila. Menor log loss y Brier es mejor; mayor AUC es mejor.

| Escenario | Finalista de CV | Hiperparámetros principales | AUC `val` | Log loss `val` | Brier `val` |
|---|---|---|---:|---:|---:|
| A | AUC | entropy, profundidad 12, hoja 50, 50 árboles, `max_features=0.25` | 0.8005 | 0.5391 | 0.1826 |
| A | Log loss | gini, profundidad 12, hoja 20, 25 árboles, `max_features=0.5` | **0.8029** | **0.5343** | **0.1808** |
| A | Brier | gini, profundidad 12, hoja 20, 50 árboles, `max_features=0.25` | 0.8016 | 0.5383 | 0.1821 |
| B | AUC | entropy, profundidad 12, hoja 50, 50 árboles, `max_features=0.25` | 0.7614 | 0.5714 | 0.1966 |
| B | Log loss | gini, profundidad 12, hoja 20, 25 árboles, `max_features=0.5` | 0.7609 | 0.5727 | 0.1970 |
| B | Brier | gini, profundidad 12, hoja 20, 50 árboles, `max_features=0.25` | **0.7621** | **0.5714** | **0.1964** |
| C | AUC | entropy, profundidad 12, hoja 50, 100 árboles, `max_features=0.25` | 0.8043 | 0.5357 | 0.1811 |
| C | Log loss | gini, profundidad 12, hoja 20, 25 árboles, `max_features=0.5` | **0.8063** | **0.5312** | **0.1794** |
| C | Brier | gini, profundidad 12, hoja 20, 50 árboles, `max_features=0.25` | 0.8038 | 0.5364 | 0.1812 |

La configuración elegida lidera las tres métricas en A y C. En B, la finalista
por Brier tiene mayor AUC y menor Brier; la finalista por AUC tiene un log loss
ligeramente menor. Para elegir una sola configuración común, el protocolo usa
el macro-promedio simple del **AUC global en `val`**, dando igual peso a A, B y
C. Este es un criterio interno de selección, no un resultado de desempeño que
se reporte en lugar de las métricas por escenario.

| Familia y finalista común de CV | AUC `val` A | AUC `val` B | AUC `val` C | Macro-AUC usado para selección |
|---|---:|---:|---:|---:|
| Árbol, log loss | 0.7740 | 0.7343 | 0.7791 | 0.7624 |
| Árbol, Brier | 0.7767 | 0.7344 | 0.7810 | 0.7641 |
| Bosque, Brier | 0.8016 | 0.7621 | 0.8038 | 0.7892 |
| **Bosque, log loss (elegida)** | **0.8029** | **0.7609** | **0.8063** | **0.7901** |

Solo se compararon finalistas con hiperparámetros idénticos en A, B y C; por
eso las finalistas por AUC, que no comparten `n_estimators` entre escenarios,
no integran esta comparación global. Se escogió el bosque por log loss: entre
las configuraciones comunes disponibles, tiene el mayor macro-AUC observado.
La selección usa los valores disponibles, no demuestra significancia
estadística ni que esta búsqueda haya encontrado el óptimo global.

La configuración común se ajusta por separado con el `train` de A, B y C para
respetar cada partición. Eso genera artefactos de evaluación distintos, pero
no significa que se hayan elegido hiperparámetros diferentes por escenario.
Qué artefacto se usará para la aplicación final depende del escenario de uso y
se resolverá al integrar el modelo.

## Alcance de la conclusión

- La elección usa los resultados de CV para formar las finalistas y los CSV de
  `val` para compararlas, de acuerdo con el protocolo acordado.
- No se hizo el bootstrap emparejado por partida. La selección sigue el
  criterio macro-AUC descrito arriba, pero las diferencias pequeñas no se
  presentan como estadísticamente concluyentes. No se repitió la búsqueda.
- `test` permanece reservado para la evaluación final del proyecto.
- Los CSV y los metadatos de los `.joblib` recuperados confirman que la configuración se ajustó con todo el `train` propio de cada escenario para medir `val`. Los modelos están en `final/escenario_X/`. Son artefactos para evaluar tres protocolos; el modelo único para la aplicación se decidirá al integrar el sistema. La [verificación y los hashes](../../docx/03Evidence/28-10-26_VerificacionFinalistasB2B3.json) se hicieron inspeccionando metadatos sin ejecutar predicciones.

## Archivos disponibles

```text
results/b3/
├── README.md
├── busqueda/
│   ├── b3_cv_A.csv             # pliegues CV de árbol y bosque en A (todas las pruebas de Optuna)
│   ├── b3_cv_B.csv
│   ├── b3_cv_C.csv
│   ├── b3_candidatas_B.csv     # finalistas de CV de B (una por modelo y métrica)
│   └── b3_candidatas_C.csv     # finalistas de CV de C
└── final/escenario_X/
    ├── b3_val_X.csv            # todas las finalistas medidas en val de X
    └── b3_X_B3_bosque_log_loss.joblib   # bosque elegido ajustado con todo el train de X
```

No existe `b3_candidatas_A.csv`: ese archivo no se conservó en la corrida original. Las finalistas de A y sus hiperparámetros sí aparecen en `final/escenario_A/b3_val_A.csv` y los pliegues en `busqueda/b3_cv_A.csv`.

Reorganización: `b3_candidatas.csv` pasó a `b3_candidatas_B.csv` y `b3_candidatas (1).csv` a `b3_candidatas_C.csv`. Se eliminaron `b3_candidatas (2).csv` y `b3_cv_A (1).csv`, que eran copias byte a byte (mismo MD5) de `b3_candidatas (1).csv` y `b3_cv_A.csv`, creadas al descargar dos veces desde el navegador.

## Protocolo registrado

- La búsqueda usa pliegues de `GroupKFold` agrupados por `game_id` dentro de
  `train`; `val` se reserva para comparar las finalistas y `test` no participa
  en la selección.
- Los CSV de `val` indican `muestreo=todo_train` y `fraccion_train=1.0` para los
  ajustes: se usaron todas las partidas disponibles de `train` en cada
  escenario.
- `val` contiene 8 255 partidas en A, 5 191 en B y 8 239 en C.
- Las métricas por etapa (`inicio`, `medio`, `final`) también están en cada
  `b3_val_*.csv`; la decisión resumida aquí se basa en las métricas globales.
- Los modelos se generaron con scikit-learn 1.7.2. El registro indica semilla base 2026; el `random_state` efectivo de estos bosques es 2030, por la posición de la candidata en el ajuste original.
