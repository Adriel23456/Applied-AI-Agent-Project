# Auditoría de cumplimiento de B0 a B3

**Alcance:** contraste de los baselines B0, B1, B2 y B3 con el contrato de modelado de la sección 10 del [Diccionario de Datos](../05AmbienteDeDesarrollo/DiccionarioDeDatos.md#10-contrato-para-modelar-obligatorio-en-los-cuadernos-02-en-adelante) y los entregables de las etapas 04, 05 y 06 del [Plan de Desarrollo](../01SeguimientoDeTareas/PlanDeDesarrollo.md). B4 se excluye de la auditoría.

**Resultado actualizado:** el protocolo de selección y evaluación de B0–B3 está implementado y los resultados disponibles cubren globalmente y por etapa A/B/C. B0–B3 comparten el módulo de métricas, con rutas en memoria y por lotes. La sección 10 documenta ambas rutas de carga y el ajuste incremental de B2. Para la búsqueda de B2/B3 se registra una duración calendario aproximada según el recuerdo del equipo y el historial de commits de implementación y reanudación. No hubo un commit único asociado al entrenamiento de cada artefacto ni se registró su tiempo exacto de cómputo. Los entregables finales de las etapas 05/06 siguen abiertos.

## Contrato de la sección 10

| Requisito | B0/B1 | B2 | B3 | Evidencia y observación |
|---|---|---|---|---|
| Cargar datos útiles con partición y etapa correctas | Conforme en train/val | Conforme en train/val | Conforme en train/val | `ScenarioStream` aplica `usable`, particiones por `game_id` y cortes de train; su equivalencia con `load_scenario` para train/val se comprueba en un corpus sintético. El contrato actualizado admite esta ruta por memoria. B0/B1 usan el iterador diario, que depende de la unicidad de partida entre días auditada para el corpus original. |
| Ajustar transformaciones con train solamente | Conforme para B0/B1 | Conforme al procedimiento incremental documentado | Conforme: no requiere transformación | B0/B1 calculan prevalencia y `hp_unit` solo en train. B2 ajusta `StandardScaler` incrementalmente con fit y luego guarda escalador y clasificador en un `Pipeline`. El ajuste del escalador ocurre fuera de `Pipeline.fit` para limitar memoria; val/calib/test no lo ajustan. |
| Validación cruzada agrupada por `game_id` | No aplica; no hay búsqueda de hiperparámetros | Conforme | Conforme | B2 y B3 usan `GroupKFold` agrupado por partida en `src/ptcg_wp/b2.py` y `src/ptcg_wp/b3.py`. |
| Roles de train, val, calib y test | Conforme | Conforme | Conforme | Se ajusta con train y se comparan configuraciones en val. Los cuadernos y resultados reservan calib y test para la etapa final. No se encontró evidencia de uso de test en la selección B0–B3. |
| Excluir IDs de carta del estado completo de 62 características | No aplica: B0/B1 son referencias de prevalencia y heurística | Conforme | Conforme | Los cuadernos B2 y B3 validan que la lista principal tenga 62 características (`assert len(FEATURES) == 62`). `feature_columns` excluye IDs salvo la opción explícita de ablación. |
| Métricas globales y por etapa con cantidad de partidas | Conforme | Conforme | Conforme | El resumen reproducido desde los CSV de origen contiene 48 filas únicas, para A/B/C, B0–B3 y global/inicio/medio/final. Está en `results/resumen_baselines/metricas_val_B0_B3.csv`; el README correspondiente reporta resultados y límites. |
| Informar A, B y C por separado | Conforme | Conforme | Conforme | Los CSV y los reportes mantienen filas por escenario. El macro-AUC de B3 solo se usa internamente para elegir una configuración común; no sustituye las métricas individuales. |
| Semilla de la ejecución | Conforme | Conforme | Conforme | B0/B1 registra semilla 2026; B2 registra semilla 2026. B3 conserva semilla base 2026 y semilla efectiva 2030 en los modelos recuperados. |

### Alcances y límites documentados de B0–B3

1. **Trazabilidad B2/B3:** los CSV y metadatos no contienen tiempos exactos por artefacto; ese dato nunca se midió ni se guardó. El recuerdo del equipo estima unos cuatro días calendario de búsqueda para B2 y tres para B3, incluyendo interrupciones y reanudaciones; son estimaciones del proceso, no horas de cómputo. Git registra cambios de código y reanudación en varios commits, pero ninguno identifica por sí solo el código exacto que produjo cada archivo final. Los metadatos y hashes verifican configuración y uso del train completo. La duración aproximada y el historial de desarrollo ya quedan registrados; no es un pendiente para repetir entrenamientos.
2. **Métricas comunes:** B0–B3 comparten `ptcg_wp.evaluation`: `metric_rows` para predicciones en memoria y `evaluate_stream` para modelos evaluados por lotes. La equivalencia de las rutas se comprueba con pesos por partida, etapas y empates en datos sintéticos. El pendiente general del Plan sigue abierto para la integración de B4, que no se incluyó en este trabajo.
3. **B2:** los tres modelos se ajustaron con todo el train propio de su escenario; ninguno alcanzó la tolerancia del gradiente al llegar a 600 épocas. Se cierra con esa limitación descrita en `docx/03Evidence/25-10-26_B2SeleccionFinalC.md`.
4. **B3:** hay una configuración compartida elegida por macro-AUC global de val, pero tres artefactos de ajuste para evaluar los protocolos A, B y C. Eso no equivale a tres configuraciones finalistas. Aún no se ha escogido el único artefacto para la aplicación; debe definirse durante la integración según el escenario de uso.
5. **B1:** la fórmula ejecutada se adoptó posteriormente como decisión técnica delegada. El `registro.json` conserva correctamente el estado histórico de propuesta al momento de ejecución. El método de Newton tuvo un máximo de seis iteraciones y la corrida no guardó si llegó a la tolerancia; por tanto, la convergencia de B1 es desconocida.
6. **B2 por fila:** la demo prueba el solapamiento de partidas cuando se divide por filas y conserva un control agrupado sin solapamiento. La diferencia de AUC cambia de signo entre escenarios, por lo que la evidencia demuestra el problema del procedimiento, no una inflación universal del AUC.

## Estado de los entregables por etapa

### Etapa 04: baselines y desarrollo

| Entregable sin B4 | Estado | Evidencia |
|---|---|---|
| B0 | Cerrado para A/B/C | `results/baseline0_1/` |
| B1 | Fórmula adoptada; límite de convergencia reportado | `results/baseline0_1/` y `results/resumen_baselines/` |
| B2 y demostración de fuga | Resultados y artefactos recuperados, verificados y documentados | `results/baseline2/` |
| B3 | Una configuración común; tres ajustes de evaluación recuperados y documentados | `results/baseline3/` |
| Resumen comparativo B0–B3 | Cerrado en val, por escenario y etapa | `results/resumen_baselines/` |
| Funciones de evaluación comunes para B0–B3 | Implementadas y verificadas en datos sintéticos | `src/ptcg_wp/evaluation.py` y `tests/test_b2_streaming.py`. El alcance general del Plan incluye B4 y sigue abierto. |
| Registro con escenario, modelo, parámetros, semilla, métricas, duración y trazabilidad de código | Cerrado con precisión histórica | B0/B1 conserva el registro original. Para B2/B3 se reporta la duración calendario aproximada de la búsqueda y el historial de commits de desarrollo/reanudación; se distingue de un tiempo exacto de ajuste y de un commit único de entrenamiento que no existieron. |
| Evaluación final de B0–B3 en test | Pendiente de etapa 05 | `test` sigue reservado; no usarlo para selección. |
| Interfaz de observación a probabilidad para la aplicación | Pendiente | No la producen por sí solos los `.joblib`. |

### Etapas 05 y 06

La existencia de métricas de `val` no completa la evaluación final. Según el Plan de Desarrollo, permanecen pendientes: evaluación única en test por escenario, intervalos por remuestreo de partidas, comparación final con referencias, curvas de aprendizaje, análisis de errores, SHAP, calibración con calib, prueba de H3 y veredictos H1–H3. Tampoco se cierran la metodología y resultados finales del artículo ni las correcciones editoriales del listado de etapa 06. Estas actividades requieren los resultados y decisiones finales de la etapa 05; no se deben presentar como terminadas por haber cerrado los baselines.

## Fuentes de verificación

- Contrato: `docx/05AmbienteDeDesarrollo/DiccionarioDeDatos.md`, sección 10.
- Lista de entregables y estado: `docx/01SeguimientoDeTareas/PlanDeDesarrollo.md`, etapas 04, 05 y 06.
- Ejecución y archivos disponibles: `notebooks/README_ejecucion_baselines.md`.
- Resultados agregados: `results/resumen_baselines/README.md` y `metricas_val_B0_B3.csv`.
- Registro histórico reconstruido con campos desconocidos explícitos: `results/resumen_baselines/registro_historico_B2_B3.json`.
- Detalle B2 y fuga: `results/baseline2/README.md` y `docx/03Evidence/25-10-26_B2SeleccionFinalC.md`.
- Selección y artefactos B3: `results/baseline3/README.md` y `docx/03Evidence/28-10-26_VerificacionFinalistasB2B3.json`.
- Implementación de carga y métricas: `src/ptcg_wp/data.py`, `src/ptcg_wp/baselines.py`, `src/ptcg_wp/evaluation.py`, `src/ptcg_wp/b2.py`, `src/ptcg_wp/b2_streaming.py` y `src/ptcg_wp/b3.py`.
