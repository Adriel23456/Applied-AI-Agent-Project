# Ejecución de pendientes de baselines

Los cuadernos se ejecutan en Colab con CPU y RAM alta. Los experimentos guardan sus salidas en Google Drive; `RUN_ID` identifica cada sesión en UTC. La fórmula de B1 sigue marcada como propuesta. El protocolo de LightGBM quedó definido el 28 de octubre en `docx/03Evidence/28-10-26_ProtocoloLightGBM.md`. Las métricas de `val` se reportan por escenario y no se usa `calib` ni `test`.

## Preparación

1. Asegúrate de que la rama `04MainAIModelTrainingAndDevelopment` contiene los cambios actuales y abre en Colab el cuaderno del baseline que vas a ejecutar.
2. Cada cuaderno de baseline prepara **su propio runtime** en la primera celda: conecta Drive, actualiza o clona la rama, instala dependencias y baja las tablas procesadas a `/content/datos` si faltan. No requiere ejecutar `00_arranque` ni comparte el runtime con otro cuaderno. Si Colab inicia un runtime nuevo, vuelve a ejecutar la primera celda de ese cuaderno.
3. Verifica el commit impreso y que no haya cambios locales. Cada celda de experimento largo tiene un interruptor `False`; actívalo solo para esa sección.
4. La raíz de las salidas es `MyDrive/Applied-AI-Agent-Project/model_checkpoints/`. Conserva el `RUN_ID` impreso. LightGBM tiene el mismo presupuesto de búsqueda que B4: 20 trials y 3 pliegues, más 6 ajustes para su única configuración finalista. El tiempo real puede variar entre implementaciones.

## Orden sugerido

1. **B0/B1** (`02_baselines_B0_B1.ipynb`): ejecutar primero la celda de preparación propia y luego las celdas de métricas, registro y ejecución. Las salidas quedan en `b0_b1/<RUN_ID>/`. B1 se guarda como propuesta y requiere confirmación antes de usarla como evidencia final.
2. **B2** (`03_baseline_B2.ipynb`): ejecutar su celda de preparación, cambiar `EJECUTAR_FUGA` a `True` y ejecutar la celda de la demostración. Guarda métricas y solapamiento en `b2/demo_fuga/<RUN_ID>/escenario_X/`. La demostración usa solo `C=0.1`, la configuración finalista; reajusta para cada partición porque cambia el conjunto de entrenamiento. Es un diagnóstico LBFGS con muestra pequeña, no reutiliza el `.joblib` final SGD. Ejecutar después la celda de recuperación con `BUSCAR_MODELOS_B2=True`; copia solo los finalistas `C=0.1` de A, B y C a `export_repo/baseline2/`. Si no hay artefactos, activa `GENERAR_B2_FINALISTA_SI_FALTA`; reajusta solo `C=0.1` en los escenarios faltantes y guarda los `.joblib` en Drive. Mantiene el tope acordado de 600 épocas y registra que no convergió el gradiente. Luego vuelve a ejecutar la celda de recuperación para copiarlos a `export_repo/baseline2/`.
3. **B3** (`04_baseline_B3.ipynb`): ejecutar su celda de preparación y la celda de recuperación con `BUSCAR_MODELOS_B3=True`. Se copia solo el modelo de la configuración común finalista de cada escenario (tres ajustes, uno por cada `train` propio) a `export_repo/baseline3/`. No se usan las otras candidatas de búsqueda. Si falta alguno, activa `GENERAR_B3_FINALISTA_SI_FALTA`; ajusta únicamente el bosque seleccionado y solo para los escenarios sin artefacto. Luego vuelve a ejecutar la celda de recuperación para copiarlos a `export_repo/baseline3/`. Si hay varias coincidencias, revisa la ruta antes de copiar.
4. **B4: ablaciones** (`05_baseline_B4.ipynb`): ejecutar su celda de preparación y activar `EJECUTAR_ABLACIONES`. Se realizan tres variantes por escenario, cada una con vigilancia y ajuste final. Salen a `b4/ablaciones/<RUN_ID>/escenario_X/`. `familias.json` define las columnas eliminadas.
5. **H2** (mismo cuaderno): activar `EJECUTAR_H2`. Guarda las métricas y el modelo de la variante restringida, y muestra la comparación con B4 en `b4/h2/<RUN_ID>/escenario_X/`. Si la cardinalidad de un ID supera 255, la implementación se detiene y requiere otra codificación.
6. **LightGBM** (mismo cuaderno): ejecutar la instalación de LightGBM 4.6.0, activar `EJECUTAR_LIGHTGBM` y ejecutar la celda. Completa búsqueda, selección de una finalista por AUC de CV, ajustes en A/B/C y comparación con B4 mediante 1000 remuestreos emparejados de partidas. Guarda `comparacion_b4/decision_val.json` y los resultados separados por escenario. LightGBM reemplaza a B4 solo si el intervalo del 95 % para la diferencia de AUC queda por encima de cero en A, B y C y no suben los valores observados de log loss ni Brier en ninguno. Ante resultados mixtos o inciertos, se mantiene B4. Si el runtime se interrumpe, asigna el `RUN_ID` anterior después de la preparación y actualiza `RUN_INFO["run_id_utc"]` antes de continuar; los escenarios con modelo y métricas completos omiten el ajuste final.

Se pueden ejecutar los escenarios o secciones por separado cambiando las tuplas `ESCENARIOS_*`. El resumen del cuaderno B4 muestra las salidas que coinciden con el `RUN_ID` actual; para otra sesión, asigna el identificador anterior antes de ejecutar el resumen.

## Qué copiar desde Drive al repositorio

| Origen bajo `model_checkpoints/` | Destino sugerido en el repositorio | Contenido |
|---|---|---|
| `b0_b1/<RUN_ID>/` | `results/baseline0_1/<RUN_ID>/` | `metricas_B0_B1.csv`, `ajustes_B0_B1.csv`, `registro.json` |
| `b2/demo_fuga/<RUN_ID>/` | `results/baseline2/demo_fuga/<RUN_ID>/` | `metricas.csv`, `solapamiento.csv`, `config.json`, `registro.json`, por escenario |
| `export_repo/baseline2/` y, si se generó, `b2/finalista_seleccionada_refit/<RUN_ID>/` | `results/baseline2/modelos/` | Modelos B2 `C=0.1` encontrados o reajustados y verificados |
| `export_repo/baseline3/` y, si se generó, `b3/finalista_seleccionada_refit/<RUN_ID>/` | `results/baseline3/modelos/` | Modelos B3 finalistas encontrados o reajustados y verificados |
| `b4/ablaciones/<RUN_ID>/` | `results/baseline4/ablaciones/<RUN_ID>/` | Familias, métricas, manifiestos, tiempos y modelos de cada variante |
| `b4/h2/<RUN_ID>/` | `results/baseline4/h2/<RUN_ID>/` | Métricas, configuración, registro y modelo restringido, por escenario |
| `lightgbm/<RUN_ID>/` | `results/lightgbm/<RUN_ID>/` | Estudio SQLite, CV por trial y pliegue, `lightgbm_finalista.csv`, configuración, tiempos, modelos y resultados de `val`; incluir `comparacion_b4/` con métricas, remuestreos y decisión |

Copia únicamente carpetas de corridas completadas; si se detuvo una corrida, conserva el estado parcial claramente identificado. Antes de agregar archivos `.joblib` comprueba su tamaño y las reglas del repositorio o de Git LFS. Los resultados copiados deben mantener el manifiesto de la misma corrida. Los resultados de B1 siguen siendo provisionales hasta confirmar la fórmula.
