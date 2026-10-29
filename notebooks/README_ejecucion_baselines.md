# Celdas exactas para los cuadernos de baselines

Los números de celda de abajo empiezan en **0** y corresponden a la versión publicada en la rama `04MainAIModelTrainingAndDevelopment`. Cada cuaderno prepara su propio runtime en la **celda 1**; no hace falta ejecutar `00_arranque` ni compartir runtime. Ejecuta las celdas de código en el orden indicado. Las celdas Markdown solo explican el paso.

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

## B4: LightGBM, ablaciones y H2

En `05_baseline_B4.ipynb`:

1. Ejecuta la **celda 1**. La **celda 3** muestra las métricas B4 que ya están versionadas; puedes ejecutarla para consultarlas.
2. **LightGBM, primero:** ejecuta la instalación de la **celda 6**. En la **celda 7**, cambia `EJECUTAR_LIGHTGBM = False` a `True` y ejecútala. Deja la semilla 2026 y los escenarios A/B/C por defecto. La celda hace la búsqueda, ajusta una finalista por escenario y compara con B4. No cambies tamaños de búsqueda, pliegues, presupuesto ni regla de comparación.
3. **Ablaciones, opcionales:** cuando decidas ejecutarlas, en la **celda 9** cambia `EJECUTAR_ABLACIONES = False` a `True` y ejecútala. Deja `ESCENARIOS_ABLACIONES = ('A', 'B', 'C')`.
4. **H2, opcional:** en la **celda 11** cambia `EJECUTAR_H2 = False` a `True` y ejecútala. No cambies las cuatro características ni la semilla.
5. La **celda 13** muestra un resumen si corriste LightGBM o ablaciones. La **celda 15** descarga el ZIP con lo producido bajo el `RUN_ID` actual.

Las celdas 7, 9 y 11 están apagadas por defecto. Activa solo la sección que vas a correr. LightGBM va antes porque su resultado permite decidir si B4 sigue como modelo principal; H2 conserva su definición actual, que compara específicamente las cuatro entradas con B4.

## Archivos descargados

Cada celda de descarga crea un archivo ZIP en Colab y abre la descarga en el navegador. B4 puede generar un ZIP grande porque incluye modelos `.joblib` y el estudio de Optuna. La celda imprime su tamaño.

Los resultados nuevos se guardan primero en Drive, bajo `MyDrive/Applied-AI-Agent-Project/model_checkpoints/`. Si quieres versionarlos, copia la carpeta de la corrida a `results/` conservando el `RUN_ID`, sus CSV y sus archivos `registro`, `config` o `manifest`.
