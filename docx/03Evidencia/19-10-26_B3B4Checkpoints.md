# Checkpoints y reanudación de B3/B4 en Colab

**Fecha:** 19 de octubre de 2026

**Rama:** `04MainAIModelTrainingAndDevelopment`

**Propósito:** registrar cómo conservar el progreso de Optuna y de las comparaciones finales de B3/B4 si Colab interrumpe el runtime.

## Almacenamiento

`notebooks/03_modelo_principal.ipynb` monta Google Drive y guarda las salidas bajo:

```text
MyDrive/Applied-AI-Agent-Project/model_checkpoints/
├── b3/<modo>/escenario_<A|B|C>/
└── b4/<modo>/escenario_<A|B|C>/
```

Cada carpeta de escenario contiene una base SQLite de Optuna, CSV de progreso y, al completar la evaluación de candidatas, los modelos serializados. Los archivos temporales de datos de B4 siguen en el disco local de Colab: se vuelven a materializar al iniciar otro runtime para no penalizar la lectura y escritura de memmaps en Drive.

## Punto de recuperación

- B3 y B4 persisten cada trial completo de Optuna. Los registros de métricas por pliegue quedan dentro del trial y se reflejan en el CSV de progreso. Si se reinicia Colab, la búsqueda reconstruye resultados desde la base y continúa hasta el total de trials configurado; los trials completados no se repiten.
- Si el runtime se corta a mitad de un trial, sus pliegues parciales no se consideran resultado completo. Ese trial se vuelve a ejecutar desde el principio al reanudar; no se guarda el estado interno del árbol, bosque o boosting a mitad de su ajuste.
- La evaluación final de `val` también guarda cada candidata al completarla: sus métricas y el artefacto del modelo. Las candidatas completas se omiten en la reanudación.
- Los manifiestos verifican escenario/datos, características y configuración relevante. Si la corrida no coincide, el código falla con un mensaje para restaurar los parámetros originales o elegir una carpeta nueva, evitando mezclar experimentos.

## Cómo reanudar

1. Abrir la versión actualizada del notebook y conectar/montar Drive.
2. Mantener el mismo `B3_MODE` o `B4_MODE`, semillas, pliegues y parámetros de la corrida interrumpida. Se puede aumentar el total de trials para extender una búsqueda; los ya completados cuentan hacia ese total.
3. Ejecutar setup, configuración y la celda de ejecución. El código carga los estudios existentes y continúa.

Para dejar el trabajo corriendo en una sola sesión se agregó `notebooks/04_entrenamiento_secuencial.ipynb`. Su orden es B2 (solo las finalistas anteriores, 600 épocas máximas) → B3 → B4. Cada etapa espera a que termine la anterior y conserva sus propios checkpoints. Si el runtime se interrumpe, se vuelve a ejecutar este cuaderno; las etapas completadas se reconocen desde Drive antes de continuar.

El orquestador guarda `model_checkpoints/pipeline_status.json` con una marca por modelo y escenario (B2/A–C, B3/A–C, B4/A–C). `complete` significa que terminaron CV y evaluación de finalistas; `running` al reiniciar identifica la fase que quedó interrumpida. Las fases completas se saltan enteras. La fase interrumpida continúa usando sus checkpoints de pliegues/trials/candidatas. Si se cambia la configuración, se invalida la marca de fase; los manifiestos internos protegen contra mezclar configuraciones incompatibles.

No se deben ejecutar simultáneamente dos runtimes contra la misma carpeta SQLite. Para una búsqueda nueva o una configuración distinta, usar una carpeta de salida nueva. El modo (`pilot`/`full`) ya crea carpetas separadas. Al reanudar B4 se reconstruyen sus memmaps locales antes de consultar el progreso persistido.

## Verificación y limitaciones

Las pruebas sintéticas de B3/B4 se ampliaron para comprobar que invocar otra vez la misma búsqueda no aumenta el número de trials y que la evaluación final no duplica candidatas ya guardadas. La compilación sintáctica del código y la lectura del notebook como JSON pasan localmente. En el entorno local de esta implementación no está instalado `optuna`, por lo que las pruebas dirigidas no se pudieron ejecutar allí; el notebook instala la versión fijada en `requirements.txt`.

Estos checkpoints cubren la búsqueda CV por trial y la evaluación final por candidata. No guardan progreso dentro de un trial, ni evitan reconstruir la matriz local de B4 después de un reinicio. La confiabilidad ante cortes requiere que Drive esté montado y que se conserve la misma carpeta de salida.
