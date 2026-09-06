# Declaración de Uso de Herramientas de IA

**Proyecto:** Estimación de Probabilidad de Victoria desde el Estado de Juego en Pokémon TCG
**Curso:** IC-6200 — Inteligencia Artificial, ITCR · II Semestre 2026 · Track A
**Equipo:** Adriel S. Chaves Salazar · Daniel Duarte Cordero · Sebastián Hernández Bonilla
**Cubre:** Etapa 1 — estado del arte, análisis del problema y diseño
**Última actualización:** 2026-09-05

Esta declaración es obligatoria en cada entrega. Declarar el uso de IA no conlleva penalización; ocultarlo agrava cualquier hallazgo posterior. Las Etapas 2 y 3 adjuntarán sus propias secciones en lugar de sobrescribir esta, de modo que el registro se acumule a lo largo del semestre.

---

## 1. Herramientas utilizadas

| Herramienta | Propósito en este proyecto |
|---|---|
| **Claude (Anthropic)** | Exploración y delimitación del tema; estructuración de la pregunta de investigación, hipótesis y objetivos; redacción y revisión de la documentación; interpretación de los requisitos de la Etapa 1; estudio de artículos; asistencia con código y formato. |
| **Consensus** | Descubrimiento de literatura — localización de trabajos revisados por pares sobre predicción de victorias, calibración de clasificadores y fuga de datos. |

Ambas herramientas se utilizaron como **asistentes de búsqueda y redacción**. Ninguna se utilizó para producir resultados, decidir la pregunta de investigación o seleccionar el conjunto final de referencias sin revisión humana.

---

## 2. Dónde se usó la IA y qué se hizo manualmente después

### 2.1 Delimitación y encuadre del tema

**Qué hizo la herramienta.** Se usó Claude en una extensa conversación exploratoria para examinar posibles direcciones del proyecto antes de que el equipo se decidiera por esta. Esa conversación exploró inicialmente una dirección de aprendizaje por refuerzo (planificación de rutas de cobertura en terreno desconocido) que fue **abandonada**; el tema actual del Track A la reemplazó tras la reevaluación del propio equipo y la retroalimentación del profesor.
La herramienta contribuyó a: refinar la pregunta de investigación para que fuera falsable, distinguir los tres ejes de revisión requeridos por el curso, y poner a prueba si los diferenciadores propuestos frente a trabajos previos eran técnicamente defendibles o meramente retóricos.

**Verificado manualmente.** El equipo leyó directamente la retroalimentación del profesor y tomó la decisión del tema por su cuenta. Cada afirmación de encuadre que sobrevivió en la propuesta fue contrastada con el enunciado del curso y con las fuentes primarias.

**No generado por IA.** La elección del tema, la elección del track, la pregunta de investigación tal como quedó formulada finalmente, y la decisión de abandonar la dirección de RL.

### 2.2 Descubrimiento de literatura

**Qué hicieron las herramientas.** Se usó Consensus para encontrar trabajos candidatos revisados por pares según el tema. Se usó Claude para evaluar si los artículos candidatos realmente respaldaban los tres ejes, para marcar qué candidatos eran *preprints* en lugar de publicaciones revisadas por pares, y para identificar redundancias dentro del conjunto de candidatos.

**Verificado manualmente.** El DOI de cada referencia debe ser resuelto por un miembro del equipo y su contenido leído antes de que ingrese a `refs.bib`. Los archivos `.bib` de cada miembro llevan un comentario explícito de estado `VERIFIED` / `UNVERIFIED` en cada entrada; **una entrada que no esté marcada como VERIFICADA no aparece en el documento.** Hasta el momento de redactar este texto, 2 de 21 entradas están verificadas y 19 están pendientes.

**No generado por IA.** La selección final de los 21 artículos, la asignación de ejes y la distribución de lectura entre los miembros del equipo fueron producidas por el equipo.

**Explícitamente no delegado.** No se aceptó ningún DOI, lista de autores, lugar de publicación o rango de páginas basándose en la afirmación de una herramienta. Cuando los metadatos no pudieron confirmarse contra una fuente primaria, el campo se dejó como un marcador de posición en lugar de rellenarse con una suposición plausible.

### 2.3 Evaluación del conjunto de datos

**Qué hizo la herramienta.** Se usó Claude para discutir las implicaciones de la estructura del conjunto de datos (muchas instantáneas correlacionadas por episodio, deriva de distribución a lo largo de los días, coexistencia de versiones del motor) y para razonar sobre cuáles de estas constituyen amenazas a la validez.

**Verificado manualmente.** Todas las afirmaciones cuantitativas sobre el conjunto de datos provienen de los propios *scripts* de auditoría del equipo, no de ninguna herramienta. Cifras como el recuento de episodios, el recuento de instantáneas, la tasa de completitud de campos y la contaminación medida bajo una partición aleatoria son reproducibles desde `reports/audit_summary.md` y `reports/deep_probe.json` con una semilla fija.

**No generado por IA.** El *pipeline* de auditoría, su ejecución y cada número que produjo.

### 2.4 Documentación y estructura del artículo

**Qué hizo la herramienta.** Se usó Claude para redactar y revisar la documentación del proyecto: la propuesta del tema, los documentos de asignación de lectura, las convenciones del repositorio y la interpretación de cómo los requisitos de la Etapa 1 (tres ejes, tabla comparativa, identificación de brechas, línea base de la literatura, metodología) se mapean en las secciones de un artículo en formato IEEE.

**Verificado manualmente.** Cada afirmación técnica en esos documentos fue verificada contra el enunciado del curso o contra una fuente primaria. Los pasajes que no pudieron fundamentarse fueron eliminados en lugar de ser suavizados.

**No generado por IA.** La formalización del problema, el diccionario de características, la lista negra de fugas, el protocolo experimental, la escalera de líneas base y cada resultado que se reportará.

---

## 3. Límites establecidos por el equipo

Estas reglas se mantienen independientemente de qué herramienta utilice cualquier miembro.

*   **Ninguna referencia entra en la bibliografía por recomendación ciega de una herramienta.** Cada DOI se resuelve manualmente y la fuente se lee para confirmar que dice lo que le atribuimos.
*   **No se delega ninguna decisión técnica.** La pregunta de investigación, la definición del objetivo, el diseño de la partición, la elección de métricas y la interpretación de los resultados son razonamiento propio del equipo. Una herramienta puede sugerir opciones; el equipo elige y defiende.
*   **No se genera ningún resultado experimental.** Cada número reportado en el artículo proviene de código que escribimos y ejecutamos.
*   **El código generado se ejecuta antes de ser consolidado.** No se fusiona nada asumiendo que funciona.
*   **Los *preprints* se marcan como tales.** Cuando una herramienta sugirió un trabajo exclusivo de arXiv, este fue excluido de los 21 artículos revisados por pares o se consultó con el profesor antes de su inclusión.

---

## 4. Declaración por integrante

Cada miembro completa su propio bloque antes de la entrega.

### Adriel S. Chaves Salazar
*   **Herramientas utilizadas:** Claude y herramientas de IA generativa.
*   **Dónde y para qué:** Búsqueda y descubrimiento de documentos académicos para el Eje B; asistencia para el estudio y comprensión profunda de estos artículos; apoyo en la redacción de la versión individual del documento correspondiente al Eje B; y concatenación de grandes bloques de información comparativa y estructuralmente similar.
*   **Verificado manualmente después:** [POR COMPLETAR: p. ej., revisión de que las uniones de texto tuvieran coherencia académica y validación de las interpretaciones generadas sobre los artículos del Eje B].
*   **No generado por IA:** [POR COMPLETAR: p. ej., las conclusiones críticas de la comparación y la selección final de qué papers incluir en el Eje B].

### Daniel Duarte Cordero
*   **Herramientas utilizadas:** [POR COMPLETAR]
*   **Dónde y para qué:** [POR COMPLETAR]
*   **Verificado manualmente después:** [POR COMPLETAR]
*   **No generado por IA:** [POR COMPLETAR]

### Sebastián Hernández Bonilla
*   **Herramientas utilizadas:** Claude (Claude Code, Opus 5).
*   **Dónde y para qué:** Organización y cribado de la literatura; recuperación de textos completos desde fuentes de los editores; extracción de figuras, tablas y limitaciones declaradas de los 7 trabajos revisados; resolución de metadatos bibliográficos contra Crossref; asistencia con formato y construcción del fichero BibTeX. Asistencia previa con los *scripts* de auditoría del corpus y lectura de sus salidas.
*   **Verificado manualmente después:** Los 7 trabajos citados fueron recuperados y leídos a texto completo. Todo valor atribuido a una fuente fue transcrito manualmente. Todos los DOI se resolvieron contra Crossref o el registro del editor. La versión KDD'11 citada es la efectivamente leída. Está pendiente una relectura manual independiente de las fuentes antes de la entrega.
*   **No generado por IA:** La pregunta de investigación, las hipótesis de trabajo, la elección del Track A, la decisión de agrupar por episodio, la lista negra de campos prohibidos, el diseño/ejecución de la auditoría y la interpretación de sus resultados. Ninguna magnitud de la auditoría es producto de un modelo de lenguaje.