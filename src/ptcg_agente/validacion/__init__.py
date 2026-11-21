"""Validacion del agente (rama 08AgentValidationAndSimulator).

Protocolo: docx/03Evidencia/08-11-26_ProtocoloValidacionAgente.md (escrito antes de ejecutar).

  casos.py        Seleccion de estados reales (test de A, B, C y errores) y extraccion de sus
                  observaciones desde las repeticiones publicas. Corre en Colab (cuaderno 09).
  comun.py        Bateria: llamadas medidas, filas de resultados y utilidades de los casos.
  normales.py     N-01 a N-06: escenarios normales.
  limite.py       L-01 a L-10: casos limite.
  entradas.py     E-01 a E-09: entradas inesperadas.
  poblaciones.py  D-01 y D-02: estados de B y de C.
  sinteticos.py   S-01 a S-05: estados alejados del dominio de entrenamiento.
  errores.py      M-01 y M-02: errores muy seguros del modelo.
  bateria.py      Corre todo el nivel N1 y devuelve resultados, detalle y latencias.
  resumen.py      Metricas del agente (seccion 5 del protocolo) del nivel N1.
  consultas.py    Nivel N2: el agente completo con Claude (cuaderno 10, en la PC).
"""