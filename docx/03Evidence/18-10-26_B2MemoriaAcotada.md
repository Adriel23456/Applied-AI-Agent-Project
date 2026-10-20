# B2 con todos los estados de entrenamiento y lectura por lotes

Fecha: 18 de octubre de 2026. Rama: `04MainAIModelTrainingAndDevelopment`.

## Motivo y alcance

El límite de 5,000 partidas se introdujo para evitar los fallos de RAM de Colab,
pero `_collect_rows` todavía concatenaba las matrices de fit y evaluación.
Se sustituye ese flujo por lectura por lotes y regresión logística incremental.
Esta implementación actualiza la elección del optimizador registrada el 12 de
octubre; conserva las características, los escenarios, la cuadrícula de C y los
cinco pliegues agrupados por partida.

El cambio se aplica al entrenamiento y evaluación de B2. B0/B1 conservan su
iterador diario y su evaluación existente; el cálculo compartido de los cortes
de etapa ahora usa frecuencias de turnos, sin concatenar los turnos de train.

## Procedimiento

1. Contar estados útiles por partida, incluyendo partidas que crucen lotes o
   archivos. Asignar los pliegues usando solamente partidas con estados útiles.
2. Ajustar `StandardScaler.partial_fit` con las partidas de fit y pesos `1/n`.
   Fijar el escalador antes de entrenar el clasificador.
3. Escribir lotes escalados en archivos temporales locales. Se reutilizan para
   todas las épocas y valores de C de ese pliegue; se eliminan al salir de él.
4. Entrenar `SGDClassifier(loss="log_loss", penalty="l2")` con pasadas completas
   por fit, mezclando el orden de los lotes y las filas dentro de cada lote.
5. Evaluar por lotes. Acumular log loss y Brier ponderados; calcular AUC exacto
   mediante ordenamiento en SQLite sobre disco, contando correctamente empates.
   No promediar AUC calculados por lote. Para cada etapa se recalcula el peso
   con el conteo completo de esa partida dentro de esa etapa.

La RAM incluye los lotes, estadísticas por partida, parámetros del modelo y
buffers del grupo Parquet activo. No se almacena la matriz completa de estados. Hay
un intercambio explícito: más lecturas y espacio de disco local. Se comprueba
espacio disponible antes de preparar la caché y antes de evaluar. Una
interrupción normal limpia los temporales; una terminación abrupta del proceso
puede dejar las carpetas temporales hasta que se reinicie el runtime.

La medición sintética detectó que un único iterador Arrow sobre todos los grupos
del archivo retenía buffers de grupos ya recorridos. Por eso se crea un iterador
por grupo y se libera su memoria al terminarlo. El tamaño del grupo Parquet
también influye en el pico: reducir el lote no reduce necesariamente todos los
buffers de decodificación. La prueba automática verifica que los buffers vivos
no crezcan hasta contener todos los grupos de un archivo.

## Regularización y convergencia

Sean N los estados de fit, G sus partidas y `w_i=1/n_game`. El objetivo es:

`sum(w_i * log_loss_i) / G + ||coef||² / (2*C*G)`.

SGD recibe pesos `w_i*N/G`, de promedio 1, y `alpha=1/(C*G)`.
Así se conserva el objetivo ponderado anterior, incluido el intercepto sin
penalizar. `alpha=1/C` no sería la conversión correcta.

La solución numérica puede diferir de LBFGS si SGD no converge. Se mide el
objetivo y la norma máxima del gradiente sobre todo fit después de cada época;
se conserva el modelo con menor objetivo de fit. Ni val ni el pliegue retenido
se utilizan para elegir la época. `convergencia` exige un gradiente menor o
igual a la tolerancia; no basta con que la pérdida deje de cambiar.

Se promedian coeficientes e intercepto al terminar épocas completas. Se usa
`average=False` en SGD: en el código de sklearn 1.6.1, la ruta binaria de
`_fit_binary` con `average=True` deja de actualizar `_standard_intercept` cuando
ya publica el promedio. Las pruebas de equivalencia detectaron el efecto al
encadenar `partial_fit`; el promedio explícito entre épocas evita esa ruta.

Configuración inicial del cuaderno:

- Lotes de 32,768 filas; semilla 2026; máximo de 20 épocas.
- `learning_rate="invscaling"`, `power_t=0.25`.
- `eta0=min(0.05, 0.05/alpha)` para moderar los pasos con regularización fuerte.
- Tolerancia del gradiente `1e-3`. Es un criterio numérico de entrenamiento,
  no un umbral para comparar métricas entre candidatas.

Veinte épocas es un presupuesto inicial, no una garantía de convergencia. El
resumen avisa si algún ajuste no converge y marca la selección como provisional.
Hay que revisar esos ajustes antes de sacar conclusiones finales. Los CSV
incluyen cobertura, estados y partidas de fit, épocas, gradiente, objetivo,
alpha, tasa inicial efectiva, semilla y versión de scikit-learn.

## Ejecución en Colab

Abrir la versión actualizada de `notebooks/02_baselines.ipynb`, preferiblemente
en un runtime nuevo. Actualizar `/content/repo` no reemplaza las celdas de un
cuaderno que ya estaba abierto.

Ejecutar setup y las dos celdas de B2; no es necesario ejecutar B0/B1 primero.
La configuración debe mostrar `train: TODAS las partidas`. El piloto forma
los pliegues con todo train de A, pero solo ejecuta un pliegue con C=1: usa
aproximadamente 80% de las partidas para fit y 20% para evaluación. `full`
ejecuta los cinco pliegues en A/B/C y reajusta finalistas con todo train.

`fraccion_train=1.0` confirma cobertura del experimento. Durante CV,
`n_partidas_fit` excluye correctamente las partidas del pliegue retenido.

El CSV de progreso se actualiza de forma atómica después de completar cada
pliegue y todos sus valores de `C`. Un manifiesto valida escenario,
características, partidas, cuadrícula, semilla, parámetros y versión de
scikit-learn antes de reanudar. Al repetir la ejecución, B2 omite los pliegues
completos y vuelve a ejecutar desde el inicio el pliegue que estaba activo.
Los finalistas de `val` se guardan individualmente, así que se saltan los que ya
terminaron. Una configuración diferente debe usar otra carpeta de salida para
no mezclar resultados.

El cuaderno monta Drive y guarda checkpoints bajo
`MyDrive/Applied-AI-Agent-Project/b2_sgd/pilot` o `.../full`, para que sobrevivan
si Colab reemplaza el runtime. También se reanudan las finalistas de `val` que
ya se hubieran completado. La caché de entrenamiento y SQLite siguen en el
disco local temporal. Las finalistas se guardan como archivos joblib con
pipeline, orden de características, cortes de etapa y metadatos; son candidatas,
no una selección final automática ni modelos calibrados.

La demo por filas queda fuera del flujo principal y limitada a una muestra
pequeña con un máximo de 100,000 estados. Usa LBFGS y requiere un protocolo
pareado propio para comparar fuga; no se compara directamente con el B2 completo.
Calibración y test siguen reservados.

## Verificación

Las pruebas sintéticas verifican cobertura, cuantiles exactos de turnos,
pesos y escalado entre lotes/archivos, equivalencia de las tres métricas con
scikit-learn, ausencia de influencia de partidas retenidas sobre el ajuste,
proximidad al objetivo de LBFGS con distintas regularizaciones, limpieza de
temporales y exportación de candidatas. No sustituyen un piloto con el corpus
real y los recursos asignados a Colab.

Medición local adicional: corpus sintético de 2,000,000 de estados con 62
características, grupos Parquet y lotes de 8,192 filas, un pliegue y una época.
El pico del proceso fue 279.3 MiB; fit procesó 1,280,000 estados y evaluación
320,000 (el resto pertenecía a val). La cobertura de train fue 100% entre ambos
lados del pliegue. La medición incluye preparación, entrenamiento y métricas,
pero excluye la generación de datos. Es una prueba de memoria, no de calidad
predictiva ni una estimación garantizada para el corpus real. Se midió con
Python 3.12, scikit-learn 1.6.1, Arrow 26.0.0, pandas 3.0.6 y un hilo BLAS.

Referencias técnicas:

- [SGDClassifier 1.6.1](https://scikit-learn.org/1.6/modules/generated/sklearn.linear_model.SGDClassifier.html).
- [Objetivo de regresión logística](https://scikit-learn.org/1.6/modules/linear_model.html#logistic-regression).
- [StandardScaler 1.6.1](https://scikit-learn.org/1.6/modules/generated/sklearn.preprocessing.StandardScaler.html).
- [Lectura de Parquet por lotes](https://arrow.apache.org/docs/python/generated/pyarrow.parquet.ParquetFile.html).
