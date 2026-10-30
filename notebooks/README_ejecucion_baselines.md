# Ejecución de los cuadernos de baselines

Todos los resultados (CSV, JSON, SQLite y `.joblib`) viven en el dataset **privado** de Kaggle
`adrielchavessalazar/ptcg-wp-tablas`, junto a las tablas procesadas. No se usa Google Drive y los
resultados no se versionan en el repo. La estructura y el significado de cada archivo están en
`results/README.md` (también publicado en Kaggle como `results__README.md`).

## Cómo funciona cada cuaderno

1. **Celda 1 (preparación):** clona o actualiza el repo, instala dependencias, **muestra núcleos de
   CPU y RAM**, configura Kaggle y baja a `/content/datos` solo las tablas que falten. No depende de
   `00_arranque` ni de otro cuaderno.
2. **Cada celda que entrena** declara la lista exacta de archivos que produce y llama a
   `store.asegurar(archivos, entrenar, mensaje)`:
   - si **todos** están en Kaggle, los baja a `/content/resultados/<ruta>` (verificando SHA-256) y
     termina sin entrenar;
   - si falta alguno, entrena, comprueba que se crearon y publica una versión nueva del dataset.
     La publicación conserva las tablas y todos los resultados anteriores.
   Lo que depende del escenario se revisa y publica **por escenario**.
3. **No hay interruptores** (`EJECUTAR_... = False`, `CREAR`, `CONSTRUIR`): ejecutar una celda
   hace lo que hace falta.

Para trabajar en paralelo: si dos personas publican al mismo tiempo, la versión que termina
después puede no incluir lo que subió la otra. Avisen en el grupo antes de ejecutar celdas que
entrenan algo nuevo. Cada publicación vuelve a subir las tablas (unos minutos) y Kaggle tarda unos
minutos en mostrar la versión nueva a otros servidores.

## Orden y tiempos

| Cuaderno | Celdas | Si todo está en Kaggle | Si falta |
|---|---|---|---|
| `02_baselines_B0_B1` | 1 → 3 → 5 | segundos | ~2 min |
| `03_baseline_B2` | 1 → 3 → 5 → 7 | segundos | demo de fuga ~1 min por escenario; B2 final varias horas por escenario |
| `04_baseline_B3` | 1 → 3 → 5 | segundos | bosque final por escenario |
| `05_baseline_B4` | 1 → 3 → 5 | segundos | búsqueda ~2 h 20 min; final ~50 min por escenario (8 núcleos) |
| `05_baseline_B4` (experimentos) | 7 → 8 (LightGBM), 10 (ablaciones), 12 (H2), 14 (resumen) | segundos | horas |

En `05`, la celda 5 usa la finalista de la celda 3. LightGBM, ablaciones y H2 ya están en Kaggle:
al ejecutarlas solo se bajan. Su código está en `src/ptcg_wp/experiments/`.

## Si algo falla

- **Kaggle 401:** token incorrecto. Vuelve a ejecutar la celda 1; si el secreto no tiene un formato
  reconocido aparece un campo oculto para pegar el token o el JSON legacy.
- **Kaggle 403 / "no está en Kaggle" en todas las tablas:** tu usuario no tiene acceso al dataset;
  Adriel debe agregarlo en el dataset > Settings > Sharing.
- **La publicación falla:** los archivos quedan en `/content/resultados`. Volver a ejecutar la
  celda los publica sin reentrenar (detecta que ya están completos en el servidor).
- **"el índice dice que X existe, pero no se pudo bajar":** la versión es muy reciente; espera unos
  minutos y vuelve a ejecutar.

El [cuaderno original exacto de B4](../docx/03Evidence/05_entrenamiento_B4_independiente_original.ipynb) está preservado como evidencia.