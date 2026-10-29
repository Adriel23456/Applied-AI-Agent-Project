# Protocolo de comparación de LightGBM con B4

Fecha: 28 de octubre de 2026.
Decisión: el usuario delegó al asistente cerrar presupuesto y regla de comparación antes de ejecutar. No se ejecutaron entrenamientos para tomar esta decisión.

## Presupuesto y datos

- LightGBM 4.6.0, semilla 2026, 62 características sin IDs de carta.
- Una búsqueda TPE de 20 configuraciones con 3 pliegues agrupados por `game_id`, sobre las partidas que son `train` simultáneamente en A, B y C. No se mezclan escenarios para evaluar desempeño.
- Objetivo de Optuna: log loss; AUC y Brier registrados. Espacios análogos a B4: tasa 0.02–0.2, hojas 8/16/31, mínimo por hoja 20/50/100 y L2 1e-6–10. Las dos implementaciones tienen diferencias algorítmicas; igual presupuesto de trials no implica igual costo ni capacidad.
- Vigilancia del 15 % por partidas dentro del entrenamiento de cada ajuste; paciencia 30, máximo 2000 iteraciones en búsqueda y 4000 al decidir iteraciones finales.
- Cada partida suma el mismo peso total en ajuste y métricas. En métricas por etapa, se vuelve a ponderar dentro de cada etapa.
- Una sola configuración se selecciona por mayor AUC medio de los pliegues de CV; empates por menor log loss, menor Brier y menor número de trial. Esta selección no consulta `val` de ningún escenario.
- Se usa la configuración seleccionada con el `train` propio de A, B y C. En cada escenario, vigilancia decide iteraciones y luego se reajusta con todo `train`, guardando `.joblib` y métricas globales y por etapa en `val`.
- Presupuesto máximo ordinario: 60 ajustes de búsqueda y 6 finales (vigilancia y reajuste por escenario), comparable con el flujo final de B4. No hay una segunda búsqueda ni repeticiones con otras semillas. Se reutilizan los modelos B4 ya versionados.

## Regla de selección sobre val

Se cambia a LightGBM únicamente si se cumplen **todas** las condiciones en **cada uno** de A, B y C:

1. La diferencia de AUC `LightGBM − B4` tiene un intervalo percentil del 95 % completamente mayor que cero.
2. Los valores observados de log loss y Brier de LightGBM no aumentan frente a B4.

Se calculan 1000 remuestreos emparejados de partidas completas, con reemplazo y semilla 2026; cada repetición sortea tantas partidas como contiene `val`. Ambas predicciones reciben las mismas multiplicidades. Las filas de cada partida conservan su peso 1/n y una partida sorteada varias veces pesa su multiplicidad. Para AUC, el orden de predicciones se calcula una vez y se reutiliza para reducir costo.

Si la regla no se cumple completa, se mantiene B4 y se reportan las diferencias observadas por escenario. No se promedian A, B y C para tomar la decisión. La regla evita exigir un umbral arbitrario de mejora absoluta, pero no demuestra que una diferencia estadística sea importante en la aplicación. Los intervalos son individuales por escenario, no intervalos simultáneos, y no incorporan incertidumbre por la búsqueda o por el ajuste. La ausencia de incremento observado en log loss y Brier no demuestra equivalencia probabilística.

Esta es una decisión de selección con `val`. La evaluación única en `test`, calibración y conclusiones finales siguen en etapa 05.

## Registro

La ejecución guarda en Drive configuración, commit y estado del árbol de trabajo, semilla, versiones, estudio Optuna, CV por trial y pliegue, configuración seleccionada, modelos por escenario, métricas, duración, remuestreos de AUC y `comparacion_b4/decision_val.json`. No hay resultados nuevos hasta ejecutar la celda de LightGBM.
