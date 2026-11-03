# Declaración de Uso de Herramientas de IA

**Proyecto:** Estimación de la Probabilidad de Victoria a partir del Estado de Juego en el Pokémon Trading Card Game: un Estudio de Clasificación Tabular con Control Explícito de Fuga de Información

**Curso:** IC-6200 — Inteligencia Artificial, ITCR · II Semestre 2026 · Track A

**Equipo:** Adriel S. Chaves Salazar · Daniel Duarte Cordero · Sebastián Hernández Bonilla

**Cubre:** Etapa 2 — Modelado y evaluación

**Estado:** BORRADOR. Debe completarse después de ejecutar el cuaderno 06 y antes de la entrega. Lo que falta está marcado con `[COMPLETAR]`.

Esta sección se suma a `Etapa1UsoDeIA.md`, no la sustituye.

---

## 1. Herramientas utilizadas

| Herramienta | Propósito en esta etapa |
| --- | --- |
| **Claude (Claude Code, Opus 5.5)** | En `05FinalModelChecks`: revisión del repositorio y del artículo, redacción del protocolo de evaluación final, implementación de la lógica y las pruebas de evaluación, escritura de las celdas del cuaderno 06 y borradores de documentación. |
| `[COMPLETAR]` | `[COMPLETAR: herramientas usadas en las ramas 03 y 04 por cada integrante]` |

---

## 2. Dónde se usó la IA y qué se hizo manualmente después

### 2.1 Rama `05FinalModelChecks`

**Qué hizo la herramienta.** Reconstruyó el estado del proyecto a partir del repositorio y el artículo (`02-11-26_DiagnosticoFinalModelChecks.md`). Propuso el protocolo (`02-11-26_ProtocoloEvaluacionFinal.md`), incluidas tres decisiones de método: mover SHAP y la revisión de fuga antes de `test`, decidir H3 con la descomposición de calibración y discriminación, y controlar la duración en H1 con una cohorte de partidas. Implementó `src/ptcg_wp/evaluacion_final.py`, `tests/test_evaluacion_final.py` y las celdas de `notebooks/06_evaluacion_final.ipynb`, y comprobó el cuaderno con un corpus inventado. Redactó el borrador de la sección de reproducción del `README.md` y este documento.

**Qué no hizo la herramienta.** No tuvo acceso al dataset de Kaggle y no ejecutó el cuaderno con los datos del proyecto. Ninguna métrica de `calib` o `test` proviene de ella. Los resultados los produce el código del cuaderno, ejecutado por el equipo.

**Verificado manualmente.** `[COMPLETAR: quién revisó el protocolo y lo aprobó antes de abrir test; quién revisó el código]`

**No generado por IA.** `[COMPLETAR: interpretación de resultados, hallazgos de SHAP y veredicto final, si los escribió el equipo]`

### 2.2 Ramas `03DataCollectionAndEnvironmentSetup` y `04MainAIModelTrainingAndDevelopment`

`[COMPLETAR. Los documentos de docx/03Evidence registran participación de un asistente de IA, por ejemplo en 12-10-26_AcuerdosTecnicosModelado.md y 28-10-26_ProtocoloLightGBM.md.]`

---

## 3. Límites establecidos por el equipo

Se mantienen los límites de la Etapa 1. En esta etapa se suman:

* **El protocolo se fija antes de abrir `test`.** Las reglas de decisión no cambian al ver los resultados.
* **`test` se usa una sola vez.** Ninguna selección de modelo o calibrador depende de sus números.
* **Ningún resultado se genera con IA.** Cada cifra proviene de una celda ejecutada y queda trazada en el dataset del equipo.
* **Los resultados con datos sintéticos no son resultados del proyecto.** Solo prueban que el código corre.

---

## 4. Declaración por integrante

Cada miembro completa su propio bloque antes de la entrega.

### Adriel S. Chaves Salazar

* **Herramientas utilizadas:** `[COMPLETAR]`
* **Dónde y para qué:** `[COMPLETAR]`
* **Verificado manualmente después:** `[COMPLETAR]`
* **No generado por IA:** `[COMPLETAR]`

### Daniel Duarte Cordero

* **Herramientas utilizadas:** `[COMPLETAR]`
* **Dónde y para qué:** `[COMPLETAR]`
* **Verificado manualmente después:** `[COMPLETAR]`
* **No generado por IA:** `[COMPLETAR]`

### Sebastián Hernández Bonilla

* **Herramientas utilizadas:** Claude (Claude Code, Opus 5.5).
* **Dónde y para qué:** Ver la sección 2.1. `[COMPLETAR: otros usos en esta etapa]`
* **Verificado manualmente después:** `[COMPLETAR]`
* **No generado por IA:** `[COMPLETAR]`
