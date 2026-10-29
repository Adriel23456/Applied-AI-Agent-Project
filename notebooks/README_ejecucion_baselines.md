# Ejecución de pendientes de baselines

Los cuadernos se ejecutan en Colab con CPU y RAM alta. Los experimentos guardan sus salidas en Google Drive; `RUN_ID` identifica cada sesión en UTC. B1 y el protocolo de LightGBM están marcados como propuestas. Las métricas de `val` se reportan por escenario y no se usa `calib` ni `test`.

## Preparación

1. En el repositorio local, revisa y publica en la rama los cambios de los cuadernos, `src/ptcg_wp/pending_experiments.py` y la documentación que se quiera conservar. No se han hecho commit ni push automáticamente. Colab debe obtener un commit que incluya el módulo nuevo.
2. Abre `00_arranque.ipynb` en Colab, en la rama `04MainAIModelTrainingAndDevelopment`, y ejecuta las celdas de preparación y descarga de datos. Abre los cuadernos siguientes en el **mismo runtime**. Verifica que el commit impreso sea el esperado y que no haya cambios locales en Colab.
3. Cada celda de experimento largo tiene un interruptor `False`. Cámbialo a `True` únicamente cuando vayas a ejecutar esa sección. Mantén las demás secciones en `False`.
4. La raíz de las salidas es `MyDrive/Applied-AI-Agent-Project/model_checkpoints/`. Conserva el identificador de corrida impreso. La ejecución de LightGBM es costosa; su protocolo y el criterio de mejora clara siguen pendientes de acuerdo.

## Orden sugerido

1. **B0/B1** (`02_baselines_B0_B1.ipynb`): ejecutar preparación y celdas de métricas, registro y ejecución. Las salidas quedan en `b0_b1/<RUN_ID>/`. B1 se guarda como propuesta y requiere confirmación antes de usarla como evidencia final.
2. **B2** (`03_baseline_B2.ipynb`): ejecutar preparación, cambiar `EJECUTAR_FUGA` a `True` y ejecutar la celda de la demostración. Guarda métricas y solapamiento en `b2/demo_fuga/<RUN_ID>/escenario_X/`. Ejecutar después la celda de recuperación con `BUSCAR_MODELOS_B2=True`; los modelos válidos se copian a `export_repo/baseline2/`. Si hay cero o varias coincidencias, revisar la ruta manualmente.
3. **B3** (`04_baseline_B3.ipynb`): montar Drive y ejecutar la celda de recuperación con `BUSCAR_MODELOS_B3=True`. Los modelos verificados se copian a `export_repo/baseline3/`. Si hay cero o varias coincidencias, revisar la ruta manualmente.
4. **B4: ablaciones** (`05_baseline_B4.ipynb`): ejecutar preparación y activar `EJECUTAR_ABLACIONES`. Se realizan tres variantes por escenario, cada una con vigilancia y ajuste final. Salen a `b4/ablaciones/<RUN_ID>/escenario_X/`. `familias.json` define las columnas eliminadas.
5. **H2** (mismo cuaderno): activar `EJECUTAR_H2`. Guarda las métricas y el modelo de la variante restringida, y muestra la comparación con B4 en `b4/h2/<RUN_ID>/escenario_X/`. Si la cardinalidad de un ID supera 255, la implementación se detiene y requiere otra codificación.
6. **LightGBM** (mismo cuaderno): revisar primero el protocolo propuesto con el equipo. Para ejecutarlo, instalar LightGBM 4.6.0 en la celda indicada y activar `EJECUTAR_LIGHTGBM`. La búsqueda y sus finalistas salen a `lightgbm/<RUN_ID>/`. No declarar una mejora clara sin acordar el criterio. Si el runtime se interrumpe, asignar el `RUN_ID` anterior después de ejecutar la preparación y actualizar `RUN_INFO["run_id_utc"]` antes de reutilizar esa carpeta para continuar el estudio; los ajustes finales pueden repetirse.

Se pueden ejecutar los escenarios o secciones por separado cambiando las tuplas `ESCENARIOS_*`. El resumen del cuaderno B4 muestra las salidas que coinciden con el `RUN_ID` actual; para otra sesión, asigna el identificador anterior antes de ejecutar el resumen.

## Qué copiar desde Drive al repositorio

| Origen bajo `model_checkpoints/` | Destino sugerido en el repositorio | Contenido |
|---|---|---|
| `b0_b1/<RUN_ID>/` | `results/baseline0_1/<RUN_ID>/` | `metricas_B0_B1.csv`, `ajustes_B0_B1.csv`, `registro.json` |
| `b2/demo_fuga/<RUN_ID>/` | `results/baseline2/demo_fuga/<RUN_ID>/` | `metricas.csv`, `solapamiento.csv`, `config.json`, `registro.json`, por escenario |
| `export_repo/baseline2/` | `results/baseline2/modelos/` | Modelos B2 `C=0.1` encontrados y verificados |
| `export_repo/baseline3/` | `results/baseline3/modelos/` | Modelos B3 encontrados y verificados |
| `b4/ablaciones/<RUN_ID>/` | `results/baseline4/ablaciones/<RUN_ID>/` | Familias, métricas, manifiestos, tiempos y modelos de cada variante |
| `b4/h2/<RUN_ID>/` | `results/baseline4/h2/<RUN_ID>/` | Métricas, configuración, registro y modelo restringido, por escenario |
| `lightgbm/<RUN_ID>/` | `results/lightgbm/<RUN_ID>/` | Estudio SQLite, CV por trial y pliegue, candidatas, configuración, tiempos y resultados de `val`; conservar los modelos necesarios para la decisión final |

Copia únicamente carpetas de corridas completadas; si se detuvo una corrida, conserva el estado parcial claramente identificado. Antes de agregar archivos `.joblib` comprueba su tamaño y las reglas del repositorio o de Git LFS. Los resultados copiados deben mantener el manifiesto de la misma corrida. Los resultados de B1 siguen siendo provisionales hasta confirmar la fórmula.
