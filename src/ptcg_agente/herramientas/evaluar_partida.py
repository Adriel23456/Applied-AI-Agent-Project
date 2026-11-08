"""evaluar_partida: curva de probabilidad de una repeticion completa, paso a paso y por turno.

En cada paso actua un jugador distinto, y el modelo da la probabilidad de quien actua. Para
dibujar una sola curva todo se pasa a la perspectiva del jugador 0:
    p_jugador0 = p si actua el jugador 0, y 1 - p si actua el jugador 1.

Puntos de giro: los cambios mas grandes entre estados consecutivos con prediccion, y los
momentos en que la curva cruza 50 %. Si la repeticion trae el resultado, se informa el
ganador real (es un analisis posterior a la partida, no una prediccion).
"""

import numpy as np

from ptcg_agente import dominio
from ptcg_agente.entradas import resolver_repeticion, validar_current, EntradaInvalida
from ptcg_agente.lenguaje import porcentaje
from ptcg_wp.features import acting_player, extract_features
from ptcg_wp.predictor import estado_de

NOMBRE = "evaluar_partida"
DESCRIPCION = ("Recorre una repeticion completa y devuelve la probabilidad de victoria del jugador 0 "
               "por paso y por turno, con los puntos de giro de la partida.")

UMBRAL_GIRO = 0.15
MAX_GIROS = 5


def ejecutar(modelo, repeticion=None, archivo=None):
    datos, origen = resolver_repeticion(repeticion, archivo)
    features = list(modelo.features)
    revisadas = features + list(dominio.CARTAS)
    puntos, filas, fuera, saltados = [], [], 0, 0
    for i, paso in enumerate(datos["steps"]):
        j = acting_player(paso)
        cur = (paso[j].get("observation") or {}).get("current") if j is not None else None
        if not cur:
            saltados += 1
            continue
        try:
            cur = validar_current(cur)
        except EntradaInvalida:
            saltados += 1
            continue
        if estado_de(cur) != "modelo":
            continue
        fila = extract_features(cur)
        hallazgos = dominio.revisar_fila(fila, modelo.perfil, revisadas)
        fuera += any(h["severidad"] == "fuera" for h in hallazgos)
        filas.append([fila[f] for f in features])
        puntos.append({"paso": i, "turno": cur["turn"], "actua": cur["yourIndex"],
                       "etapa": modelo.etapa(cur["turn"])})
    # Una sola llamada al modelo para toda la partida: llamarlo estado por estado es lento
    # (cada llamada tiene un costo fijo) y da exactamente las mismas probabilidades.
    curva = []
    if filas:
        p = modelo.predictor.model.predict_proba(np.asarray(filas, dtype=np.float32))[:, 1]
        for punto, pi in zip(puntos, p):
            p0 = float(pi) if punto["actua"] == 0 else 1 - float(pi)
            curva.append({**punto, "p_jugador0": round(p0, 4)})
    if not curva:
        raise EntradaInvalida("la repeticion no tiene ningun estado con prediccion")
    por_turno = {}
    for punto in curva:
        por_turno[punto["turno"]] = punto
    resumen_turnos = [{"turno": t, "p_jugador0": v["p_jugador0"], "etapa": v["etapa"]}
                      for t, v in sorted(por_turno.items())]
    giros = []
    for anterior, actual in zip(curva, curva[1:]):
        cambio = actual["p_jugador0"] - anterior["p_jugador0"]
        cruce = (anterior["p_jugador0"] - 0.5) * (actual["p_jugador0"] - 0.5) < 0
        if abs(cambio) >= UMBRAL_GIRO or cruce:
            giros.append({"paso": actual["paso"], "turno": actual["turno"],
                          "de": anterior["p_jugador0"], "a": actual["p_jugador0"],
                          "cambio": round(cambio, 4), "cruza_50": cruce})
    giros = sorted(giros, key=lambda g: -abs(g["cambio"]))[:MAX_GIROS]
    rewards = datos.get("rewards") or [None, None]
    ganador = None
    if None not in rewards[:2] and rewards[0] != rewards[1]:
        ganador = 0 if rewards[0] > rewards[1] else 1
    final = curva[-1]["p_jugador0"]
    advertencias = []
    if fuera:
        advertencias.append({"codigo": "fuera_de_dominio",
                             "mensaje": f"{fuera} de {len(curva)} estados tienen valores o cartas "
                                        "que el modelo nunca vio en entrenamiento."})
    return {"ok": True, "origen": origen, "perspectiva": "jugador 0",
            "n_pasos": len(datos["steps"]), "n_estados_con_prediccion": len(curva),
            "n_pasos_sin_observacion": saltados, "turnos": resumen_turnos,
            "puntos_de_giro": sorted(giros, key=lambda g: g["paso"]),
            "p_final_jugador0": final, "p_final_texto": porcentaje(final),
            "ganador_real": ganador, "curva": curva, "advertencias": advertencias}