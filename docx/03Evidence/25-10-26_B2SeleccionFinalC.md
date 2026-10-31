# B2: selección final de regularización

**Fecha:** 25 de octubre de 2026  
**Decisión:** usar `C = 0.1` para B2 en los escenarios A, B y C.

## Alcance y datos usados

La decisión usa exclusivamente `train` y `val`. Primero se evaluaron `C=0.1`
y `C=1.0` mediante cinco pliegues de `GroupKFold` por `game_id` dentro de
`train`. Después, cada candidata se reajustó con todas las partidas de `train`
y se evaluó una vez en la partición fija `val`.

Los archivos revisados fueron `b2_cv_A.csv`, `b2_cv_B.csv`, `b2_cv_C.csv`,
`b2_cv_summary (1).csv`, `b2_val_A.csv`, `b2_val_B.csv` y `b2_val_C.csv`.
Los tres primeros CSV de validación contienen las métricas globales y por
etapa; la tabla siguiente usa únicamente la fila `etapa=global`.

La ejecución usó `scikit-learn=1.7.2`, semilla 2026, lotes de 32,768,
`eta0=0.05`, hasta 600 épocas y tolerancia de gradiente `0.001`.

## Resultado de validación

| Escenario | C | AUC | Log loss | Brier |
|---|---:|---:|---:|---:|
| A | 0.1 | **0.760739** | **0.577387** | **0.197521** |
| A | 1.0 | 0.760685 | 0.577514 | 0.197549 |
| B | 0.1 | **0.728113** | **0.630855** | **0.214018** |
| B | 1.0 | 0.727825 | 0.632428 | 0.214302 |
| C | 0.1 | **0.760264** | **0.578559** | **0.197693** |
| C | 1.0 | 0.760208 | 0.578684 | 0.197717 |

`C=0.1` tiene el mayor AUC y las menores pérdidas globales en los tres
escenarios. La diferencia de AUC en A y C es muy pequeña; en esos casos la
decisión también está respaldada por menor log loss y menor Brier. En B la
ventaja de `C=0.1` aparece en las tres métricas con una magnitud mayor.

La comparación emparejada por remuestreo de partidas de `val`, recomendada en
los acuerdos técnicos para cuantificar incertidumbre, no se ejecutó porque los
CSV disponibles contienen métricas agregadas y no las predicciones por partida.
Por ello, esta decisión no afirma una diferencia estadísticamente demostrada
en A o C; fija la configuración operativa que rindió mejor en `val`.

## Convergencia

Ninguno de los diez ajustes de CV por escenario ni de los dos reajustes de
finalistas alcanzó el umbral de gradiente `0.001` antes de las 600 épocas.
Los gradientes de los modelos reajustados con todo `train` quedaron entre
0.00349 y 0.00717. Esto indica que el optimizador no certificó el mínimo del
objetivo según el criterio configurado. No impide comparar las predicciones
que efectivamente produjo ni obliga a aumentar indefinidamente el número de
épocas.

Se decide cerrar B2 con el presupuesto ya invertido. Las métricas y la falta de
convergencia deben informarse juntas al presentar el baseline; no se usará
`test` para volver a elegir `C` ni para intentar resolver este diagnóstico.

## Artefactos y siguiente paso

La evaluación de finalistas ya reajustó ambos valores de `C` con todo `train`
y guardó sus modelos en los checkpoints de B2. El artefacto seleccionado es el
de nombre `b2_<escenario>_C0.1.joblib` dentro de cada carpeta
`model_checkpoints/b2/finalists_c_1_0_0_1_600/escenario_<escenario>` de Drive.
Ese modelo se conserva como el baseline B2 seleccionado para las comparaciones
posteriores; no se repite la búsqueda ni se aumentan sus épocas.

El siguiente paso de cómputo es continuar B3 desde sus checkpoints `efficient_v2`.
Al terminar B3 seguirá B4. Cuando estén seleccionados los modelos que se van a
comparar, `calib` se usará para el análisis o ajuste de calibración y `test`
se reservará para la única evaluación final definida por el proyecto.
