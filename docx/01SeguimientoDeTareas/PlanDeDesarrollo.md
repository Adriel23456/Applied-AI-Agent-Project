# Plan de Desarrollo

Notas de trabajo del equipo. No forma parte de la entrega.

Proyecto de IA Aplicada - Estimación de la probabilidad de victoria en el Pokémon TCG (Track A)
Inteligencia Artificial (IC-6200) - Instituto Tecnológico de Costa Rica

## Estado actual

| Etapa | Rama principal | Peso | Estado |
|---|---|---|---|
| Etapa 1 - Estado del arte y diseño | `stage1` | 30 % | Completa |
| Etapa 2 - Modelado y evaluación | `Stage2` | 45 % | En curso |
| Etapa 3 - Agente y artículo final | `stage3` | 25 % | No iniciada |

---

## Etapa 1 - Completa

### `00TrackConfirmation`

- [x] Track A y tema aprobados por el profesor
- [x] Repositorio operativo (licencia, `.gitignore`, `requirements.txt`, reglas de Git)
- [x] Compilación del artículo en IEEEtran
- [x] Corpus localizado y auditado (10 días, 52 085 partidas, 7 038 378 observaciones)
- [x] Formalización del problema y protocolo experimental

### `01LiteratureReview`

- [x] 21+ artículos revisados en los tres ejes
- [x] Tabla comparativa y apartado de brechas
- [x] Baseline de literatura declarado (AUC 0.78 a 0.80, AAIA'17 Hearthstone)
- [x] Pregunta de investigación, hipótesis H1 a H3 y objetivos
- [x] Prevención de fuga documentada

### `02PaperAndDelivery`

- [x] Artículo preliminar completo
- [x] Declaración de uso de IA
- [x] Entrega en TecDigital

### Pendientes heredados del artículo

- [ ] Poner la URL real del dataset en `ptcg_dataset_2026`

---

## Etapa 2 - En curso

### `03DataCollectionAndEnvironmentSetup`

- [ ] Entorno en Colab reproducible (Drive, clon del repo, dependencias fijadas, semillas)
- [ ] Credencial de Kaggle fuera del repositorio
- [ ] Ingesta de los días auditados día por día hacia Parquet
- [ ] Extractor de características: una fila por estado del jugador que actúa, perspectiva propio/oponente
- [ ] Filtro de campos excluidos por fuga
- [ ] Tratamiento de ausencia estructural (indicador + centinela, sin imputar)
- [ ] Exclusión de empates y marcado de partidas anómalas
- [ ] EDA de la tabla: prevalencia por fila, ausencias, rangos imposibles, diccionario de datos final
- [ ] Cortes de etapa de la partida calculados solo con entrenamiento
- [ ] Particiones de los escenarios A, B y C, agrupadas por partida
- [ ] Auditoría de cobertura de cartas en entrenamiento
- [ ] Pruebas automáticas de los invariantes de fuga

### `04MainAIModelTrainingAndDevelopment`

- [ ] Preprocesamiento dentro de un pipeline ajustado solo con entrenamiento
- [ ] Registro de cada ejecución (configuración, semilla, métricas, commit)
- [ ] B0 - probabilidad a priori
- [ ] B1 - heurística de dominio
- [ ] B2 - regresión logística regularizada
- [ ] Demostración de inflación: B2 con partición por fila contra agrupada
- [ ] B3 - árbol de decisión y bosque aleatorio
- [ ] B4 - potenciación del gradiente por histogramas
- [ ] Búsqueda sistemática de hiperparámetros con validación cruzada agrupada, espacio y costo justificados
- [ ] Ablaciones por familia de características y prueba de H2
- [ ] Modelo final exportado y consumible desde fuera de Colab

### `05FinalModelChecks`

- [ ] Evaluación única sobre prueba en los escenarios A, B y C
- [ ] Métricas globales y por etapa, con intervalos por remuestreo de partidas
- [ ] Comparación contra B0, B2 y el baseline de literatura
- [ ] Curvas de aprendizaje y diagnóstico de sobreajuste
- [ ] Análisis de errores y casos límite
- [ ] SHAP sobre el modelo final, con hallazgos accionables
- [ ] Calibración: diagramas de fiabilidad, Brier y regresión isotónica (módulo de grupo de 3)
- [ ] Veredicto sobre H1, H2 y H3
- [ ] Confirmar con el profesor si las secciones de metodología y resultados del artículo se exigen en esta etapa
- [ ] Cuaderno completo, README de reproducción y declaración de uso de IA
- [ ] Entrega en TecDigital

---

## Etapa 3 - No iniciada

Se detalla al cerrar la Etapa 2.

- [ ] Agente que consume el modelo como evaluador de posiciones de forma verificable
- [ ] Ética del despliegue
- [ ] Artículo final con los resultados de la Etapa 2
- [ ] Demostración funcional