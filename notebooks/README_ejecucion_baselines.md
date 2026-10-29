# Celdas exactas para los cuadernos de baselines

Los números de celda de abajo empiezan en **0** y corresponden a la versión publicada en la rama `04MainAIModelTrainingAndDevelopment`. Cada cuaderno prepara su propio runtime en la **celda 1**; no hace falta ejecutar `00_arranque` ni compartir runtime. Ejecuta las celdas de código en el orden indicado. Las celdas Markdown solo explican el paso.

**Si falla Kaggle en la celda 1:** el secreto `KAGGLE_API_TOKEN` no tiene un formato reconocido. Después de actualizar la rama, vuelve a ejecutar la celda 1: aparecerá un campo oculto donde puedes pegar tu token de Kaggle como texto o un JSON legacy con `username` y `key`. No pegues la credencial en una celda ni en el chat. Como alternativa, corrige el valor del secreto en el panel de secretos de Colab y vuelve a ejecutar la celda 1.

## B0/B1: resultados ya listos

B0/B1 ya está versionado en `results/baseline0_1/20261029T005435Z/`; **no vuelvas a ejecutar el ajuste para continuar con los otros baselines**. La fórmula de B1 sigue pendiente de confirmación, así que sus métricas son preliminares.

Si necesitas repetir toda la corrida, en `02_baselines_B0_B1.ipynb` ejecuta las celdas de código **1 → 3 → 6 → 7 → 9**. No cambies valores. La celda 6 genera un `RUN_ID` nuevo y abre una carpeta nueva en Drive; la celda 7 ajusta B0/B1 para A/B/C; la celda 9 descarga el ZIP. No vuelvas a ejecutar la celda 6 dentro de la misma corrida, porque intenta crear de nuevo la carpeta con ese `RUN_ID`.

## B2: fuga y artefactos finalistas

En `03_baseline_B2.ipynb`:

1. Ejecuta la **celda 1** para preparar ese runtime.
2. Para demostrar la fuga, cambia `EJECUTAR_FUGA = False` a `True` en la **celda 6** y ejecútala. Deja `ESCENARIOS_FUGA = ('A', 'B', 'C')` y `C=0.1` tal como están.
3. Cambia `BUSCAR_MODELOS_B2 = False` a `True` en la **celda 8** y ejecútala. Busca solo los finalistas `C=0.1`.
4. Si falta algún `.joblib`, cambia `GENERAR_B2_FINALISTA_SI_FALTA = False` a `True` en la **celda 10** y ejecútala. Solo ajusta el finalista de los escenarios faltantes, con el tope acordado de 600 épocas. Luego vuelve a ejecutar la **celda 8** para copiar los modelos a `export_repo/baseline2/`.
5. Ejecuta la **celda 12** para descargar el ZIP.

Si solo quieres recuperar los `.joblib`, omite las celdas 5–6 y ejecuta 1, 8 y 12. Activa la celda 10 únicamente si la celda 8 informa que falta un artefacto.

## B3: artefactos finalistas

En `04_baseline_B3.ipynb`:

1. Ejecuta la **celda 1**. La **celda 2** solo muestra los CSV existentes y es opcional.
2. Cambia `BUSCAR_MODELOS_B3 = False` a `True` en la **celda 5** y ejecútala. Busca solamente el bosque de la configuración común finalista en A/B/C.
3. Si falta un `.joblib`, cambia `GENERAR_B3_FINALISTA_SI_FALTA = False` a `True` en la **celda 7** y ejecútala. Solo ajusta los finalistas faltantes. Luego repite la **celda 5** para copiarlos a `export_repo/baseline3/`.
4. Ejecuta la **celda 9** para descargar el ZIP.

Si solo quieres recuperar `.joblib`, ejecuta 1, 5 y 9; activa la celda 7 únicamente si faltan archivos.

## B4: entrenamiento original y experimentos posteriores

En `05_baseline_B4.ipynb`:

1. Ejecuta la **celda 1** para preparar ese runtime. Si aparece el aviso de Kaggle, usa el campo oculto como se explica arriba. La **celda 4** muestra CPU y RAM.
2. Las celdas **5** y **7** contienen, respectivamente, la búsqueda original y el ajuste final de B4. Como B4 ya está entrenado, deja `EJECUTAR_BUSQUEDA_B4 = False` y `EJECUTAR_AJUSTE_FINAL_B4 = False`: la celda 5 consulta la finalista versionada y la celda 7 informa dónde están los modelos. La **celda 9** muestra sus métricas. No se entrena en este paso.
3. Si alguna vez necesitas reproducir B4 desde cero, cambia `EJECUTAR_BUSQUEDA_B4` a `True` en la **celda 5** y ejecuta después la **celda 7** con `EJECUTAR_AJUSTE_FINAL_B4 = True`. Estas operaciones pueden tardar horas y guardan una reproducción nueva en Drive bajo `b4_reproduccion/<RUN_ID>/`, sin sobrescribir los resultados oficiales. Para reproducir solo el ajuste final con la configuración ya seleccionada, deja la celda 5 en `False`, ejecútala y activa la celda 7.
4. **LightGBM, primero entre los experimentos pendientes:** ejecuta la instalación de la **celda 12**. En la **celda 13**, cambia `EJECUTAR_LIGHTGBM = False` a `True` y ejecútala. Deja la semilla 2026 y los escenarios A/B/C. Esa celda realiza la búsqueda, ajusta una finalista por escenario y compara con B4.
5. **Ablaciones:** en la **celda 15** cambia `EJECUTAR_ABLACIONES = False` a `True` cuando vayas a ejecutarlas. Conserva `ESCENARIOS_ABLACIONES = ('A', 'B', 'C')`.
6. **H2:** en la **celda 17** cambia `EJECUTAR_H2 = False` a `True` cuando vayas a ejecutarla. Conserva los escenarios y las cuatro características definidos.
7. La **celda 19** muestra un resumen de LightGBM o ablaciones. La **celda 21** descarga el ZIP de los experimentos guardados bajo el `RUN_ID` actual, incluidas las reproducciones de B4 si las ejecutaste.

Las celdas 5, 7, 13, 15 y 17 están desactivadas por defecto. Si se ejecutan así, imprimen que no entrenaron: un tiempo muy corto indica que se consultaron o saltaron las tareas, no que se completó un entrenamiento. B4 original ya está entrenado; LightGBM, ablaciones y H2 siguen pendientes hasta activar sus celdas y obtener sus salidas. La pregunta H2 sigue definida específicamente para B4.

El [cuaderno original exacto de B4](../docx/03Evidence/05_entrenamiento_B4_independiente_original.ipynb) está preservado como evidencia. En Git ese cuaderno no contenía salidas de celda; los CSV, manifiestos y modelos de la ejecución original están en `results/baseline4/`.

## Archivos descargados

Cada celda de descarga crea un archivo ZIP en Colab y abre la descarga en el navegador. B4 puede generar un ZIP grande porque incluye modelos `.joblib` y el estudio de Optuna. La celda imprime su tamaño.

Los resultados nuevos se guardan primero en Drive, bajo `MyDrive/Applied-AI-Agent-Project/model_checkpoints/`. Si quieres versionarlos, copia la carpeta de la corrida a `results/` conservando el `RUN_ID`, sus CSV y sus archivos `registro`, `config` o `manifest`.
