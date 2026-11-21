---
description: Consulta multiagente sobre una partida del Pokemon TCG (planificador, ejecutor, redactor y verificador como subagentes).
argument-hint: <ruta del archivo> [paso] [pregunta]
---
Responde esta consulta con los cuatro subagentes del proyecto, en este orden, sin saltarte ninguno:

Consulta: $ARGUMENTS

1. Delega al subagente planificador-ptcg la pregunta y la ruta del archivo. Recibe el plan JSON.
2. Delega al subagente ejecutor-ptcg ese plan. Recibe los resultados.
3. Delega al subagente redactor-ptcg la pregunta y SOLO los resultados utilizables.
4. Delega al subagente verificador-ptcg el borrador exacto.
5. Si no aprueba, vuelve al paso 3 con la lista de problemas (maximo 2 veces). Si sigue sin
   aprobar, responde solo con lo que dicen las herramientas y di que no pudiste verificar mas.

Al final muestra: la respuesta aprobada, el plan usado y el resultado de la verificacion.
No llames tu mismo a las herramientas del modelo: lo hacen los subagentes.