# Resultados de B4 (modelo principal)

B4 = potenciación del gradiente por histogramas (`HistGradientBoostingClassifier`, scikit-learn 1.7.2),
entrenada con `notebooks/05_entrenamiento_B4_independiente.ipynb`. La copia exacta de ese cuaderno se preserva en `docx/03Evidence/05_entrenamiento_B4_independiente_original.ipynb`; el cuaderno de trabajo `notebooks/05_baseline_B4.ipynb` recupera las celdas de búsqueda y ajuste final con ejecución explícita.

Estos archivos se **copiaron manualmente** desde Google Drive
(`MyDrive/Applied-AI-Agent-Project/model_checkpoints/b4_independiente/busqueda_v3/`) para dejar
versionados los resultados y los modelos finales. `test` no se usó: estas métricas son de `val`.

## Contenido

```text
results/baseline4/
├── README.md
├── busqueda/
│   ├── b4_candidatas.csv
│   ├── b4_cv_trials.csv
│   └── b4_optuna.sqlite3
├── final_4000/
│   ├── escenario_A/  (b4_auc_CVtrial20.joblib, b4_val_finalistas.csv, b4_val_manifest.json)
│   ├── escenario_B/  (b4_auc_CVtrial20.joblib, b4_val_finalistas.csv, b4_val_manifest.json)
│   └── escenario_C/  (b4_auc_CVtrial20.joblib, b4_val_finalistas.csv, b4_val_manifest.json)
└── registro_tope_2000/
    ├── escenario_A/  (b4_val_finalistas.csv, b4_val_manifest.json)
    ├── escenario_B/  (b4_val_finalistas.csv, b4_val_manifest.json)
    └── escenario_C/  (b4_val_finalistas.csv, b4_val_manifest.json)
```

| Archivo | Contenido |
|---|---|
| `busqueda/b4_candidatas.csv` | Finalistas de la búsqueda con hiperparámetros y métricas de validación cruzada |
| `busqueda/b4_cv_trials.csv` | Cada trial y cada pliegue de la búsqueda |
| `busqueda/b4_optuna.sqlite3` | Estudio de Optuna completo, con su manifiesto de configuración |
| `final_4000/escenario_X/b4_auc_CVtrial20.joblib` | **Modelo final de B4** del escenario X |
| `final_4000/escenario_X/b4_val_finalistas.csv` | Métricas en `val` del modelo final, globales y por etapa |
| `final_4000/escenario_X/b4_val_manifest.json` | Configuración exacta del reentrenamiento final |
| `registro_tope_2000/escenario_X/...` | Métricas y configuración de la corrida con tope 2000 (solo registro) |

## Protocolo

- **Búsqueda única** de hiperparámetros con Optuna (TPE), 20 trials, validación cruzada de 3 pliegues
  agrupada por partida.
- La búsqueda usa solo las **11 285 partidas que son `train` en A, B y C a la vez**: ningún
  hiperparámetro vio partidas de `val`, `calib` o `test` de ningún escenario.
- Un solo estudio optimiza log loss. AUC y Brier se registran por trial.
- Parada temprana (paciencia 30) sobre un 15 % de partidas de vigilancia separado.
- Cada fila pesa 1/n de su partida, así que cada partida cuenta igual en el ajuste y en las métricas.
- 62 características: sin ids de carta y sin columnas meta.
- Semilla 2026.

## Hiperparámetros elegidos (trial 20)

Fue el mejor trial en las tres métricas, así que hay una sola finalista.

| Parámetro | Valor |
|---|---|
| `learning_rate` | 0.06943 |
| `max_leaf_nodes` | 31 |
| `min_samples_leaf` | 50 |
| `l2_regularization` | 4.2503 |

Validación cruzada sobre las partidas de búsqueda: **AUC 0.8378**, log loss 0.4880, Brier 0.1632.

## Resultados finales en `val` (`final_4000/`)

Cada escenario reentrenó la finalista con todo su `train`. La parada temprana decidió el número de
árboles con un tope de 4000 que no se alcanzó.

| Escenario | Árboles | AUC | Log loss | Brier |
|---|---|---|---|---|
| A (partidas nuevas) | 2888 | 0.8346 | 0.4916 | 0.1651 |
| B (días posteriores) | 2370 | 0.7863 | 0.5576 | 0.1898 |
| C (arquetipos reservados) | 2714 | 0.8355 | 0.4918 | 0.1647 |

Las métricas por etapa (inicio, medio y final) están en cada `b4_val_finalistas.csv`.

## Registro de estabilidad (`registro_tope_2000/`)

Una primera corrida con tope de 2000 árboles alcanzó el tope en los tres escenarios. Se repitió solo
el reentrenamiento final con tope 4000; las métricas en `val` cambiaron menos de 0.002. Se usan los
modelos de `final_4000` en los tres escenarios, con una sola regla para todos. Los modelos de la
corrida con tope 2000 no se versionan.

## Cómo cargar los modelos

Cada `.joblib` es un diccionario con `model` (el clasificador), `features` (las 62 columnas en el
orden en que el modelo las espera), `n_iter_vigilancia`, `candidata` y `version_sklearn`.
Para cargarlos hace falta **scikit-learn 1.7.2** (fijado en `requirements.txt`).

```python
# Carga los modelos finales de B4 desde el repo (despues de clonar o hacer pull)
from pathlib import Path
import joblib

base = Path("/content/repo/results/baseline4/final_4000")
b4 = {s: joblib.load(base / f"escenario_{s}" / "b4_auc_CVtrial20.joblib") for s in ("A", "B", "C")}
print({s: len(m["features"]) for s, m in b4.items()})  # esperado: 62 caracteristicas por modelo

# Probabilidad de victoria del jugador que actua para filas utiles de un escenario:
# prob = b4["A"]["model"].predict_proba(X[b4["A"]["features"]])[:, 1]
```

Para regenerarlos desde cero, ejecutar el cuaderno `05` en un servidor CPU + High-RAM.