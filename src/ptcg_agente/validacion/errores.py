"""M-01 y M-02: errores muy seguros del modelo del agente en test de A (p >= 0.9 con derrota o
p <= 0.1 con victoria), por subpoblacion (A completa, B y C) y etapa.

M-01 (inicio): el agente debe avisar con extrema_temprana en el 100 %.
M-02 (medio y final): no hay criterio; se mide que fraccion llega al usuario con alguna
advertencia. Es la medida de fragilidad del agente.
"""

from ptcg_agente.validacion.comun import codigos, proporcion

GRUPO = "errores"


def correr(bat, datos):
    casos = datos.casos[datos.casos["grupo"].str.startswith("error_")].sort_values("caso")
    salidas = {}
    for _, f in casos.iterrows():
        s = bat.llamar("estimar_probabilidad", observacion=datos.obs(f["caso"]))
        salidas[f["caso"]] = s
        bat.anotar_estado(f["caso"], f, s, {"subpoblacion": f["grupo"][-1]})

    def m01():
        inicio = casos[casos["stage"] == "inicio"]
        con = sum("extrema_temprana" in codigos(salidas[c]) for c in inicio["caso"])
        por_sub = {g[-1]: int((inicio["grupo"] == g).sum()) for g in sorted(inicio["grupo"].unique())}
        if inicio.empty:
            return "no hay errores muy seguros de inicio en los casos", None
        return f"con extrema_temprana {proporcion(con, len(inicio))}; casos por subpoblacion {por_sub}", con == len(inicio)

    def m02():
        resto = casos[casos["stage"] != "inicio"]
        partes = []
        for etapa in ("medio", "final"):
            sub = resto[resto["stage"] == etapa]["caso"]
            alguna = sum(bool(codigos(salidas[c])) for c in sub)
            partes.append(f"{etapa}: con alguna advertencia {proporcion(alguna, len(sub))}")
        return "; ".join(partes), None

    bat.caso("M-01", GRUPO, "errores muy seguros de inicio (A, B y C)", "extrema_temprana en el 100 %", m01)
    bat.caso("M-02", GRUPO, "errores muy seguros de medio y final (A, B y C)",
             "solo registro: fraccion con alguna advertencia (prediccion: la mayoria sin advertencia)", m02)