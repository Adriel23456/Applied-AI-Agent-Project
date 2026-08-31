# Propuesta de tema — Track C (Aprendizaje por Refuerzo)

**Curso:** IC-6200 Inteligencia Artificial · II Semestre 2026
**Equipo:** Adriel S. Chaves Salazar · Daniel Duarte Cordero · Sebastián Hernández Bonilla

---

## 1. El tema en una frase

Un agente de aprendizaje por refuerzo que aprende a **recorrer y cubrir por completo un terreno desconocido**, decidiendo su ruta no solo por dónde hay obstáculos, sino por **qué tan costoso es atravesar cada zona** según el tipo de suelo y la pendiente.

**Título tentativo:**
> *Traversability-Aware Coverage Path Planning on Unknown Terrain: A 2.5D Reinforcement Learning Approach with Elevation and Soil-Class Cost Modeling*

---

## 2. El problema

**Coverage Path Planning (CPP)** es el problema de encontrar una ruta que pase por todo el espacio libre de un área. Aplica a robots de limpieza, agricultura de precisión, inspección, y exploración planetaria. Es NP-duro, y se vuelve más difícil cuando el entorno es desconocido y hay que planificar en línea mientras se descubre.

**El supuesto que casi toda la literatura hace:** el terreno es binario. Una celda está libre o tiene un obstáculo. Moverse a cualquier celda libre cuesta lo mismo.

**Ese supuesto es falso en terreno real.** Un robot no solo evita rocas: evita arena suelta donde se atasca, prefiere superficie firme, y gasta más energía subiendo que bajando. La misma distancia recorrida puede costar el triple según por dónde pase.

---

## 3. Las brechas detectadas

Las tres son concretas y verificables contra la literatura que ya revisamos.

**Brecha 1 — El terreno se modela como binario.**
Los entornos de RL para cobertura representan el mundo como libre/obstáculo. Los trabajos que sí consideran terreno irregular lo hacen con métodos clásicos de optimización, no con RL. Qiu et al. (*J. Intell. Robot. Syst.*, 2024) declaran explícitamente que el CPP sobre terrenos irregulares no está resuelto.

**Brecha 2 — El costo energético es independiente del terreno.**
El trabajo más cercano al nuestro, Wijegunawardana et al. (*IEEE Trans. Systems, Man, and Cybernetics: Systems*, 2025), incorpora conciencia de riesgo mediante RL, pero modela la energía como una penalización constante por cambio de dirección. Cruzar arena y cruzar roca cuestan lo mismo en su formulación.

**Brecha 3 — El mapa de peligros se asume conocido.**
En ese mismo trabajo, el mapa con la ubicación de los peligros se entrega al robot antes de empezar. No hay descubrimiento en línea del tipo de terreno. Esto elimina el problema de decidir bajo incertidumbre sobre qué hay más adelante.

**Lo que este proyecto cubre:** las tres, en su versión 2.5D — cuadrícula con capas de clase de suelo y elevación, descubiertas en línea.

**Lo que queda fuera:** validación en hardware físico, dinámica de contacto real (deslizamiento, vuelco), y transferencia sim-to-real. Se declara como limitación y trabajo futuro.

---

## 4. Pregunta de investigación

> **¿Una política Proximal Policy Optimization (PPO) que observa clase de terreno y elevación produce trayectorias de cobertura con menor costo energético total que la misma política entrenada sobre ocupación binaria y que los planificadores clásicos, y a qué costo en número de pasos y tasa de cobertura final?**

**Es refutable.** El agente consciente del terreno puede perder: puede rodear tanto que gaste más de lo que ahorra. Ese resultado negativo también responde la pregunta.

**Es medible.** Costo energético acumulado por episodio, sobre mapas no vistos durante el entrenamiento.

**Hipótesis de trabajo:** el agente consciente de traversabilidad reducirá el costo energético total en al menos 15% frente al agente ciego, a cambio de hasta 20% más pasos.

---

## 5. Formulación del MDP

El problema se modela como un proceso de decisión de Markov
$\mathcal{M} = \langle \mathcal{S}, \mathcal{A}, P, R, \gamma \rangle$.

### 5.1 Representación del terreno

Tres capas sobre la misma cuadrícula:

| Capa | Contenido |
|---|---|
| `C[i,j]` | Clase de suelo: `{bedrock, soil, sand, big_rock}` |
| `H[i,j]` | Elevación (valor continuo) |
| `V[i,j]` | Visitado / no visitado |

Las clases de suelo se derivan de la taxonomía de **AI4Mars** (NASA JPL, CVPR Workshop on AI for Space, 2021), diseñada específicamente para análisis de traversabilidad de rovers. Esto ancla los pesos de costo en una fuente operacional en vez de en una elección arbitraria.

### 5.2 Espacio de estados $\mathcal{S}$

Observación egocéntrica de cuatro canales:

1. Máscara de exploración (visitado / no visitado)
2. Clase de terreno **conocida** — valor `unknown` en celdas no visitadas
3. Elevación **conocida** — valor `unknown` en celdas no visitadas
4. Posición del agente

**Punto clave:** los canales 2 y 3 solo tienen información en celdas ya observadas. El entorno es **parcialmente observable**, y esa es la parte del problema que la literatura previa elimina al entregar el mapa completo.

### 5.3 Espacio de acciones $\mathcal{A}$

Discreto, cuatro acciones: `{Norte, Sur, Este, Oeste}`.

**Justificación:** mantenerlo discreto permite comparación directa contra los planificadores clásicos, que también operan sobre celdas adyacentes, y simplifica la estabilidad del entrenamiento. Se descarta el espacio continuo porque introduce complejidad de control que no aporta a la pregunta de investigación.

### 5.4 Dinámica de transición $P(s'|s,a)$

Determinista en la posición, con una excepción: en celdas de arena el movimiento falla con probabilidad $p_{\text{slip}}$ y el robot no avanza. Esto modela el atascamiento sin requerir física de contacto.

**Terminación del episodio:** cobertura ≥ 95%, límite de pasos alcanzado, o presupuesto energético agotado.

### 5.5 Función de recompensa

$$R(s,a,s') = \alpha \cdot n_{\text{nuevas}} - \beta \cdot c_{\text{energía}}(s,a) - \delta \cdot \mathbb{1}_{\text{atasco}} + \omega \cdot \mathbb{1}_{\text{cobertura} \geq \tau}$$

donde el costo energético combina suelo y pendiente:

$$c_{\text{energía}}(s,a) = w_{C[i,j]} \cdot \left(1 + \kappa \cdot \max(0, \Delta h)\right)$$

| Peso | Clase | Justificación |
|---|---|---|
| 1.0 | Bedrock | Superficie consolidada, tracción firme |
| 1.5 | Soil | Intermedio |
| 3.0 | Sand | Material suelto, riesgo de atascamiento |
| ∞ | Big rock | Intransitable |

**El término $\max(0, \Delta h)$ hace el costo asimétrico:** subir cuesta, bajar no. La literatura de navegación en terreno señala que los métodos convencionales de RL asumen costos simétricos y por eso producen trayectorias subóptimas.

**Alternativas descartadas:**
- *Recompensa pura de cobertura* → ignora la variable de interés del estudio.
- *Costo simétrico por pendiente* → no refleja el consumo real y elimina la mitad del fenómeno.
- *Penalización por giro únicamente* (como en el trabajo previo) → el terreno deja de importar.

### 5.6 Factor de descuento

$\gamma = 0.99$. La cobertura completa es un objetivo de horizonte largo; un $\gamma$ bajo produce comportamiento voraz, que es precisamente el baseline que se busca superar. La literatura de CPP con RL justifica este valor por la misma razón.

---

## 6. Estabilidad del entrenamiento

**Algoritmo: PPO**, con justificación de literatura y no de preferencia. Wijegunawardana et al. (2025) compararon PPO contra DQN, A2C y TRPO sobre este mismo tipo de problema con la misma función de recompensa: PPO obtuvo la mayor recompensa promedio con menos fluctuaciones y convergencia más estable.

**Punto de partida de hiperparámetros**, tomado de ese trabajo: learning rate 0.0005, $\lambda$ (GAE) 0.9, clip range 0.2, mini-batch 64.

**Prevención de fuga de datos** — específica de generación procedural:

| Conjunto | Semillas |
|---|---|
| Entrenamiento | 0 – 799 |
| Validación (hiperparámetros) | 800 – 899 |
| Prueba (se toca una sola vez) | 900 – 999 |

Además, los mapas de prueba usan configuraciones de dificultad no vistas: tamaños, densidades de obstáculos y proporciones de arena distintas. Esto mide generalización real, no memorización.

**Reporte:** toda métrica con media y desviación estándar sobre al menos 5 semillas de entrenamiento.

---

## 7. Objetivos

**Objetivo general**
Determinar si la incorporación de clase de terreno y elevación en la observación y en la función de recompensa de un agente de RL mejora la eficiencia energética de la planificación de cobertura sobre terreno desconocido.

**Objetivos específicos**
1. Formalizar el problema como un MDP 2.5D con costo de tránsito heterogéneo y asimétrico por pendiente.
2. Extender un entorno de cobertura existente de ocupación binaria a un modelo de terreno con clases y elevación.
3. Implementar tres baselines: política aleatoria, exploración basada en fronteras, y A\* ponderado por costo.
4. Entrenar y comparar dos políticas PPO —ciega al terreno y consciente del terreno— bajo un protocolo experimental con separación estricta de conjuntos.
5. Cuantificar el intercambio entre costo energético, número de pasos y tasa de cobertura, y evaluar generalización a configuraciones no vistas.

---

## 8. Entorno y viabilidad

**Entorno base:** MarsExplorer (Koutras et al., *Electronics*, 2021, 10(22), 2751), compatible con la API de Gymnasium, extendido con las capas de clase de suelo y elevación.

**Baseline de literatura:** el resultado publicado de PPO sobre la configuración binaria original del entorno. Se declara explícitamente que la configuración extendida no es directamente comparable, y se corren ambas.

**Cómputo:** el entorno es una cuadrícula sin física de contacto. Corre en Google Colab Pro en el orden de minutos a pocas horas por corrida.

**Riesgo principal:** la modificación del generador de terreno. Mitigación: si la extensión no está lista en el plazo previsto, el proyecto se ejecuta sobre la configuración binaria original más los baselines clásicos, lo cual sigue respondiendo una versión reducida de la pregunta.


## Veredicto de viabilidad

**Sí es viable, y está en el lado fácil del espectro de proyectos de RL.** Se lo justifico con las razones concretas:

**Lo que lo hace manejable:**
- No hay física de contacto. Es una cuadrícula — un paso del entorno son unas cuantas operaciones sobre matrices.
- Espacio de acciones discreto de 4 opciones. Lo más simple que existe.
- PPO viene implementado en Stable-Baselines3. No van a escribir el algoritmo.
- Los hiperparámetros de partida ya los tienen del paper de IEEE TSMC.
- Los baselines clásicos son cortos: frontier-based son ~80 líneas, A\* ponderado ~60.

**Lo que NO es su cuello de botella:** el cómputo. Este entorno es CPU-bound, no GPU-bound. Una corrida de 2M de pasos con 8 entornos en paralelo debería tomar entre 1 y 3 horas en Colab. Con 20 corridas totales (2 políticas × 5 semillas × 2 configuraciones) hablamos de unas 40 horas de cómputo repartidas en varias semanas. Cabe cómodo.

**Sus tres riesgos reales, en orden:**

| Riesgo | Por qué duele | Mitigación |
|---|---|---|
| **Ajuste de la recompensa** | Es donde se van las semanas en RL. El agente aprende algo degenerado y hay que iterar | Fije los pesos temprano, documente cada cambio, y **no busque el óptimo** — busque que funcione |
| **Colab se desconecta** | Pierde 3 horas de entrenamiento | Guardar checkpoints a Drive cada 100k pasos, desde el día uno |
| **Alcance del agente de Etapa 3** | Es fácil sobre-diseñarlo | Tres herramientas y ya. No construyan un producto |

**Lo único que le pediría que no haga:** no intente hacerlo "más completo" agregando multiagente, sensores realistas, o un segundo entorno. El proyecto está bien dimensionado como está.

---

## Los siguientes pasos

### Ahora — cerrar la Etapa 1 (esta semana)

**Paso 1 — Solicitud de aprobación** *(Adriel, hoy)*
Enviar el documento de propuesta al profesor. Archivar el envío y la respuesta en el repo.

**Paso 2 — Completar los 21 papers** *(los tres, 2 días)*
Cada quien cierra sus 7 en su eje. El Eje B y el C están cortos.

**Paso 3 — Tabla comparativa** *(Sebastián)*
Poblar las siete columnas. Verificar cada DOI en IEEE Xplore o ACM DL antes de meterlo al `.bib`.

**Paso 4 — Escribir el paper preliminar** *(los tres, 2 días)*
Introducción, trabajos relacionados con los tres ejes, metodología con el MDP formal. Las secciones ya están esqueletadas en LaTeX.

**Paso 5 — Prueba de humo del entorno** *(Adriel, en paralelo)*
Instalar MarsExplorer en Colab, correr un episodio aleatorio, abrir el generador de terreno. No para modificarlo todavía — solo para saber con qué se van a topar.

### Después — arrancar la Etapa 2

**Paso 6 — Extender el generador de terreno**
De booleano a tres capas: clase, elevación, visitado.

**Paso 7 — Wrapper de observación y recompensa**
Los cuatro canales y la función de costo energético.

**Paso 8 — Baselines clásicos**
Aleatorio, frontier-based, A\* ponderado.

**Paso 9 — Entrenar y comparar**
Dos políticas, cinco semillas cada una, dos configuraciones.

---

## División de tareas

La regla: **cada quien es dueño de un eje bibliográfico y de un bloque técnico.** Así la autoría por commits queda clara y nadie depende de otro para avanzar.

### Adriel — Entorno y formulación

| Etapa 1 | Etapa 2 |
|---|---|
| Eje B: RL, PPO, generalización, multi-objetivo | Extender el generador de terreno |
| Formalización del MDP (sección 5 del documento) | Wrapper de observación de 4 canales |
| Protocolo experimental y prevención de leakage | Función de recompensa y su calibración |
| Sección de metodología del paper | Entrenamiento y checkpointing |

**Por qué usted:** es el bloque más técnico y el que define si el proyecto avanza. También es lo que va a tener que defender oralmente frente al profesor.

### Daniel — Baselines y redacción

| Etapa 1 | Etapa 2 |
|---|---|
| Eje A: CPP, métodos clásicos, traversabilidad | Implementar política aleatoria |
| Baseline de literatura (el número objetivo) | Implementar frontier-based exploration |
| Introducción y abstract preliminar | Implementar A\* ponderado por costo |
| Verificación de DOIs | Scripts de evaluación comparativa |

**Por qué él:** ya tiene el Eje A casi completo, y los baselines clásicos son código autocontenido que no depende del entorno modificado. Puede trabajar en paralelo sin bloquearse.

### Sebastián — Terreno, evidencia y evaluación

| Etapa 1 | Etapa 2 |
|---|---|
| Eje C: MarsExplorer, AI4Mars, NOAH-H, dominio marciano | Definir la taxonomía de clases y los pesos de costo |
| Tabla comparativa (7 columnas) | Notebook de análisis y figuras |
| Sección de brechas | Cálculo de métricas y estadísticos |
| Sección de trabajos relacionados | Paquete de evidencia (cada figura trazable) |

**Por qué él:** el Eje C alimenta directamente el modelo de terreno. Quien lee los papers de AI4Mars y NOAH-H es quien mejor puede justificar por qué la arena cuesta 3.0 y no 2.0.

---

## Lo que se hace en conjunto

Tres cosas **no** se reparten:

1. **La declaración de uso de IA.** Un bloque por persona, cada quien el suyo.
2. **La decisión sobre los pesos de la recompensa.** Los tres tienen que poder defenderla.
3. **La lectura del paper de Wijegunawardana.** Es el trabajo más cercano al suyo; si el profesor lo menciona y solo uno lo leyó, se nota.

---

## Dos cosas prácticas para el día uno de la Etapa 2

**Checkpointing desde el primer entrenamiento.** No espere a perder una corrida:

```python
from stable_baselines3.common.callbacks import CheckpointCallback

checkpoint = CheckpointCallback(
    save_freq=100_000,
    save_path="/content/drive/MyDrive/runs/",
    name_prefix="ppo_terrain"
)
model.learn(total_timesteps=2_000_000, callback=checkpoint)
```

**Paralelizar entornos, no confiar en la GPU.** Este entorno es CPU-bound; ocho entornos en paralelo le van a dar más aceleración que cualquier GPU:

```python
from stable_baselines3.common.env_util import make_vec_env
env = make_vec_env("explorer-v1", n_envs=8)
```

---

Cuando tenga la respuesta del profesor sobre la aprobación del track, me avisa y ajustamos lo que haya que ajustar antes de arrancar la Etapa 2.