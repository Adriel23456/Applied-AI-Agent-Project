# Declaración de Uso de Herramientas de IA

**Proyecto:** Estimación de la Probabilidad de Victoria a partir del Estado de Juego en el Pokémon Trading Card Game: un Estudio de Clasificación Tabular con Control Explícito de Fuga de Información

**Curso:** IC-6200 — Inteligencia Artificial, ITCR · II Semestre 2026 · Track A

**Equipo:** Adriel S. Chaves Salazar · Daniel Duarte Cordero · Sebastián Hernández Bonilla

**Cubre:** Etapa 1 — Estado del arte, análisis del problema y diseño

**Última actualización:** 2026-09-06

Esta declaración es obligatoria en cada entrega. Declarar el uso de IA no conlleva penalización; ocultarlo agrava cualquier hallazgo posterior. Las Etapas 2 y 3 adjuntarán sus propias secciones en lugar de sobrescribir esta, de modo que el registro se acumule a lo largo del semestre.

---

## 1. Herramientas utilizadas

| Herramienta | Propósito en este proyecto |
| --- | --- |
| **Claude (Anthropic)** | Exploración y delimitación del tema; estructuración de la pregunta de investigación, hipótesis y objetivos; redacción y revisión de la documentación; interpretación de los requisitos de la Etapa 1; estudio de artículos; asistencia con código y formato. |
| **Consensus** | Descubrimiento de literatura — localización de trabajos revisados por pares sobre predicción de victoria, calibración de clasificadores y fuga de datos; identificación de palabras clave y construcción de cadenas de búsqueda. |
| **ChatGPT** | Agrupación y clasificación de referencias; traducción de explicaciones complejas a un lenguaje accesible; diseño de plantillas de análisis sistemático; organización de ideas y adaptación del vocabulario a un tono profesional y técnico. |

Todas las herramientas se utilizaron como **asistentes de búsqueda y redacción**. Ninguna se utilizó para producir resultados, decidir la pregunta de investigación o seleccionar el conjunto final de referencias sin revisión humana. También se utilizaron motores de búsqueda regulares para el descubrimiento de literatura.

---

## 2. Dónde se usó la IA y qué se hizo manualmente después

### 2.1 Delimitación y encuadre del tema

**Qué hizo la herramienta.** Se usó Claude en una extensa conversación exploratoria para examinar posibles direcciones del proyecto antes de que el equipo se decidiera por esta. Esa conversación exploró inicialmente una dirección de aprendizaje por refuerzo (planificación de rutas de cobertura en terreno desconocido) que fue **abandonada**; el tema actual del Track A la reemplazó tras la reevaluación del propio equipo y la retroalimentación del profesor.
La herramienta contribuyó a: refinar la pregunta de investigación para que fuera falsable, distinguir los tres ejes de revisión requeridos por el curso, y poner a prueba si los diferenciadores propuestos frente a trabajos previos eran técnicamente defendibles o meramente retóricos.

**Verificado manualmente.** El equipo leyó directamente la retroalimentación del profesor y tomó la decisión del tema por su cuenta. Cada afirmación de encuadre que sobrevivió en la propuesta fue contrastada contra el enunciado del curso y con las fuentes primarias.

**No generado por IA.** La elección del tema, la elección del track, la pregunta de investigación tal como quedó formulada finalmente, y la decisión de abandonar la dirección de RL.

### 2.2 Descubrimiento de literatura

**Qué hicieron las herramientas.** Se usó Consensus para identificar palabras clave, construir cadenas de búsqueda y encontrar trabajos candidatos revisados por pares según el tema. Se usaron Claude y ChatGPT para evaluar si los artículos candidatos realmente respaldaban los tres ejes, para marcar qué candidatos eran *preprints* en lugar de publicaciones revisadas por pares, para identificar redundancias dentro del conjunto de candidatos y para proporcionar una clasificación inicial de las referencias.

**Verificado manualmente.** El DOI de cada referencia debe ser resuelto por un miembro del equipo y su contenido leído antes de que ingrese a `refs.bib`. Los archivos `.bib` de cada miembro llevan un comentario explícito de estado `VERIFIED` / `UNVERIFIED` en cada entrada; **una entrada que no esté marcada como VERIFICADA no aparece en el documento.** Hasta el momento de redactar este texto, 2 de 21 entradas están verificadas y 19 están pendientes. Las interpretaciones conceptuales generadas por IA se contrastaron constantemente con el contenido original de las fuentes.

**No generado por IA.** La selección final de los 21 artículos, la asignación de ejes, la distribución de lectura entre los miembros del equipo y la evaluación crítica de su relevancia fueron realizadas por el equipo.

**Explícitamente no delegado.** No se aceptó ningún DOI, lista de autores, lugar de publicación o rango de páginas basándose en la afirmación de una herramienta. Cuando los metadatos no pudieron confirmarse contra una fuente primaria, el campo se dejó como un marcador de posición en lugar de rellenarse con una suposición plausible.

### 2.3 Evaluación del conjunto de datos

**Qué hizo la herramienta.** Se usó Claude para discutir las implicaciones de la estructura del conjunto de datos (muchas instantáneas correlacionadas por episodio, deriva de distribución a lo largo de los días, coexistencia de versiones del motor) y para razonar sobre cuáles de estas constituyen amenazas a la validez.

**Verificado manualmente.** Todas las afirmaciones cuantitativas sobre el conjunto de datos provienen de los propios *scripts* de auditoría del equipo, no de ninguna herramienta. Cifras como el recuento de episodios, el recuento de instantáneas, la tasa de completitud de campos y la contaminación medida bajo una partición aleatoria son reproducibles desde `reports/audit_summary.md` y `reports/deep_probe.json` con una semilla fija.

**No generado por IA.** El *pipeline* de auditoría, su ejecución y cada número que produjo.

### 2.4 Documentación y estructura del artículo

**Qué hizo la herramienta.** Se usaron Claude y ChatGPT para redactar y revisar la documentación del proyecto: la propuesta del tema, los documentos de asignación de lectura, las convenciones del repositorio y la interpretación de cómo los requisitos de la Etapa 1 (tres ejes, tabla comparativa, identificación de brechas, línea base de la literatura, metodología) se mapean en las secciones de un artículo en formato IEEE. También se utilizó ChatGPT para diseñar una plantilla de análisis sistemático para los artículos, organizar ideas y adaptar el vocabulario a un tono profesional y técnico. Se solicitó constantemente a la IA corregir o ajustar puntos y argumentos para desarrollar adecuadamente el montaje del documento.

**Verificado manualmente.** Cada afirmación técnica en esos documentos fue verificada contra el enunciado del curso o contra una fuente primaria. Los pasajes que no pudieron fundamentarse fueron eliminados en lugar de ser suavizados. Las plantillas de análisis fueron completadas manualmente por los integrantes del equipo. Todos los ajustes de argumentos realizados por la IA se revisaron manualmente para asegurar que reflejaran correctamente las posturas del equipo.

**No generado por IA.** La formalización del problema, la idea general básica y estructura de cómo debía redactarse todo el documento, el diccionario de características, la lista negra de fugas, el protocolo experimental, la escalera de líneas base y cada resultado que se reportará.

---

## 3. Límites establecidos por el equipo

Estas reglas se mantienen independientemente de qué herramienta utilice cualquier miembro.

* **Ninguna referencia entra en la bibliografía por recomendación ciega de una herramienta.** Cada DOI se resuelve manualmente y la fuente se lee para confirmar que dice lo que le atribuimos.
* **No se delega ninguna decisión técnica.** La pregunta de investigación, la definición del objetivo, el diseño de la partición, la elección de métricas y la interpretación de los resultados son razonamiento propio del equipo. Una herramienta puede sugerir opciones; el equipo elige y defiende.
* **No se genera ningún resultado experimental.** Cada número reportado en el artículo proviene de código que escribimos y ejecutamos.
* **El código generado se ejecuta antes de ser consolidado.** No se fusiona nada asumiendo que funciona.
* **Los *preprints* se marcan como tales.** Cuando una herramienta sugirió un trabajo exclusivo de arXiv, este fue excluido de los 21 artículos revisados por pares o se consultó con el profesor antes de su inclusión.

---

## 4. Declaración por integrante

Cada miembro completa su propio bloque antes de la entrega.

### Adriel S. Chaves Salazar

* **Herramientas utilizadas:** Claude, herramientas de IA generativa y motores de búsqueda regulares.
* **Dónde y para qué:** Asistencia para el estudio y comprensión profunda de los artículos del Eje B; apoyo en la redacción de la versión individual del documento correspondiente al Eje B; y concatenación de grandes bloques de información comparativa. Revisión e iteración constante del montaje del documento, pidiendo explícitamente a la IA ajustar o arreglar puntos y argumentos con los que no estaba de acuerdo para desarrollar adecuadamente el texto.
* **Verificado manualmente después:** Revisión manual de todas las uniones de texto para garantizar la coherencia académica. Revisión manual de todos los ajustes realizados por la IA para asegurar que reflejaran correctamente mis puntos de vista y argumentos.
* **No generado por IA:** La búsqueda y hallazgo de los *papers* propuestos (se utilizaron estrictamente herramientas de búsqueda regulares para este propósito con el fin de aprovecharlas al máximo). La idea general básica y la estructura de cómo debía redactarse todo el documento. Las conclusiones críticas de la comparación, la selección final de los *papers* del Eje B y todas las decisiones finales.

### Daniel Duarte Cordero

* **Herramientas utilizadas:** Consensus y ChatGPT.
* **Dónde y para qué:** Identificación de palabras clave y construcción de cadenas de búsqueda en Consensus. Agrupación y clasificación inicial de referencias utilizando ChatGPT. Traducción de explicaciones complejas a un lenguaje accesible y aclaración de conceptos desconocidos. Diseño de una plantilla de análisis para identificar sistemáticamente los aspectos clave de cada artículo (problema, datos, metodología, métricas, resultados, limitaciones y contribución). Organización de ideas, mejora de la redacción y adaptación del vocabulario a un tono profesional y técnico.
* **Verificado manualmente después:** Contrastación de las interpretaciones de la IA con el contenido original de las fuentes. Lectura de los artículos y llenado manual de la plantilla de análisis. Revisión y validación de la selección final de fuentes, la evaluación de su relevancia y la redacción final.
* **No generado por IA:** La lectura crítica, la toma de decisiones final, la selección de fuentes, la interpretación de resultados y la evaluación de la relevancia de los *papers*.

### Sebastián Hernández Bonilla

* **Herramientas utilizadas:** Claude (Claude Code, Opus 5).
* **Dónde y para qué:** Organización y cribado de la literatura; recuperación de textos completos desde fuentes de los editores; extracción de figuras, tablas y limitaciones declaradas de los 7 trabajos revisados; resolución de metadatos bibliográficos contra Crossref; asistencia con formato y construcción del fichero BibTeX. Asistencia previa con los *scripts* de auditoría del corpus y lectura de sus salidas.
* **Verificado manualmente después:** Los 7 trabajos citados fueron recuperados y leídos a texto completo. Todo valor atribuido a una fuente fue transcrito manualmente. Todos los DOI se resolvieron contra Crossref o el registro del editor. La versión KDD'11 citada es la efectivamente leída. Está pendiente una relectura manual independiente de las fuentes antes de la entrega.
* **No generado por IA:** La pregunta de investigación, las hipótesis de trabajo, la elección del Track A, la decisión de agrupar por episodio, la lista negra de campos prohibidos, el diseño/ejecución de la auditoría y la interpretación de sus resultados. Ninguna magnitud de la auditoría es producto de un modelo de lenguaje.