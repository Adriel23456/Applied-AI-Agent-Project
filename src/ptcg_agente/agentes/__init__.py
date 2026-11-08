"""Roles de la arquitectura multiagente (un archivo por agente).

  planificador.py  Claude aislado y sin herramientas: pregunta -> plan JSON validado por Python.
  ejecutor.py      Python: corre el plan sobre el modelo final con las herramientas.
  verificador.py   Deterministico: revisa cada resultado de herramienta y cada respuesta final.
  redactor.py      Claude aislado y sin herramientas: resultados aprobados -> texto para el usuario.
  llm.py           Llamada a Claude Code sin interfaz (claude -p) con la membresia del equipo.

ptcg_agente/orquestador.py los encadena. Desde Claude Code tambien existen como subagentes
(.claude/agents/) y desde Claude Desktop un solo Claude cumple planificador y redactor sobre el
servidor MCP, que hace de ejecutor y verificador.
"""