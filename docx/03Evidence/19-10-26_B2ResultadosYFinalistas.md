# B2: resultados de la primera búsqueda de C y candidatas finalistas

**Fecha:** 19 de octubre de 2026

**Propósito:** dejar checkpoint de la búsqueda inicial de regularización de B2 y explicar qué significa que los ajustes no hayan convergido.

## Qué se hizo

B2 comparó nueve valores de regularización (`C = 0.0001` a `10000`) en los escenarios A, B y C. Usó cinco pliegues de validación cruzada agrupados por partida (`game_id`), con todas las partidas útiles de `train` (`fraccion_train=1.0`). Las métricas reportadas son promedios entre pliegues y su desviación estándar. Se eligieron candidatas por AUC, log loss y Brier; cuando una misma `C` ganaba más de una métrica, se conservó una sola vez.

La tabla de resultados también muestra que ningún pliegue cumplió el criterio de convergencia configurado: `pliegues_convergentes=0` de 5 para todos los valores de `C` y en los tres escenarios. Aun así, los ajustes terminaron y generaron predicciones y métricas; la columna no significa que el proceso se haya caído.

## Resultados que motivan las candidatas

| Escenario | C | AUC (media ± DE) | Log loss (media ± DE) | Brier (media ± DE) | Convergencia |
|---|---:|---:|---:|---:|---:|
| A | 0.0001 | 0.7303 ± 0.0036 | 0.6144 ± 0.0027 | 0.2128 ± 0.0012 | 0/5 |
| A | 0.01 | 0.7556 ± 0.0051 | 0.5814 ± 0.0044 | 0.1992 ± 0.0019 | 0/5 |
| A | 0.1 | 0.7570 ± 0.0051 | 0.5810 ± 0.0048 | 0.1988 ± 0.0020 | 0/5 |
| A | 1 | 0.7571 ± 0.0051 | 0.5812 ± 0.0047 | 0.1988 ± 0.0020 | 0/5 |
| B | 0.0001 | 0.7426 ± 0.0059 | 0.6061 ± 0.0030 | 0.2090 ± 0.0014 | 0/5 |
| B | 0.01 | 0.7773 ± 0.0032 | 0.5605 ± 0.0039 | 0.1905 ± 0.0014 | 0/5 |
| B | 0.1 | 0.7791 ± 0.0031 | 0.5596 ± 0.0040 | 0.1898 ± 0.0014 | 0/5 |
| B | 1 | 0.7793 ± 0.0031 | 0.5596 ± 0.0040 | 0.1898 ± 0.0014 | 0/5 |
| C | 0.0001 | 0.7255 ± 0.0075 | 0.6171 ± 0.0034 | 0.2140 ± 0.0016 | 0/5 |
| C | 0.01 | 0.7564 ± 0.0050 | 0.5804 ± 0.0053 | 0.1989 ± 0.0020 | 0/5 |
| C | 0.1 | 0.7577 ± 0.0050 | 0.5799 ± 0.0055 | 0.1985 ± 0.0021 | 0/5 |
| C | 1 | 0.7578 ± 0.0051 | 0.5799 ± 0.0056 | 0.1985 ± 0.0021 | 0/5 |

This is a compact excerpt of the full grid; the attached Colab output contains all nine values per scenario. From about `C=0.1` onward, the scores largely flatten. For example, the AUC changes from `C=0.1` to `C=1` by only 0.0001 in A, 0.0002 in B, and 0.0001 in C; log loss and Brier are equal or nearly equal at the shown precision. By contrast, the smallest `C` values score noticeably worse in all three scenarios.

## Finalistas que produjo la búsqueda

El procedimiento conservó la mejor `C` observada por cada métrica (AUC más alta; log loss y Brier más bajos), eliminando repetidas:

| Escenario | Candidatas de CV |
|---|---|
| A | `1000`, `0.1` |
| B | `10000`, `0.1` |
| C | `10000`, `0.1`, `1` |

Se mantienen como **finalistas para la siguiente corrida**, no como ganadoras definitivas. `C=0.1` aparece de forma consistente en las selecciones y ya está en la zona donde las métricas se estabilizan. `C=1` es prácticamente indistinguible en las métricas resumidas y también fue seleccionado para C. Los valores altos (`1000`/`10000`) entraron porque la búsqueda los eligió entre resultados empatados o casi empatados; la tabla no demuestra que sean mejores ni que el modelo se beneficie de una regularización tan débil. La nueva corrida con finalistas sirve para comprobar si ampliar el presupuesto de entrenamiento cambia de forma material el ranking y las métricas.

## Qué significa “no convergió”

En esta implementación, `convergencia` se activa cuando la norma máxima del gradiente del objetivo de entrenamiento es menor o igual a `B2_GRADIENT_TOL = 1e-3`. Ningún pliegue llegó a ese umbral dentro del máximo de épocas de la corrida. Por tanto:

- **No podemos afirmar que se haya encontrado el mínimo del objetivo** ni que el ajuste esté suficientemente estabilizado según ese criterio.
- **Tampoco podemos afirmar que no se encontró el mínimo.** El indicador solo dice que el criterio implementado no logró certificarlo antes del límite. El umbral puede ser estricto para este SGD; harían falta los gradientes/objetivos por época y una prueba con más entrenamiento para distinguirlo.
- Las métricas sí describen las predicciones de los modelos que se alcanzaron a entrenar, pero la comparación de `C` es provisional: más entrenamiento podría mover las métricas y el orden entre candidatas.

En particular, `0/5` no quiere decir “el modelo falló” ni “no hay resultados”. Quiere decir “los cinco ajustes terminaron sin cumplir el umbral de gradiente establecido”. No se debe cambiar la tolerancia solo para hacer que el indicador diga convergencia; primero hay que revisar que el criterio sea apropiado y que el entrenamiento se estabilice.

## Próximo paso y conservación del progreso

Se acordó volver a ejecutar B2 usando solo las finalistas de cada escenario y un presupuesto de épocas mayor, para comparar sus métricas con esta búsqueda inicial. Esa verificación aún no está ejecutada. La corrida debe usar una carpeta de salida nueva en Google Drive, separada de la búsqueda anterior, y guardar el checkpoint después de cada pliegue. Así, si Colab se reinicia, se podrán saltar los pliegues ya terminados. La ejecución anterior no se guardó en Drive; el texto de resultados sirve como registro, pero no contiene pesos del modelo para continuar desde una época intermedia.

No se toma `val` ni `test` para volver a escoger épocas dentro de CV. `val` sigue reservado para comparar finalistas después de la validación cruzada; `test` permanece intacto para la evaluación final.

**Fuente de resultados:** salida pegada desde Colab, con `version_sklearn=1.6.1`, lote de 32,768 y cobertura completa de train. El resumen incluye promedios de cinco pliegues. Se conserva como evidencia la salida original en la conversación; no se encontraron CSV persistidos en Drive para esta búsqueda.
