# Ejecución de los cuadernos

Qué hace cada cuaderno, dónde se ejecuta, en qué orden, cuánto tarda y cómo obtener las cifras del artículo. Para preparar el ambiente (Kaggle, Colab, token y dependencias), ver primero [`GuiaDeAmbiente.md`](../GuiaDeAmbiente.md). Para el agente en la PC (Claude Code, servidor MCP y orquestador), ver [`GuiaDelAgente.md`](../docx/05AmbienteDeDesarrollo/GuiaDelAgente.md).

Rama actual de trabajo: `08AgentValidationAndSimulator` (Etapa 3).

---

## 1. Dos lugares de ejecución

| Dónde | Cuadernos | Por qué |
|---|---|---|
| **Colab** | `00` a `07` y `09` | Necesitan las tablas del corpus (varios GB) y, algunos, horas de cómputo |
| **PC** (VS Code con el kernel de `.venv`) | `08` y `10` | Usan Claude Code con la membresía del equipo, que corre en la PC |

Los cuadernos de la PC no clonan nada: usan el repositorio tal como está en la PC, en la rama que tengas activa. Antes de abrirlos hay que haber instalado `.venv` y bajado los archivos del agente (`GuiaDelAgente.md`, sección 2).

---

## 2. Cómo funciona un cuaderno de Colab

1. **La primera celda prepara todo.** Clona o actualiza el repositorio en `/content/repo`, instala `requirements.txt`, muestra los núcleos y la RAM, pide el token de Kaggle sin mostrarlo y baja a `/content/datos` las tablas que falten. Cada cuaderno puede abrirse solo, sin ejecutar antes otro.
2. **Cada celda que calcula algo declara los archivos que produce** y llama a `store.asegurar(archivos, calcular, mensaje)`:
   - si **todos** están en Kaggle, los baja a `/content/resultados/<ruta>`, comprueba su SHA-256 y no recalcula;
   - si falta alguno, calcula, comprueba que se crearon y publica una versión nueva del dataset, sin borrar lo publicado antes.
3. **No hay interruptores** (`EJECUTAR = False`, `CREAR`, `CONSTRUIR`): ejecutar una celda hace lo que haga falta.
4. **Rama clonada.** La variable `BRANCH` de la primera celda indica qué rama se clona:

   | Cuadernos | `BRANCH` |
   |---|---|
   | `00` a `05` | `04MainAIModelTrainingAndDevelopment` |
   | `06` | `05FinalModelChecks` |
   | `07` | `07MultiAgentIntegration` |
   | `09` | `08AgentValidationAndSimulator` |

   Esas ramas se conservan. Para ejecutar la versión entregada, cambia `BRANCH` a `Stage2`, `Stage3` o `master`.
5. **Pruebas primero.** Los cuadernos del agente (`07` a `10`) tienen como segunda celda las pruebas automáticas. Si fallan, la celda se detiene y no se calcula nada.

Todos los resultados (CSV, JSON, figuras y modelos `.joblib`) viven en el dataset privado `adrielchavessalazar/ptcg-wp-tablas`, nunca en Git. En Kaggle los nombres van aplanados (`results__b4__final__...`), y el índice `results__indice.csv` guarda el SHA-256, el commit y la fecha de cada archivo. El significado de cada carpeta está en `results__README.md` del dataset.

---

## 3. Cuadernos, en orden

### Etapas 1 y 2: datos, modelos y evaluación (Colab)

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

### Etapa 3: agente y validación

| Cuaderno | Dónde | Qué hace | Carpeta en Kaggle | Si ya está en Kaggle | Si falta |
|---|---|---|---|---|---|
| `07_agente` | Colab | Perfil del dominio de entrenamiento, repeticiones reales de ejemplo, verificación del agente con partidas reales y demostración de las herramientas | `agente/dominio.json`, `agente/ejemplos/` | ~5 min | ~15 min |
| `08_agente_orquestador` | PC | Pruebas, tres consultas con el orquestador multiagente (planificador y redactor con Claude) y copia del registro como evidencia | Nada (escribe `docx/03Evidencia/DD-MM-AA_RegistroOrquestador.jsonl`) | — | ~1 min por consulta |
| `09_validacion_agente` | Colab | Nivel N1 del protocolo de validación: elige los casos, extrae sus observaciones y corre la batería sin LLM | `agente/validacion/` | ~5 min | ~20 min (bajar 166 repeticiones del corpus público tarda unos 7) |
| `10_validacion_llm` | PC | Repite N1 con las correcciones de la rama y corre el nivel N2: 31 consultas al orquestador con Claude (normales, errores del modelo y adversas) | Nada (escribe `docx/03Evidencia/DD-MM-AA_ValidacionN1Corregida.csv`, `_ValidacionN2.csv` y `_ValidacionN2.jsonl`) | — | ~20–30 min |

El protocolo de `09` y `10` está en [`docx/03Evidencia/08-11-26_ProtocoloValidacionAgente.md`](../docx/03Evidencia/08-11-26_ProtocoloValidacionAgente.md), escrito antes de ejecutar.

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

### Cuaderno 07 por partes

| Parte | Celda | Produce |
|---|---|---|
| 1 | `PARTE 1 - PERFIL DEL DOMINIO` | `agente/dominio.json`: rangos de las 62 características, cartas activas vistas y cortes de etapa, solo con `train` de A |
| 2 | `PARTE 2 - EJEMPLOS REALES` | `agente/ejemplos/partida_<id>.json`: 4 partidas de `test` de A del 22 de julio |
| 3 | `PARTE 3 - VERIFICACION CON PARTIDAS REALES` | Nada: comprueba que el agente da la misma probabilidad que el modelo final en cada estado |
| 4 | `PARTE 4 - DEMOSTRACION DE LAS HERRAMIENTAS` | Nada: salida de cada herramienta y casos límite |

### Cuaderno 10 por partes

| Parte | Celda | Produce |
|---|---|---|
| 1 | `PARTE 1 - MODELO, EJEMPLOS Y CASOS DE VALIDACION` | Baja de Kaggle lo que falte y lo verifica |
| 2 | `PARTE 2 - BATERIA N1 CON LAS CORRECCIONES` | `docx/03Evidencia/DD-MM-AA_ValidacionN1Corregida.csv` y la comparación con la corrida del cuaderno 09 |
| 3 | `PARTE 3 - NIVEL N2 CON CLAUDE` | `docx/03Evidencia/DD-MM-AA_ValidacionN2.csv` y `.jsonl` |
| 4 | `PARTE 4 - METRICAS DEL AGENTE Y REVISION HUMANA` | Nada: métricas y respuestas para revisar a mano |

### Cuaderno 09 por partes

| Parte | Celda | Produce |
|---|---|---|
| 1 | `PARTE 1 - CASOS DE VALIDACION` | `agente/validacion/casos.csv`, `observaciones.json` y `partidas.json.gz` |
| 2 | `PARTE 2 - BATERIA N1` | `agente/validacion/resultados_n1.csv` (un caso por fila), `detalle_n1.csv` y `latencias_n1.csv` |
| 3 | `PARTE 3 - ANALISIS` | Nada: tablas por población, errores muy seguros y dirección de los cambios |

---

## 4. Cuadernos de la PC (08 y 10)

1. Abre la carpeta del repositorio en VS Code, en la rama que quieras ejecutar.
2. Abre el cuaderno y elige el kernel: **Select Kernel → Python Environments → `.venv`**. Si `.venv` no aparece: **Enter interpreter path... → Find...** y elige `.venv\Scripts\python.exe` (en Linux o macOS, `.venv/bin/python`).
3. Haz clic en **Run All**.

La primera celda comprueba que Claude Code está instalado. Las consultas usan la membresía: si se agota el límite, la celda falla con `Claude respondio con error` y basta con esperar a que se renueve. Pasos completos y errores frecuentes: `GuiaDelAgente.md`, secciones 7 y 9.

---

## 5. Cómo obtener las cifras del artículo

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

Las cifras del agente salen de `07_agente` (verificación con partidas reales: 642 estados, diferencia máxima 0.0), de `08_agente_orquestador` (registro de evidencia) y de `09` y `10` (validación).

**Recalcular desde cero.** Usa un dataset de Kaggle propio y vacío (en `configs/datos.yaml`) y ejecuta los cuadernos 00 a 06 en orden. Con la semilla fija (`SEED = 2026`) y las versiones de `requirements.txt`, las particiones son idénticas y los modelos deben dar las mismas cifras dentro de la precisión numérica. El tiempo total es de varios días de cómputo, sobre todo por B2, B3 y la búsqueda de B4. Después, `07` y `09` reconstruyen lo del agente en menos de una hora.

---

## 6. Reglas de los cuadernos que leen `test`

`06_evaluacion_final` abre `test`, que se usa una sola vez para evaluar los modelos. Sigue el protocolo [`docx/03Evidencia/02-11-26_ProtocoloEvaluacionFinal.md`](../docx/03Evidencia/02-11-26_ProtocoloEvaluacionFinal.md), escrito antes de abrirlo.

- Una sola persona lo ejecuta.
- El servidor no debe tener cambios locales y nadie más debe estar publicando en Kaggle.
- La celda de `test` no corre si la revisión de fuga no aprobó o si faltan la calibración o las curvas.
- Si una sesión se corta, vuelve a ejecutar desde arriba: lo publicado se baja y no se recalcula.

`07_agente` y `09_validacion_agente` leen partidas de `test` de A para probar el agente, pero no eligen, ajustan ni recalibran ningún modelo: el modelo final ya está fijo desde la Etapa 2.

---

## 7. Trabajo en paralelo

Si dos personas publican al mismo tiempo, la versión que termina después puede no incluir lo que subió la otra. Avisen en el grupo antes de ejecutar celdas que calculan algo nuevo. Cada publicación tarda unos minutos, y Kaggle tarda otros minutos en mostrar la versión nueva a otros servidores. Los cuadernos de la PC (`08` y `10`) no publican en Kaggle, así que pueden correr en paralelo.

---

## 8. Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| Kaggle 401 | Token incorrecto | Volver a ejecutar la primera celda; si el secreto no se reconoce, aparece un campo oculto para pegarlo |
| Kaggle 403 o "no está en Kaggle" en todas las tablas | Tu usuario no tiene acceso al dataset | Adriel lo agrega en el dataset > Settings > Sharing |
| La publicación falla | Error de red o de Kaggle | Los archivos quedan en `/content/resultados`; volver a ejecutar la celda los publica sin recalcular |
| "El índice dice que X existe, pero no se pudo bajar" | Versión muy reciente | Esperar unos minutos y volver a ejecutar |
| `Kaggle pidio esperar (429)` en `09` | Kaggle limita cuántas descargas se hacen seguidas | Nada: la celda espera y reintenta sola |
| `no se pudo bajar la partida ...` en `09` | Fallo de red, o Kaggle siguió respondiendo 429 tras varios reintentos | Esperar unos minutos y volver a ejecutar la celda: las partidas ya bajadas en esa sesión no se repiten |
| `ModuleNotFoundError: ptcg_wp` o `ptcg_agente` | `src/` no está en el path | Ejecutar la primera celda |
| El repo en Colab no tiene mis cambios | Falta el push | `git push` desde la PC y volver a ejecutar la primera celda |
| Aviso de versión de scikit-learn distinta | El servidor traía otra versión | Reiniciar el runtime y volver a ejecutar la primera celda |
| `fallaron pruebas` en la segunda celda | El código de la rama clonada tiene un error | Revisar la salida de `pytest`; no seguir hasta corregirlo |
| Se perdió todo | El servidor se reinició | Normal: volver a ejecutar desde arriba |
| `no se encontro 'claude'` en `08` o `10` | Claude Code no está instalado o VS Code se abrió antes de instalarlo | Instalarlo (`GuiaDelAgente.md`, sección 3.1) y reiniciar VS Code |
| `no hay manifiesto.json` en `08` o `10` | No se bajaron los archivos del agente | `python -m ptcg_agente.artefactos` (`GuiaDelAgente.md`, sección 2) |