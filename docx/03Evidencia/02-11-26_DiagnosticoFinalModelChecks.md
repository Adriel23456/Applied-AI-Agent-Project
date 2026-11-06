# Diagnóstico de `05FinalModelChecks`

Fecha: 2 de noviembre de 2026.
Participantes: Sebastián Hernández Bonilla y asistente de IA (Claude).
Base: commit `ecb5440` de `05FinalModelChecks`.

## Alcance de esta revisión

**Se leyó:** `PlanDeDesarrollo.md`, el artículo preliminar en PDF, los cuadernos 02 a 06 (solo código, porque se versionan sin salidas), `src/ptcg_wp/`, las pruebas y los documentos de `docx/03Evidencia/` citados aquí.

**No se pudo leer:** el dataset privado de Kaggle. En esta máquina no hay token, tablas ni modelos. Por eso **las métricas de `val` de este documento vienen del plan, no se volvieron a medir**. Los nombres de archivo vienen de los cuadernos, no del índice real. La Parte 1 del cuaderno 06 hace esa comprobación contra los datos.

**No se revisaron a fondo:** los cuadernos 00 y 01 ni las fuentes LaTeX; el artículo se leyó en el PDF.

## A. Comprensión del proyecto

Se estima la probabilidad de que gane el jugador que actúa, a partir de un único estado observable de una partida del Pokémon TCG entre agentes automáticos, con aprendizaje clásico sobre datos tabulares (Track A). El problema central es de evaluación: una partida produce unos 135 estados casi idénticos que comparten etiqueta, así que toda partición, pliegue e intervalo se agrupa por partida.

Se mide por separado ordenar (AUC) y dar probabilidades correctas (log loss, Brier, calibración), en tres escenarios: A partidas nuevas, B días posteriores y C arquetipos reservados.

Hipótesis:

- **H1:** hay señal desde el inicio y crece con la partida.
- **H2:** la señal temprana no se explica solo por turno e identidad del mazo.
- **H3:** bajo cambio temporal, las probabilidades se degradan antes y más que el ordenamiento.

## B. Estado del desarrollo

| Componente | Estado | Evidencia |
|---|---|---|
| Tablas: 55 196 partidas y 7 540 389 estados; 7 286 386 filas útiles | Según documentos | `DiccionarioDeDatos.md`, secciones 4 y 5 |
| Particiones A, B y C | Código y pruebas | `src/ptcg_wp/splits.py`, `tests/test_particiones.py` |
| Escalera B0 a B4 en `val` | Según el plan | AUC A 0.500/0.677/0.761/0.803/0.835; B 0.500/0.668/0.728/0.761/0.786; C 0.500/0.671/0.760/0.806/0.836 |
| LightGBM | No sustituye a B4 | `28-10-26_ProtocoloLightGBM.md` y plan |
| Ablaciones en `val` | Según el plan | Recursos y tablero es la familia esencial |
| H2 en `val` | Sin comparar por etapa | AUC restringido/completo: A 0.7333/0.8346, B 0.6139/0.7863, C 0.7433/0.8355 |
| Modelo final | Exportado, sin calibrar | `ptcg_wp.predictor`, `modelo_final/` en Kaggle |

**Pendiente:** todo `05FinalModelChecks`. Al iniciar la rama, el cuaderno 06 solo traía preparación y pruebas: ningún check estaba implementado y nadie había medido `calib` ni `test`, según el plan, la auditoría del 29 de octubre y el código.

## C. Arquitectura experimental

```text
Corpus público (10 días) → 00_arranque: ingest.py + features.py → estados_*.parquet, partidas_*.parquet
    → splits.py → particiones.parquet (por partida; etapas con cortes de train)
    → 02 B0 y B1 → 03 B2 → 04 B3 → 05 B4, LightGBM, ablaciones, H2 y modelo_final
    → dataset privado de Kaggle (tablas + resultados, índice con SHA-256 y commit)
    → 06 evaluación final → evaluacion_final/ en Kaggle
```

Todos los modelos usan 62 características públicas, sin ids de carta; H2 usa cuatro entradas. Cada partida pesa lo mismo y las métricas salen de `ptcg_wp.evaluation`. Hiperparámetros de B4: Optuna TPE, 20 trials, 3 pliegues por partida sobre las 11 285 partidas que son `train` en A, B y C; trial 20. Semilla 2026; B3 usa semilla efectiva 2030.

## D. Estado del cuaderno 06

**Al iniciar:** portada, preparación (clona la rama, instala, configura Kaggle, baja 21 tablas y todos los resultados a `/content`), pruebas y una lista de recomendaciones.

**Dependencias:** Colab con Linux, rutas fijas en `/content`, token de Kaggle con acceso al dataset y código ya subido a GitHub, porque la celda 1 clona la rama.

**Ahora:** 28 celdas con las partes 0 a 9 descritas en la portada. La lógica está en `src/ptcg_wp/evaluacion_final.py`. Ninguna celda se ha ejecutado con datos reales.

## E. Contraste con el plan y el artículo

| Tema | Artículo o plan | Implementado | Valoración |
|---|---|---|---|
| Corpus | 52 085 partidas | 55 196 | Justificado; Kaggle agregó episodios. Pendiente en `06PendientesDelArticulo` |
| Búsqueda de B4 | CV agrupada, anidada si el costo lo permite | 3 pliegues sobre la intersección de `train` | Justificado y documentado |
| Escenario C | Mazos reservados | Arquetipos por Pokémon principal | Documentado; mide arquetipos nuevos, no cartas nuevas |
| Escenario B | Días tempranos y tardíos | Días completos, sin el 17 de junio | Documentado |
| Semillas | Repetir con varias semillas (IV-F) | Una semilla | **Desviación abierta**: decisión 6 de los acuerdos del 12 de octubre |
| Explicabilidad | Coeficientes, permutación agrupada, ablaciones y SHAP (IV-E) | Ablaciones y SHAP | **Desviación abierta**: coeficientes y permutación no están en el plan |
| Ablación de contexto de mazo | Bloque de ids (IV-D1) | H2 de cuatro entradas; no se ejecutó la de 64 | Documentado |
| Referencias | Plan: B0, B2 y literatura | Se agrega B1 | El criterio de éxito del artículo (III-D) es superar a B1, y el plan no lo menciona |
| Calibración | Artículo: isotónica; plan: "isotónica o Platt" | Isotónica principal y Platt de contraste | Compatible con ambos |

## F. Siguientes actividades

1. Revisar el protocolo como equipo y congelarlo con un commit.
2. Subir la rama; la celda 1 de Colab solo ve lo que está en GitHub.
3. Ejecutar el cuaderno en Colab Pro, una sola persona, de arriba abajo.
4. Escribir la interpretación al final del cuaderno y marcar los pendientes del plan con sus cifras.
5. Versionar el cuaderno con salidas y completar la declaración de IA.
6. Entregar en TecDigital. Después, `06PendientesDelArticulo`.

## G. Riesgos e inconsistencias

**Metodológicos**

1. **El orden sugerido exponía `test`.** El cuaderno dejaba SHAP y la revisión de fuga para después de `test`. Se movieron antes y la celda de `test` depende de ellos.
2. **Comparar directamente las caídas de AUC y log loss favorecía a H3.** Están en escalas distintas. El protocolo decide con la descomposición MCB/DSC, en las mismas unidades y sobre las mismas partidas.
3. **Las etapas mezclan duración y progreso.** Las partidas cortas no llegan a `final`, y H1 debe controlarlo. Se usa una cohorte con estados en las tres etapas.
4. **B y A difieren en tamaño de entrenamiento** (27 643 y 33 066 partidas). Parte de la diferencia en H3 puede deberse a eso; las curvas de aprendizaje lo acotan.
5. **Calendario y versión del motor siguen confundidos.** B mide su efecto conjunto.

**Hallazgo nuevo: el AUC de B3 depende levemente del tamaño de lote**

`evaluate_stream` predijo B3 por lotes con `n_jobs=2`. El bosque suma árboles en orden distinto según el hilo, cambia el último bit de algunas filas (2.2e-16) y rompe empates exactos. En un corpus sintético de 2398 filas, 355 filas cambiaron y los valores únicos pasaron de 599 a 634; con `n_jobs=1` la diferencia desaparece. En esos corpus diminutos el AUC varió entre 1e-5 y 1.2e-4. Log loss y Brier no se afectan. No invalida B3: en el corpus real debería ser menor, pero no se midió. El cuaderno 06 predice todo junto y lo registra en su verificación.

**Reproducibilidad y almacenamiento**

6. **Publicaciones simultáneas.** Si dos personas publican a la vez, una versión de Kaggle puede perder lo de la otra. Solo una persona debe ejecutar el cuaderno 06.
7. **Trazabilidad histórica.** B2 y B3 no tienen un commit único de entrenamiento ni tiempo exacto; ya está documentado.
8. **Versión de `shap`.** Se fijó 0.54.1 porque es la probada con scikit-learn 1.7.2 (error de aditividad 3e-14). No se probó en el Python de Colab. Si `pip` cambia una librería ya cargada, hay que reiniciar el runtime.
9. **Las pruebas no están verificadas en Linux.** Esta máquina es Windows. Fallan 11 pruebas tanto en el commit original como con estos cambios, por bloqueo de archivos o por la herramienta `kaggle` simulada, y 7 se omiten. El cuaderno 06 las corre en Colab; ahí se espera `103 passed`.

**Inconsistencias de documentación**

10. `ReglasGit.md` dice que las tablas de métricas se versionan a propósito; la indicación actual del equipo es que los resultados viven solo en Kaggle. Se siguió la indicación actual. Conviene corregir `ReglasGit.md`.
11. `29-10-26_AuditoriaBaselinesB0B3.md` cita rutas viejas (`results/baseline0_1/`, `src/ptcg_wp/baselines.py`) que ya no existen. El plan usa `results/...`, que hoy son rutas del dataset de Kaggle.
12. `DiccionarioDeDatos.md` (secciones 11 y 12) todavía habla de 24 pruebas, y `GuiaDeAmbiente.md` lista cuadernos con los nombres antiguos.
13. `README.md` y el plan mantenían sin completar la reproducción y la URL real del dataset del artículo. La reproducción ya está escrita; la URL sigue pendiente.