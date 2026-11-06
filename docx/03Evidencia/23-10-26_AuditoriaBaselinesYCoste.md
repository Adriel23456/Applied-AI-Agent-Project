# Auditoría de baselines, reanudación y costo de búsqueda

Fecha: 23 de octubre de 2026. Código revisado: `ce3119f`.

## Conclusión y alcance

Se revisaron B0/B1, B2, B3, B4, el orquestador y los checkpoints. No se modificó el código de entrenamiento ni se accedió al Drive/runtime del usuario. No se puede certificar un hang remoto usando únicamente la barra de progreso. Sí se identificaron problemas reproducibles de reanudación y decisiones de búsqueda costosas.

La última salida disponible muestra el salto de estudios de árbol individual a bosque aleatorio cerca de la interrupción. Esa coincidencia impide atribuir todo el aumento de tiempo al checkpoint. La reanudación normal no debería agregar horas de espera por sí misma. Las estimaciones anteriores de varios días basadas en un solo trial no constituyen una medición del presupuesto restante.

## Hallazgos prioritarios

### 1. Reiniciar el muestreador puede repetir configuraciones: reproducido

En `b3.py`, cada invocación crea `TPESampler(seed=seed + len(candidates), multivariate=True)`. En B4 ocurre lo mismo con `seed + metric_number`. La base SQLite conserva trials, pero el código no conserva el estado interno del muestreador. Durante el arranque aleatorio, volver a crear el muestreador con la misma semilla puede repetir las propuestas iniciales.

Experimento con Optuna 4.6.0 y el espacio real de B3/bosque: ejecutar dos trials, cargar el mismo estudio con un muestreador recién creado con la misma semilla y ejecutar otro. El tercer trial repitió exactamente los parámetros del primero. No se repitió el identificador del trial; se repitió la configuración, lo que desperdicia un ajuste completo. Esto no demuestra que el trial remoto esté duplicado; requiere inspeccionar su base.

Con semilla 2029, la secuencia inicial reproducida fue:

| Propuesta | Árboles | Profundidad | Mínimo por hoja | max_features |
|---|---:|---:|---:|---:|
| Primera | 50 | 8 | 19 | 0.5051 |
| Segunda | 150 | 32 | 1 | 0.5393 |

La segunda combinación puede ser mucho más cara aun dentro del bosque. Esta secuencia corresponde al código y semillas actuales; no certifica qué configuración está ejecutando Colab.

Corrección propuesta: persistir el estado del muestreador junto al checkpoint o usar una política reproducible de reanudación que evite repetir propuestas. Registrar y detectar configuraciones idénticas antes de volver a entrenar.

### 2. Diez trials no aprovechan la fase adaptativa de TPE

El muestreador conserva `n_startup_trials=10`, su valor predeterminado. Los estudios nuevos tienen presupuesto de diez trials. Por tanto, sus primeras diez configuraciones se escogen aleatoriamente; la fase guiada por resultados comenzaría después. Si se reduce el presupuesto, debe reducirse explícitamente el arranque o declararse una búsqueda aleatoria.

Fuente: [TPESampler 4.6.0](https://optuna.readthedocs.io/en/v4.6.0/reference/samplers/generated/optuna.samplers.TPESampler.html).

### 3. SQLite activo directamente sobre Google Drive: riesgo de I/O, sin bloqueo confirmado

`persistent_study()` abre la base en la carpeta de Drive y escribe heartbeats cada 60 segundos. Además escribe parámetros, atributos, resultados y estados. El código oficial de Optuna espera a que termine el hilo de heartbeat al cerrar un trial; una operación de almacenamiento atascada puede retrasar también ese cierre. Esto es una ruta plausible de espera, no evidencia de que esté ocurriendo en este runtime.

El `timeout=60` de la conexión es la espera de SQLite para ciertos bloqueos; no limita la duración de un fit ni todas las operaciones del montaje Drive. `grace_period=300` sirve para detectar heartbeats antiguos, no para cancelar un entrenamiento largo que sigue enviando heartbeats.

Un experimento local con un trial antiguo `RUNNING` y otro nuevo terminó el nuevo trial en aproximadamente 0.04 segundos. Por tanto, la mera presencia de un trial huérfano no implica que Optuna espere a que termine. Además, Optuna llama a `fail_stale_trials()` antes de pedir un nuevo trial cuando heartbeat está habilitado.

Propuesta: base activa en disco local y snapshots SQLite consistentes mediante la API de backup, publicados en Drive después de cada checkpoint durable; restaurar el último snapshot al reanudar. No copiar ingenuamente una base SQLite mientras tiene transacciones activas. El usuario debe conocer que solo el último snapshot confirmado sobrevive a un cambio de runtime.

Fuentes: [Optuna 4.6.0, bucle de optimización](https://github.com/optuna/optuna/blob/v4.6.0/optuna/study/_optimize.py), [hilo de heartbeat](https://github.com/optuna/optuna/blob/v4.6.0/optuna/storages/_heartbeat.py), [FAQ de Colab sobre I/O de Drive](https://research.google.com/colaboratory/faq.html).

### 4. Presupuesto multiplicado por tres métricas

B3 ejecuta 2 modelos × 3 métricas × 10 trials × 5 pliegues × 3 escenarios = 900 ajustes, 450 de ellos de bosque. B4 añade 3 métricas × 10 trials × 5 pliegues × 3 escenarios = 450 ajustes. Estas cifras excluyen los reajustes finales y las ejecuciones interrumpidas.

Cada configuración ya calcula AUC, log loss y Brier. Mantener estudios dirigidos a cada métrica explora configuraciones distintas, pero consume tres presupuestos separados; no hace falta entrenar por separado para calcular las otras métricas.

Alternativa: un pool común de configuraciones por modelo/escenario, con AUC como objetivo principal para TPE y registro de las tres métricas. Seleccionar de ese pool hasta tres finalistas, una por métrica. Otra opción es TPE multiobjetivo y una regla explícita para escoger finalistas. Ambas requieren documentar el cambio frente a los estudios por métrica acordados originalmente. No se introduce una suma arbitraria de métricas.

### 5. B3 relee todo el corpus en cada evaluación

B3 carga `x`, `y` y grupos en RAM una vez. Sin embargo, cada pliegue llama a `evaluate_stream()`, que cuenta estados leyendo los Parquet y luego vuelve a leer características para predecir. El filtrado de partidas se hace después de leer los lotes. También inserta predicciones fila a fila en SQLite temporal y calcula cuatro AUC: global y tres etapas.

La evaluación mantiene pesos por partida y el AUC conjunto, lo cual es correcto, pero repite mucho I/O. Hay conversiones de float32 a float64 y nuevamente a float32 dentro del árbol/bosque al predecir.

Optimización propuesta: evaluar con los índices retenidos sobre la matriz ya materializada, guardar también las etapas en esa representación y usar predicción en bloques y métricas ponderadas equivalentes. Si falta RAM para el AUC global, conservar el cálculo en disco, evitando volver a leer los Parquet. Durante la búsqueda pueden calcularse solo métricas globales; las métricas por etapa pueden reservarse para las finalistas.

### 6. No hay límites efectivos de tiempo en el pipeline actual

B3 no expone timeout. B4 acepta timeout pero `run_sequential_pipeline()` no lo transmite. Ninguno usa `trial.report()`/`should_prune()` para descartar configuraciones claramente peores después de algunos pliegues. El logging de B3 no muestra inicio/fin de cada fase de un pliegue, de modo que la barra no distingue entrenamiento, evaluación o guardado.

El timeout de `study.optimize()` se comprueba entre trials; no interrumpe por sí solo un `model.fit()` que lleva horas. Un límite duro por fit exige ejecución aislada con cancelación controlada o límites de complejidad que eviten esos casos.

### 7. El bosque puede crecer demasiado; la guarda de RAM no cubre los árboles

El espacio permite 250 árboles, profundidad ilimitada y hojas de un estado. `bootstrap=False` hace que cada árbol reciba todos los estados de ajuste, con sus pesos. Es una variante válida, pero el comentario que vincula desactivar bootstrap con respetar pesos por partida no prueba que sea la única estrategia correcta. No conviene cambiarlo automáticamente porque modifica el baseline.

La guarda estima matrices y buffers a partir de filas y características, pero no usa `n_estimators`, profundidad ni número de nodos para acotar la memoria del bosque. No garantiza prevenir un OOM por crecimiento de árboles. Los memmaps de B4 tampoco eliminan las copias por indexación de los subconjuntos.

Fuente: [scikit-learn 1.7.2, notas sobre el tamaño de RandomForestClassifier](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.RandomForestClassifier.html).

## Revisión por baseline y gaps adicionales

| Baseline | Aspectos correctos observados | Gap/costo a atender |
|---|---|---|
| B0 | Prevalencia ajustada en train y evaluación separada | Procesa archivos diarios completos; si una partida aparece en varios archivos se cuenta varias veces, al agregar medias por partida/archivo. Hay que confirmar unicidad en los datos reales. |
| B1 | Score fijo, solo pendiente/intercepto aprendidos con train | Pesos calculados por archivo, incorrectos si una partida cruza archivos. Newton tiene máximo de seis iteraciones sin informar si convergió. La fórmula sigue propuesta en los acuerdos. |
| B0/B1 notebook | Métricas ponderadas sobre el val conjunto | Concatena todo val en RAM y guarda reportes solo en `/content`, sin persistencia a Drive. |
| B2 | Escalador por fold, SGD con pesos por partida, métricas globales exactas en disco y checkpoints por fold/C | Cada época hace una pasada de entrenamiento y otra para objetivo/gradiente, durante hasta 600 épocas. Muchos pases de disco. El promedio de parámetros desde las primeras épocas puede tardar en estabilizarse. Más épocas no garantiza certificar convergencia. |
| B3 | Grupos disjuntos por game_id, pesos por partida, todas las partidas en modo full, val separado | Duplicación de propuestas al reanudar, búsqueda aleatoria inicial, exceso de I/O, recursos sin acotar y pérdida de pliegues parciales al cortar un trial. |
| B4 | Early stopping con partidas de vigilancia internas; pliegue externo y val separados; reajuste final con train | Mismos problemas de muestreador/presupuesto. La reserva de vigilancia cambia con el trial porque la semilla incluye su número; añade variación a la comparación. AUC usa un bucle Python por cada probabilidad distinta y puede ser caro con muchos estados. |

No se encontró fuga directa hacia `test` en el flujo de modelado revisado. Las métricas por etapa recalculan el peso por partida dentro de cada etapa. Esto no equivale a una certificación integral del dataset y del artículo.

Gaps transversales: los manifiestos no guardan hashes completos de contenido ni versión del espacio de búsqueda. Cambiar datos con los mismos IDs puede no invalidar un checkpoint. `pipeline_status.json` permite omitir una fase completa sin comprobar primero todos sus artefactos. La reanudación exacta interrumpida y el desempeño real en Drive no estaban cubiertos por las pruebas existentes.

## Propuesta de presupuesto para cerrar el proyecto

Primero aplicar mejoras de ingeniería que mantengan las configuraciones: recuperación del muestreador, tiempos separados de fit/evaluación/guardado, checkpoint por pliegue y reutilización de matrices/métricas. Estas medidas también permiten diagnosticar el runtime antes de gastar otro bloque de horas.

Para una búsqueda nueva de B3/bosque, propuesta concreta sujeta a documentar el cambio:

1. Un pool de 8 configuraciones por escenario, con AUC como objetivo principal, las tres métricas registradas y `n_startup_trials=3`.
2. Mantener cinco pliegues agrupados para la comparación confirmatoria. Comenzar con un piloto de un pliegue y una configuración para medir el costo de la versión optimizada.
3. Para el espacio acotado inicial: 50 árboles durante búsqueda, profundidad 8 o 12, `min_samples_leaf` 20–100, `max_features` cercano a sqrt o 0.25. Son propuestas, no hiperparámetros óptimos demostrados. Se podrá comparar 50/100 árboles solo para las mejores configuraciones si queda presupuesto.
4. Esa organización pasa de 30 a 8 configuraciones por modelo/escenario: 73% menos ajustes CV, sin garantizar el mismo porcentaje de ahorro de tiempo ni el mismo óptimo.
5. Si aun así el piloto es demasiado caro, buscar sobre una muestra fija de 1,000–3,000 partidas completas de train y confirmar una lista corta con los cinco pliegues de todo train. El modelo final se ajustaría con todo train, val compararía finalistas y test seguiría reservado. El ranking sobre la muestra puede cambiar al usar todos los datos; es una limitación a medir.
6. Preservar los estudios viejos y los resultados B2. Configuraciones evaluadas bajo el mismo protocolo completo pueden reutilizarse; resultados muestreados o con diferente protocolo se guardarán en otro estudio y no se mezclarán en un mismo ranking sin confirmación comparable.

Aplicar a B4 el mismo presupuesto medido y compartido de métricas; fijar el monitoreo por fold, vectorizar AUC y comunicar límites de tiempo reales. No lanzar toda su búsqueda sin piloto.

## Evidencia de verificación

### Implementación aplicada el 23 de octubre

Se implementó la ruta `efficient_v2`, separada de los estudios lentos y parciales en `full` para no combinar protocolos. B2 no se modifica ni se vuelve a entrenar. B3 y B4 ahora: (1) guardan métricas globales y un checkpoint JSON después de cada pliegue; (2) al reiniciar, marcan el trial interrumpido como fallido, reencolan exactamente sus parámetros y reutilizan los pliegues guardados; (3) mantienen la SQLite activa en el disco local de Colab y publican un respaldo SQLite consistente en Drive después de cada checkpoint, mediante la API de respaldo de SQLite; (4) usan tres pruebas iniciales de TPE y una semilla dependiente del avance al reanudar; y (5) registran un volcado de pila cada diez minutos desde el cuaderno para distinguir ajuste, evaluación o I/O cuando no haya salida.

La búsqueda se acotó a cinco trials por estudio. En B3, el bosque queda en 25/50/100 árboles, profundidad 8/12, hojas mínimas 20/50/100 y `max_features` sqrt/0.25/0.5; el árbol usa profundidad 4/8/12 y hojas mínimas 10/20/50. B3 calcula durante búsqueda las métricas globales exactamente sobre la matriz ya materializada, sin releer los Parquet; las métricas por etapa se conservan al evaluar los finalistas en `val`. B4 usa árboles de 8/16/31 hojas, hojas mínimas 20/50/100, el mismo conjunto de vigilancia para un pliegue dado entre trials, AUC vectorizada y un límite de 3,600 segundos por estudio de métrica. Este último límite se revisa entre trials: no puede cancelar con seguridad un `fit` que ya está corriendo.

Son cambios deliberados de presupuesto/espacio que quedan reflejados en los manifiestos y las rutas v2. No constituyen una prueba de que esos límites sean óptimos; sí eliminan los casos de complejidad extrema que hicieron inviable el presupuesto anterior.

Se creó un entorno temporal aislado en `/tmp/ptcg-baseline-audit-L0eB0q`, con Optuna 4.6.0 y scikit-learn 1.7.2. Se ejecutaron los módulos `test_b2_streaming.py`, `test_b3.py`, `test_b4.py` y `test_colab.py`: **23 pruebas pasaron en 42.48 segundos**. Son corpus sintéticos pequeños; no reproducen millones de filas, el sistema de archivos de Drive ni la sesión remota.

El script temporal `audit_resume.py` reprodujo la configuración duplicada y demostró que un trial antiguo RUNNING no bloquea automáticamente otro. Las pruebas existentes comprueban sobre todo reabrir estudios ya completados; no bastan para certificar la reanudación en mitad de un trial.

## Celda de diagnóstico de solo lectura para Colab

Ejecutar con el pipeline detenido. No modifica la base, los trials ni los checkpoints. Permite ver cuál trial se ejecutó, sus parámetros y los últimos heartbeats. No reconstruye la fase interna de un fit, porque el código actual no la registra.

```python
from pathlib import Path
import sqlite3
import pandas as pd
from optuna.distributions import json_to_distribution

db = Path('/content/drive/MyDrive/Applied-AI-Agent-Project/model_checkpoints/b3/efficient_v2/escenario_A/b3_optuna.sqlite3')
with sqlite3.connect(f'{db.as_uri()}?mode=ro', uri=True, timeout=5) as con:
    trials = pd.read_sql_query('''
        SELECT t.trial_id, t.number, t.state, t.datetime_start, t.datetime_complete
        FROM trials t JOIN studies s ON s.study_id = t.study_id
        WHERE s.study_name = ? ORDER BY t.number DESC LIMIT 6
    ''', con, params=['b3_A_B3_bosque_auc'])
    display(trials)
    for trial_id in trials.trial_id:
        params = con.execute('''
            SELECT param_name, param_value, distribution_json
            FROM trial_params WHERE trial_id = ?
        ''', (int(trial_id),)).fetchall()
        print('trial_id', trial_id, {
            name: json_to_distribution(dist).to_external_repr(value)
            for name, value, dist in params
        })
    display(pd.read_sql_query('''
        SELECT h.trial_id, h.heartbeat FROM trial_heartbeats h
        JOIN trials t ON t.trial_id = h.trial_id
        JOIN studies s ON s.study_id = t.study_id
        WHERE s.study_name = ? ORDER BY h.heartbeat DESC LIMIT 6
    ''', con, params=['b3_A_B3_bosque_auc']))
```

Para la próxima corrida de diagnóstico, un volcado periódico con `faulthandler.dump_traceback_later(300, repeat=True)` registrado antes de invocar el pipeline puede mostrar si la pila permanece en entrenamiento, evaluación o espera del heartbeat. Debe cancelarse con `faulthandler.cancel_dump_traceback_later()` al terminar. No ejecutar otra instancia del entrenamiento sobre los mismos checkpoints para intentar diagnosticarlo.
