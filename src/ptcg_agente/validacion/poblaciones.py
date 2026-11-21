"""D-01 y D-02: estados de B (dias 15 y 22 de julio) y de C (arquetipos reservados).

Todos son de partidas de test de A, asi que el modelo nunca las vio. El caso aprueba si todas
las salidas quedan verificadas; las tasas de advertencias y el acierto se reportan.
Prediccion escrita en el protocolo: la tasa de fuera_de_dominio de C no sera mayor que la de A.
"""

from ptcg_agente.validacion.comun import codigos, proporcion, verificada

GRUPO = "poblaciones"


def tasas(bat, datos, grupo, anotar=True):
    casos = datos.grupo(grupo)
    ok = fuera = cartas = alguna = aciertos = 0
    for _, f in casos.iterrows():
        s = bat.llamar("estimar_probabilidad", observacion=datos.obs(f["caso"]))
        if anotar:
            bat.anotar_estado(f["caso"], f, s)
        ok += verificada(s)
        fuera += "fuera_de_dominio" in codigos(s)
        cartas += any("nunca vista" in a["mensaje"] for a in s.get("advertencias", []))
        alguna += bool(codigos(s))
        aciertos += (s["probabilidad"] >= 0.5) == bool(f["y"])
    n = len(casos)
    return {"n": n, "verificados": ok, "fuera": fuera / n, "carta_no_vista": cartas / n,
            "alguna": alguna / n, "acierto": aciertos / n}


def correr(bat, datos):
    referencia = {}

    def medir(grupo, nombre):
        def funcion():
            t = tasas(bat, datos, grupo)
            referencia[nombre] = t
            texto = (f"verificados {proporcion(t['verificados'], t['n'])}; fuera_de_dominio {t['fuera']:.1%}; "
                     f"carta no vista {t['carta_no_vista']:.1%}; alguna advertencia {t['alguna']:.1%}; "
                     f"acierto (umbral 0.5) {t['acierto']:.1%}")
            if nombre == "C" and "A" in referencia:
                cumple = t["fuera"] <= referencia["A"]["fuera"]
                texto += f"; prediccion 'C no mayor que A' ({referencia['A']['fuera']:.1%}): {'se cumple' if cumple else 'NO se cumple'}"
            return texto, t["verificados"] == t["n"]
        return funcion

    # Referencia de A con los mismos indicadores (no es un caso del protocolo; solo se anota)
    referencia["A"] = tasas(bat, datos, "normal_A", anotar=False)
    bat.caso("D-01", GRUPO, "90 estados de B (partidas de test de A)", "90/90 verificados; tasas: registro",
             medir("poblacion_B", "B"))
    bat.caso("D-02", GRUPO, "90 estados de C (partidas de test de A)", "90/90 verificados; tasas: registro",
             medir("poblacion_C", "C"))
    return referencia