"""N-01 a N-06: escenarios normales (estados de test de A en las tres etapas)."""

import json

from ptcg_agente.entradas import observacion_de_paso
from ptcg_agente.validacion.comun import codigos, proporcion, verificada

GRUPO = "normales"


def correr(bat, datos):
    casos = datos.grupo("normal_A")
    modelo = bat.modelo
    estimaciones, explicaciones = {}, {}

    def n01():
        dif_pred, dif_tabla, ok = 0.0, 0.0, 0
        for _, f in casos.iterrows():
            cur = datos.obs(f["caso"])
            s = bat.llamar("estimar_probabilidad", observacion=cur)
            estimaciones[f["caso"]] = s
            bat.anotar_estado(f["caso"], f, s)
            dif_pred = max(dif_pred, abs(s["probabilidad"] - modelo.predictor.probabilidad(cur)))
            dif_tabla = max(dif_tabla, abs(s["probabilidad"] - f["p"]))
            ok += verificada(s)
        return (f"dif. maxima con PredictorVictoria {dif_pred:.2e}; con la tabla {dif_tabla:.2e}; "
                f"verificados {proporcion(ok, len(casos))}"), dif_pred <= 1e-9 and ok == len(casos)

    def n02():
        malos = 0
        for _, f in casos.iterrows():
            e = bat.llamar("explicar_prediccion", observacion=datos.obs(f["caso"]))
            explicaciones[f["caso"]] = e
            malos += abs(e["valor_base_logit"] + e["suma_shap"] - e["logit"]) > 1e-3
        return f"SHAP que no suma: {malos}/{len(casos)}", malos == 0

    def n03():
        inicio = casos[casos["stage"] == "inicio"]["caso"]
        con = sum("etapa_inicio" in codigos(estimaciones[c]) for c in inicio)
        return f"con etapa_inicio: {proporcion(con, len(inicio))}", con == len(inicio)

    def n04():
        resto = casos[casos["stage"] != "inicio"]["caso"]
        malos = sum(bool({"etapa_inicio", "sin_prediccion"} & set(codigos(estimaciones[c]))) for c in resto)
        return f"con etapa_inicio o sin_prediccion: {proporcion(malos, len(resto))}", malos == 0

    def n05():
        fuera = sum("fuera_de_dominio" in codigos(s) for s in estimaciones.values())
        return f"fuera_de_dominio: {proporcion(fuera, len(estimaciones))}", fuera <= 0.05 * len(estimaciones)

    def n06():
        dif, ok = 0.0, 0
        partidas = sorted(set(casos.loc[casos["completa"], "game_id"]))
        for g in partidas:
            ruta = datos.repeticiones[g]
            s = bat.llamar("evaluar_partida", archivo=str(ruta))
            rep = json.loads(ruta.read_text(encoding="utf-8"))
            for punto in s["curva"]:
                cur = observacion_de_paso(rep, punto["paso"])
                p = modelo.predictor.probabilidad(cur)
                dif = max(dif, abs(punto["p_jugador0"] - (p if cur["yourIndex"] == 0 else 1 - p)))
            ok += verificada(s)
        n = len(partidas)
        return f"{n} repeticiones; dif. maxima {dif:.2e}; verificadas {proporcion(ok, n)}", dif <= 1e-4 and ok == n

    bat.caso("N-01", GRUPO, "90 estados de test de A con estimar_probabilidad",
             "probabilidad igual a PredictorVictoria (<= 1e-9) y 90/90 verificados", n01)
    bat.caso("N-02", GRUPO, "los mismos estados con explicar_prediccion",
             "valor base + suma SHAP = logit (<= 1e-3)", n02)
    bat.caso("N-03", GRUPO, "estados de inicio", "100 % con etapa_inicio", n03)
    bat.caso("N-04", GRUPO, "estados de medio y final", "ninguno con etapa_inicio ni sin_prediccion", n04)
    bat.caso("N-05", GRUPO, "los 90 estados", "fuera_de_dominio en <= 5 %", n05)
    bat.caso("N-06", GRUPO, "repeticiones completas de test de A con evaluar_partida",
             "curva igual al predictor (<= 1e-4) y todas verificadas", n06)