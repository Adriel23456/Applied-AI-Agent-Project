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
| **Claude (Claude Code, Opus 5.5)** | En `05FinalModelChecks`: revisión del repositorio y del artículo, redacción del protocolo de evaluación final, implementación de la lógica y las pruebas de evaluación, escritura de las celdas del cuaderno 06, auditoría de las salidas ya ejecutadas y borradores de documentación, incluido el documento de resultados. |
| `[COMPLETAR]` | `[COMPLETAR: herramientas usadas en las ramas 03 y 04 por cada integrante]` |

---

## 2. Dónde se usó la IA y qué se hizo manualmente después

### 2.1 Rama `05FinalModelChecks`

**Qué hizo la herramienta.** Reconstruyó el estado del proyecto a partir del repositorio y el artículo (`02-11-26_DiagnosticoFinalModelChecks.md`). Propuso el protocolo (`02-11-26_ProtocoloEvaluacionFinal.md`), incluidas tres decisiones de método: mover SHAP y la revisión de fuga antes de `test`, decidir H3 con la descomposición de calibración y discriminación, y controlar la duración en H1 con una cohorte de partidas. Implementó `src/ptcg_wp/evaluacion_final.py`, `tests/test_evaluacion_final.py` y las celdas de `notebooks/06_evaluacion_final.ipynb`, y comprobó el cuaderno con un corpus inventado. Redactó el borrador de la sección de reproducción del `README.md` y este documento.

Después de la ejecución, la herramienta auditó las salidas guardadas del cuaderno y redactó un borrador de `04-11-26_ResultadosEvaluacionFinal.md` y de la celda de interpretación. Todas las cifras se copiaron de esas salidas; la herramienta no calculó ninguna.

**Qué no hizo la herramienta.** No tuvo acceso al dataset de Kaggle y no ejecutó el cuaderno con los datos del proyecto. Ninguna métrica de `calib` o `test` proviene de ella. Los resultados los produce el código del cuaderno, que Adriel ejecutó en Colab; Adriel también corrigió la detección de errores de `store.py` que apareció durante esa ejecución.

**Verificado manualmente.** El equipo decidió dónde ejecutar (Colab Pro), revisó qué se subía antes de cada commit y comprobó que la ejecución pasara las barreras del cuaderno (pruebas, verificación en `val` y revisión de fuga). 

**No generado por IA.** La ejecución del cuaderno y sus resultados, la corrección de `store.py`, la decisión de dónde y quién ejecutaba, y la aprobación de los commits. 

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
* **Dónde y para qué:** En la rama `05FinalModelChecks` lo usé como asistente de programación y redacción, según la sección 2.1. Le di el contexto y el alcance: la lista de comprobaciones del plan, las reglas del equipo (resultados solo en Kaggle y ejecución solo en celdas) y el artículo de la Etapa 1. Le pedí revisar el estado del proyecto, implementar las comprobaciones del cuaderno 06, auditar la ejecución y redactar los borradores de resultados y documentación. 
* **Verificado manualmente después:** Revisé y aprobé los cambios antes de hacer el commit `b6e6607`. Decidí, con el equipo, ejecutar el cuaderno en Colab Pro en lugar de adaptarlo a mi equipo, y coordiné con Adriel su ejecución y las barreras que debía revisar antes de abrir `test`. Revisé si el trabajo cumplía las reglas del equipo y el plan. 
* **No generado por IA:** El alcance del trabajo y sus reglas, la elección del entorno de ejecución, la coordinación con el equipo y la aprobación final de lo que se versionó. Ninguna métrica proviene de la herramienta. 
