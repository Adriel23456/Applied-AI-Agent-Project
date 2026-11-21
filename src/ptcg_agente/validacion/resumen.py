"""Metricas del agente de la seccion 5 del protocolo que se miden en N1."""

import pandas as pd

ADVERTENCIAS = ("N-03", "L-01", "L-02", "L-03", "L-08", "E-07", "E-08", "S-01", "S-02", "S-03", "S-04",
                "S-05", "M-01")
RECHAZOS = ("E-01", "E-02", "E-03", "E-04", "E-05", "E-06", "E-09")
META_MS = {"evaluar_partida": 30000}
META_MS_GENERAL = 2000


def _bloque(resultados, ids):
    sub = resultados[resultados["caso"].isin(ids)]
    return int(sub["aprobado"].eq(True).sum()), len(sub)


def metricas(resultados, latencias):
    filas = []
    for nombre, ids in (("Advertencias cuando corresponden", ADVERTENCIAS), ("Rechazos correctos", RECHAZOS)):
        ok, n = _bloque(resultados, ids)
        filas.append({"metrica": nombre, "valor": f"{ok}/{n} casos", "meta": "100 %", "cumple": ok == n})
    excepciones = int(resultados["excepcion"].sum())
    filas.append({"metrica": "Robustez", "valor": f"{excepciones} excepciones", "meta": "0",
                  "cumple": excepciones == 0})
    for herramienta, g in latencias.groupby("herramienta"):
        p50, p95 = g["ms"].quantile([0.5, 0.95])
        meta = META_MS.get(herramienta, META_MS_GENERAL)
        filas.append({"metrica": f"Latencia {herramienta} (n={len(g)})",
                      "valor": f"p50 {p50:.0f} ms, p95 {p95:.0f} ms", "meta": f"p95 < {meta} ms",
                      "cumple": p95 < meta})
    return pd.DataFrame(filas)


def por_grupo(resultados):
    tabla = resultados.assign(estado=resultados["aprobado"].map({True: "aprobado", False: "fallido"})
                              .fillna("registro"))
    return tabla.pivot_table(index="grupo", columns="estado", values="caso", aggfunc="count", fill_value=0)