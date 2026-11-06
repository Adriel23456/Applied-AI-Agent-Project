# Ejecución de los cuadernos

Qué hace cada cuaderno, en qué orden se ejecuta, cuánto tarda y cómo obtener las cifras del artículo. Para preparar el ambiente (Kaggle, Colab, token y dependencias), ver primero [`GuiaDeAmbiente.md`](../GuiaDeAmbiente.md).

---

## 1. Cómo funciona cada cuaderno

1. **La primera celda prepara todo.** Clona o actualiza el repositorio en `/content/repo`, instala `requirements.txt`, muestra los núcleos y la RAM, pide el token de Kaggle sin mostrarlo y baja a `/content/datos` las tablas que falten. Cada cuaderno puede abrirse solo, sin ejecutar antes otro.
2. **Cada celda que calcula algo declara los archivos que produce** y llama a `store.asegurar(archivos, calcular, mensaje)`:
   - si **todos** están en Kaggle, los baja a `/content/resultados/<ruta>`, comprueba su SHA-256 y no recalcula;
   - si falta alguno, calcula, comprueba que se crearon y publica una versión nueva del dataset, sin borrar lo publicado antes.
3. **No hay interruptores** (`EJECUTAR = False`, `CREAR`, `CONSTRUIR`): ejecutar una celda hace lo que haga falta.
4. **Rama clonada.** La variable `BRANCH` de la primera celda indica qué rama se clona: `04MainAIModelTrainingAndDevelopment` en los cuadernos 00 a 05 y `05FinalModelChecks` en el 06. Esas ramas se conservan. Para ejecutar la versión entregada, cambia `BRANCH` a `Stage2` o a `master`.

Todos los resultados (CSV, JSON, figuras y modelos `.joblib`) viven en el dataset privado `adrielchavessalazar/ptcg-wp-tablas`, nunca en Git. En Kaggle los nombres van aplanados (`results__b4__final__...`), y el índice `results__indice.csv` guarda el SHA-256, el commit y la fecha de cada archivo. El significado de cada carpeta está en `results__README.md` del dataset.

---

## 2. Cuadernos, en orden

| Cuaderno | Qué hace | Celdas que producen algo | Carpeta en Kaggle | Si ya está en Kaggle | Si falta |
|---|---|---|---|---|---|
| `00_arranque` | Pruebas, tablas Parquet de los 10 días, verificación, particiones y publicación de tablas | Pruebas → tablas → verificación → particiones → publicación | Tablas en la raíz del dataset | 1–2 min | ~12 min por día |
| `01_exploracion` | Auditoría de la tabla (rangos, valores imposibles, AUC univariada, prevalencia, días), cortes de etapa y cobertura de cartas | Partes B y C (la parte A, con JSON crudo, es opcional) | Solo muestra resultados | minutos | minutos |
| `02_baselines_B0_B1` | B0 (prevalencia) y B1 (heurística de recursos) | `B0 Y B1: AJUSTE EN TRAIN...` | `b0_b1/` | segundos | ~2 min |
| `03_baseline_B2` | Selección de C (solo lectura), demostración de fuga y B2 final | `DEMOSTRACION DE FUGA`, `B2 FINAL` | `b2/` | segundos | demo ~1 min por escenario; B2 varias horas por escenario |
| `04_baseline_B3` | Búsqueda (solo lectura) y B3 final | `B3 FINAL` | `b3/` | segundos | horas por escenario |
| `05_baseline_B4` | Búsqueda de B4, ajuste final, LightGBM, ablaciones, H2, resumen y modelo final | Parte 1 → Parte 2 → LightGBM → ablaciones → H2 → resumen → exportar → verificar | `b4/`, `lightgbm/`, `modelo_final/` | segundos | búsqueda ~2 h 20 min; ajuste final ~50 min por escenario; experimentos, horas |
| `06_evaluacion_final` | Verificación en `val`, SHAP, calibración, curvas, `test`, hipótesis, errores y veredicto | Todas, de arriba abajo | `evaluacion_final/` | minutos | ~5–7 h |

En `05`, la Parte 2 usa la configuración elegida en la Parte 1 (ensayo 20). El código de LightGBM, ablaciones y H2 está en `src/ptcg_wp/experiments/`. El [cuaderno original de B4](../docx/03Evidencia/05_entrenamiento_B4_independiente_original.ipynb) se conserva como evidencia.

### Cuaderno 06 por partes

| Parte | Celda | Produce |
|---|---|---|
| 0 | `BARRERAS Y PIEZAS COMUNES` | Comprueba que el protocolo está en el repo y que no hay cambios locales |
| 1 | `VERIFICAR LA CARGA DE MODELOS...` | Reproduce las métricas de `val` publicadas por las ramas anteriores |
| 2 | `SHAP DEL MODELO FINAL...` y `FIGURA SHAP` | `shap/` y la revisión de fuga (barrera para abrir `test`) |
| 3 | `AJUSTE Y DECISION DE CALIBRACION` | Método de calibración elegido solo con `calib` |
| 4 | `CURVAS DE APRENDIZAJE...` | `curvas/` |
| 5 | `EVALUACION UNICA EN TEST` y `COMPARACION CONTRA B0, B1, B2...` | `test/`: métricas, intervalos, comparaciones y AUC por turno |
| 6 | `CALIBRACION EN TEST` | `calibracion/` |
| 7 | `H1 Y H2` y `H3` | `hipotesis/` |
| 8 | `ANALISIS DE ERRORES` | `errores/` |
| 9 | `VEREDICTO SOBRE H1, H2 Y H3` | `veredicto.json` |

---

## 3. Cómo obtener las cifras del artículo

Ejecuta `06_evaluacion_final` de arriba abajo. Con acceso al dataset del equipo, todo se baja y nada se recalcula: las salidas son las mismas del cuaderno versionado, que se guarda con sus salidas.

| Resultado del artículo | Celda del cuaderno 06 | Archivo en `evaluacion_final/` |
|---|---|---|
| Tabla de AUC en prueba y pérdidas de B4 | `EVALUACION UNICA EN TEST` | `test/metricas_{A,B,C}.csv` |
| Diferencias contra B0–B3 y criterio de B1 | `COMPARACION CONTRA...` | `test/comparaciones_{A,B,C}.csv`, `test/referencias.json` |
| Figura de AUC por turno | `COMPARACION CONTRA...` | `test/auc_por_turno_A.csv` |
| Tabla de H1 por etapa y cohorte | `H1 Y H2` | `hipotesis/` |
| Tabla de H2 | `H1 Y H2` | `hipotesis/` |
| Figura y tabla de calibración | `CALIBRACION EN TEST` | `calibracion/` |
| Tabla de H3 | `H3` | `hipotesis/h3.csv`, `h3_decision.json`, `h3_serie_diaria.csv` |
| Curvas de aprendizaje | `CURVAS DE APRENDIZAJE` | `curvas/` |
| Análisis de errores | `ANALISIS DE ERRORES` | `errores/` |
| Figura SHAP y revisión de fuga | `SHAP DEL MODELO FINAL` | `shap/` |
| Veredicto de H1 a H3 | `VEREDICTO` | `veredicto.json` |

Las métricas de `val` (B0 a B4, LightGBM, ablaciones y H2) salen del cuaderno `05_baseline_B4` (celda `RESUMEN`) y de las carpetas `b0_b1/`, `b2/`, `b3/`, `b4/` y `lightgbm/`. Los datos del corpus (55 196 partidas, cobertura de cartas, prevalencia) salen de `00_arranque` y `01_exploracion`. La interpretación completa de los resultados está en [`docx/03Evidencia/04-11-26_ResultadosEvaluacionFinal.md`](../docx/03Evidencia/04-11-26_ResultadosEvaluacionFinal.md).

**Recalcular desde cero.** Usa un dataset de Kaggle propio y vacío (en `configs/datos.yaml`) y ejecuta los cuadernos 00 a 06 en orden. Con la semilla fija (`SEED = 2026`) y las versiones de `requirements.txt`, las particiones son idénticas y los modelos deben dar las mismas cifras dentro de la precisión numérica. El tiempo total es de varios días de cómputo, sobre todo por B2, B3 y la búsqueda de B4.

---

## 4. Reglas del cuaderno 06

`06_evaluacion_final` abre `test`, que se usa una sola vez. Sigue el protocolo [`docx/03Evidencia/02-11-26_ProtocoloEvaluacionFinal.md`](../docx/03Evidencia/02-11-26_ProtocoloEvaluacionFinal.md), escrito antes de abrirlo.

- Una sola persona lo ejecuta.
- El servidor no debe tener cambios locales y nadie más debe estar publicando en Kaggle.
- La celda de `test` no corre si la revisión de fuga no aprobó o si faltan la calibración o las curvas.
- Si una sesión se corta, vuelve a ejecutar desde arriba: lo publicado se baja y no se recalcula.

---

## 5. Trabajo en paralelo

Si dos personas publican al mismo tiempo, la versión que termina después puede no incluir lo que subió la otra. Avisen en el grupo antes de ejecutar celdas que calculan algo nuevo. Cada publicación tarda unos minutos, y Kaggle tarda otros minutos en mostrar la versión nueva a otros servidores.

---

## 6. Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| Kaggle 401 | Token incorrecto | Volver a ejecutar la primera celda; si el secreto no se reconoce, aparece un campo oculto para pegarlo |
| Kaggle 403 o "no está en Kaggle" en todas las tablas | Tu usuario no tiene acceso al dataset | Adriel lo agrega en el dataset > Settings > Sharing |
| La publicación falla | Error de red o de Kaggle | Los archivos quedan en `/content/resultados`; volver a ejecutar la celda los publica sin recalcular |
| "El índice dice que X existe, pero no se pudo bajar" | Versión muy reciente | Esperar unos minutos y volver a ejecutar |
| `ModuleNotFoundError: ptcg_wp` | `src/` no está en el path | Ejecutar la primera celda |
| El repo en Colab no tiene mis cambios | Falta el push | `git push` desde la PC y volver a ejecutar la primera celda |
| Aviso de versión de scikit-learn distinta | El servidor traía otra versión | Reiniciar el runtime y volver a ejecutar la primera celda |
| Se perdió todo | El servidor se reinició | Normal: volver a ejecutar desde arriba |