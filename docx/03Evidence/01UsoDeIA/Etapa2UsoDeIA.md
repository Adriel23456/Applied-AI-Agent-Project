# Declaración de Uso de Herramientas de IA

**Proyecto:** Estimación de la Probabilidad de Victoria a partir del Estado de Juego en el Pokémon Trading Card Game: un Estudio de Clasificación Tabular con Control Explícito de Fuga de Información

**Curso:** IC-6200 — Inteligencia Artificial, ITCR · II Semestre 2026 · Track A

**Equipo:** Adriel S. Chaves Salazar · Daniel Duarte Cordero · Sebastián Hernández Bonilla

**Cubre:** Etapa 2 — Modelado y evaluación (ramas `03DataCollectionAndEnvironmentSetup`, `04MainAIModelTrainingAndDevelopment` y `05FinalModelChecks`)

**Estado:** completa. Cada integrante revisa su bloque de la sección 4 antes de la entrega.

Esta sección se suma a `Etapa1UsoDeIA.md`, no la sustituye.

---

## 1. Herramientas utilizadas

| Herramienta | Quién | Propósito en esta etapa |
| --- | --- | --- |
| **Claude (Anthropic), modelo Opus 5.5, en la aplicación de Claude con ejecución de código** | Adriel | Ramas 03, 04 y 05: diseño e implementación de la ingesta, las características, las particiones, el almacén en Kaggle y el entorno de Colab; diagnóstico de los errores que aparecieron al ejecutar; revisión de la lógica del entrenamiento de B4; reorganización del código y de los cuadernos; codificación de H2, evaluación común y exportación del modelo final. |
| **Claude (Anthropic)** | Daniel | Rama 04: implementación de B0 a B4 con lectura por lotes y puntos de control reanudables, búsquedas de hiperparámetros, auditorías de los baselines y protocolo de comparación con LightGBM. |
| **Claude (Claude Code, Opus 5.5)** | Sebastián | Rama 05: diagnóstico del proyecto, protocolo de evaluación final, implementación de las comprobaciones del cuaderno 06 y documentación de resultados. |

Ninguna herramienta tuvo acceso al dataset privado de Kaggle ni ejecutó los cuadernos con los datos del proyecto. Todas las cifras de esta etapa provienen de celdas ejecutadas por el equipo en Google Colab y quedan trazadas en el dataset del equipo (`adrielchavessalazar/ptcg-wp-tablas`), con SHA-256 y commit por archivo.

---

## 2. Dónde se usó la IA y qué se hizo manualmente después

### 2.1 Rama `03DataCollectionAndEnvironmentSetup` (Adriel, con Claude)

**Qué hizo la herramienta.** Propuso e implementó, a partir de las indicaciones de Adriel, el código de preparación de datos y del entorno:

- `src/ptcg_wp/ingest.py`: descarga de cada día del dataset de la competencia, conversión del JSON a tablas Parquet por día y borrado del crudo.
- `src/ptcg_wp/features.py`: una fila por estado desde la perspectiva del jugador que actúa, solo con información pública; valores centinela con indicador en lugar de imputación; marcas de preparación y de estados ya resueltos; ids de carta fuera del modelo principal.
- `src/ptcg_wp/splits.py`: particiones agrupadas por partida para los escenarios A, B y C, con la auditoría y corrección de cobertura de cartas.
- `src/ptcg_wp/colab.py` y la primera versión de `src/ptcg_wp/store.py`: lectura del token de Kaggle sin escribirlo en el cuaderno, publicación de las tablas en un dataset privado y descarga archivo por archivo.
- Las pruebas de los invariantes de fuga, de particiones y de carga, y los cuadernos `00_arranque` y `01_exploracion` con comentarios por celda.

También diagnosticó, a partir de las salidas que Adriel copiaba desde Colab, los problemas que aparecieron al ejecutar:

- la herramienta `kaggle` informaba éxito al fallar la publicación;
- la descarga del dataset completo respondía 404 a los compañeros, por lo que se pasó a descarga por archivo;
- la extensión `autoreload` no funciona en el Python 3.13 de Colab, por lo que se olvidan a mano los módulos del proyecto tras cada `git pull`;
- módulos viejos en memoria causaban un `TypeError` en `feature_columns`;
- la auditoría B7 contaba filas de preparación como primera fila útil.

**Verificado manualmente.** Adriel ejecutó cada celda en Colab, comparó los conteos con lo esperado (55 196 partidas, 7 540 389 estados, 7 286 386 filas útiles, 119 empates sin estados) y revisó las auditorías del cuaderno `01_exploracion` antes de aceptar cada cambio. Las definiciones de los escenarios y los días se acordaron con el equipo.

**No generado por IA.** La ejecución de la ingesta de los diez días y de las auditorías, cada número que produjeron, la decisión de qué días usar, la creación y administración del dataset privado y sus permisos, el manejo de credenciales y la aprobación de cada commit.

### 2.2 Rama `04MainAIModelTrainingAndDevelopment`

**Entrenamiento de los baselines (Daniel, con Claude).** La herramienta implementó, a partir de las indicaciones de Daniel, B0 y B1, la regresión logística B2 con ajuste por lotes para respetar la RAM de Colab, las búsquedas de B3 y B4 con Optuna y puntos de control reanudables, la evaluación común de B0 a B3 y las auditorías de finalistas. Como registran `12-10-26_AcuerdosTecnicosModelado.md` y `28-10-26_ProtocoloLightGBM.md`, dos decisiones técnicas se delegaron al asistente y se documentaron: la adopción de la fórmula de B1 y el presupuesto y la regla de comparación de LightGBM, ambas fijadas antes de ejecutar. Daniel ejecutó los entrenamientos en Colab durante varios días (B2 y B3 se reanudaron a lo largo de varias sesiones), recuperó los artefactos y verificó con los metadatos de cada modelo que usaran todo el `train` de su escenario.

**Infraestructura, revisión y experimentos (Adriel, con Claude).** La herramienta, a partir de lo que Adriel reportaba desde Colab:

- revisó la lógica de la búsqueda de B4 y propuso corregirla: un solo estudio en lugar de tres, búsqueda solo con partidas que son `train` en A, B y C, servidor con RAM alta y tope final de 4000 árboles, después de detectar que el tope anterior se alcanzaba;
- reemplazó Google Drive por el dataset privado de Kaggle como almacén de resultados (`store.py`: índice con SHA-256, publicación que conserva todo lo anterior y espera a que Kaggle procese cada versión) y reorganizó la carpeta de resultados con un README por carpeta;
- reescribió los cuadernos 02 a 05 sin interruptores: cada celda revisa sus propios archivos en Kaggle y solo entrena lo que falta;
- propuso la codificación por bloques sin pérdida que permite a H2 usar las 359 cartas activas, ante el límite de 255 categorías por columna de HistGradientBoosting;
- corrigió el aviso de nombres de columnas de LightGBM, reorganizó el paquete (`data.py`, `b0_b1.py`, `experiments/`), unificó la evaluación de todos los modelos en una sola función e implementó `predictor.py` y la exportación del modelo final.

Adriel ejecutó LightGBM, las ablaciones, H2 y la exportación, y comprobó que el modelo exportado reproduce las métricas de `val` de B4 en A (diferencia máxima 5.6e-16).

**Verificado manualmente.** Cada cambio se probó en Colab antes del commit: pruebas automáticas, reproducción de métricas ya publicadas y comparación de cada salida con el valor esperado anotado en la celda. Daniel revisó el avance de los entrenamientos y Adriel las ejecuciones de los experimentos.

**No generado por IA.** La ejecución de todos los entrenamientos y experimentos y sus métricas; las decisiones de usar Kaggle en lugar de Drive, de eliminar los interruptores de los cuadernos y de exigir las 359 categorías completas en H2; la interpretación de los resultados de LightGBM, ablaciones y H2; y la aprobación de los commits y del PR de la rama.

### 2.3 Rama `05FinalModelChecks` (Sebastián con Claude Code; ejecución de Adriel)

**Qué hizo la herramienta.** Reconstruyó el estado del proyecto a partir del repositorio y el artículo (`02-11-26_DiagnosticoFinalModelChecks.md`). Propuso el protocolo (`02-11-26_ProtocoloEvaluacionFinal.md`), con tres decisiones de método: mover SHAP y la revisión de fuga antes de `test`, decidir H3 con la descomposición de calibración y discriminación, y controlar la duración en H1 con una cohorte de partidas. Implementó `src/ptcg_wp/evaluacion_final.py`, `tests/test_evaluacion_final.py` y las celdas de `notebooks/06_evaluacion_final.ipynb`, y comprobó el cuaderno con un corpus inventado. Redactó el borrador de la sección de reproducción del `README.md`.

Después de la ejecución, auditó las salidas guardadas del cuaderno y redactó `04-11-26_ResultadosEvaluacionFinal.md` y la celda de interpretación. Todas las cifras se copiaron de esas salidas; la herramienta no calculó ninguna.

Durante la ejecución, la publicación del análisis de errores se marcó como fallida aunque había funcionado: los archivos `errores_*.csv` contienen la palabra "error". Adriel lo diagnosticó con Claude, que corrigió la detección en `store.py` y agregó sus pruebas.

**Qué no hizo la herramienta.** No tuvo acceso al dataset de Kaggle y no ejecutó el cuaderno con los datos del proyecto. Ninguna métrica de `calib` o `test` proviene de ella.

**Verificado manualmente.** El equipo decidió dónde ejecutar (Colab Pro) y revisó qué se subía antes de cada commit. Adriel ejecutó el cuaderno 06 y comprobó que pasara sus barreras: 109 pruebas, reproducción de las métricas de `val` y revisión de fuga, todo antes de abrir `test`.

**No generado por IA.** La ejecución del cuaderno y sus resultados, la decisión de dónde y quién ejecutaba, y la aprobación de los commits.

---

## 3. Límites establecidos por el equipo

Se mantienen los límites de la Etapa 1. En esta etapa se suman:

* **Ningún resultado se genera con IA.** Cada cifra proviene de una celda ejecutada por el equipo y queda trazada en el dataset del equipo, con SHA-256 y commit por archivo.
* **La IA no accede a los datos ni a las credenciales.** El token de Kaggle no se escribe en cuadernos, archivos versionados ni conversaciones.
* **El protocolo se fija antes de abrir `test`.** Las reglas de decisión no cambian al ver los resultados, y `test` se usa una sola vez: ninguna selección de modelo o calibrador depende de sus números.
* **Las decisiones técnicas delegadas se documentan.** Cuando el equipo delegó una decisión al asistente (fórmula de B1, protocolo de LightGBM), quedó registrada en `docx/03Evidence/` antes de ejecutar.
* **Los resultados con datos sintéticos no son resultados del proyecto.** Solo prueban que el código corre.

---

## 4. Declaración por integrante

Cada miembro revisa su propio bloque antes de la entrega.

### Adriel S. Chaves Salazar

* **Herramientas utilizadas:** Claude (Anthropic), modelo Opus 5.5, en la aplicación de Claude con ejecución de código.
* **Dónde y para qué:** Rama 03 completa (preparación de datos y entorno) y la infraestructura, la revisión y los experimentos de la rama 04, según las secciones 2.1 y 2.2; en la rama 05, la ejecución del cuaderno 06 y la corrección de `store.py` (sección 2.3). Usé la herramienta como asistente de programación y de diagnóstico: le describía el objetivo y las reglas del equipo, ejecutaba sus propuestas en Colab y le devolvía las salidas y los errores para corregirlos.
* **Verificado manualmente después:** Ejecuté cada celda en Colab y comparé sus salidas con los valores esperados: conteos del corpus, auditorías, pruebas automáticas y reproducción de métricas ya publicadas. Revisé cada cambio antes del commit y rechacé o corregí las propuestas que no cumplían lo pedido, por ejemplo interruptores en las celdas, dependencia de Google Drive o la pérdida de categorías en H2.
* **No generado por IA:** La ejecución de la ingesta, de las auditorías, de LightGBM, de las ablaciones, de H2 y del cuaderno 06, y cada número que produjeron; la administración del dataset privado y de las credenciales; las decisiones de diseño del flujo de trabajo (Kaggle como almacén único, celdas sin interruptores, codificación completa de H2); y la aprobación de los commits y PR.

### Daniel Duarte Cordero

* **Herramientas utilizadas:** Claude (Anthropic).
* **Dónde y para qué:** Rama 04, entrenamiento de los baselines (sección 2.2): implementación de B0 a B4, del ajuste por lotes de B2, de las búsquedas reanudables de B3 y B4, de la evaluación común de B0 a B3, de las auditorías de finalistas y del protocolo de LightGBM. Delegué al asistente dos decisiones técnicas que quedaron documentadas antes de ejecutar: la fórmula de B1 y el protocolo de comparación con LightGBM.
* **Verificado manualmente después:** Ejecuté los entrenamientos en Colab, supervisé sus reanudaciones durante varios días, recuperé los artefactos y comprobé con sus metadatos que cada ajuste usara todo el `train` de su escenario y la configuración seleccionada.
* **No generado por IA:** La ejecución de los entrenamientos de B0 a B4 y sus métricas, la supervisión de las corridas y la aprobación de los commits de la rama.

### Sebastián Hernández Bonilla

* **Herramientas utilizadas:** Claude (Claude Code, Opus 5.5).
* **Dónde y para qué:** En la rama `05FinalModelChecks` lo usé como asistente de programación y redacción, según la sección 2.3. Le di el contexto y el alcance: la lista de comprobaciones del plan, las reglas del equipo (resultados solo en Kaggle y ejecución solo en celdas) y el artículo de la Etapa 1. Le pedí revisar el estado del proyecto, implementar las comprobaciones del cuaderno 06, auditar la ejecución y redactar los borradores de resultados y documentación.
* **Verificado manualmente después:** Revisé y aprobé los cambios antes de hacer el commit `b6e6607`. Decidí, con el equipo, ejecutar el cuaderno en Colab Pro en lugar de adaptarlo a mi equipo, y coordiné con Adriel su ejecución y las barreras que debía revisar antes de abrir `test`. Revisé si el trabajo cumplía las reglas del equipo y el plan.
* **No generado por IA:** El alcance del trabajo y sus reglas, la elección del entorno de ejecución, la coordinación con el equipo y la aprobación final de lo que se versionó. Ninguna métrica proviene de la herramienta.