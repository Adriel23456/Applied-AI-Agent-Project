"""L-01 a L-10: casos limite.

Los estados se arman a partir de un estado real de medio o final de test de A (el primero, en
orden de caso, que tenga Pokemon activo propio y banca). En L-04 a L-07 la direccion del cambio
se registra pero no decide si el caso aprueba (seccion 3.2 del protocolo).
"""

import re
import time

from ptcg_agente.validacion.comun import (activo, banca, codigos, copia, direccion, propio, rival,
                                          texto_p, verificada)

GRUPO = "limite"
CENTINELA_EN_TEXTO = re.compile(r"= -1\b")


def estado_base(datos):
    for _, f in datos.grupo("normal_A").iterrows():
        cur = datos.obs(f["caso"])
        if f["stage"] != "inicio" and activo(propio(cur)) and banca(propio(cur)):
            return f["caso"], cur
    raise RuntimeError("no hay un estado de medio o final con activo y banca propios")


def correr(bat, datos):
    nombre, base = estado_base(datos)
    p_base = bat.llamar("estimar_probabilidad", observacion=base)["probabilidad"]

    def sin_prediccion(cur):
        s = bat.llamar("estimar_probabilidad", observacion=cur)
        return (f"p={texto_p(s.get('probabilidad'))}, advertencias={codigos(s)}",
                s.get("ok") and s["probabilidad"] is None and "sin_prediccion" in codigos(s))

    def cambio(modificar):
        cur = copia(base)
        modificar(cur)
        s = bat.llamar("estimar_probabilidad", observacion=cur)
        p = s.get("probabilidad")
        return (f"{texto_p(p_base)} -> {texto_p(p)} ({direccion(p_base, p)}); advertencias={codigos(s)}",
                verificada(s) and p is not None)

    def l02(cur):
        propio(cur)["prize"] = []
        return cur

    def l03(cur):
        propio(cur)["active"], propio(cur)["bench"] = [], []
        return cur

    def l08():
        inicio = datos.grupo("normal_A", "inicio")
        reales = [c for c in inicio["caso"] if datos.obs(c)["turn"] == 1]
        if reales:
            cur, origen = datos.obs(reales[0]), f"estado real {reales[0]}"
        else:
            cur, origen = copia(base), "estado base con turno 1"
            cur["turn"] = 1
        s = bat.llamar("estimar_probabilidad", observacion=cur)
        return f"{origen}: advertencias={codigos(s)}", "etapa_inicio" in codigos(s)

    def l09():
        inicio = time.perf_counter()
        s = bat.llamar("evaluar_partida", archivo=str(datos.repeticiones[datos.larga]))
        segundos = time.perf_counter() - inicio
        return (f"partida {datos.larga}: {len(s.get('curva', []))} pasos con prediccion en {segundos:.1f} s; "
                f"advertencias={sorted(set(codigos(s)))}"), verificada(s) and segundos < 30

    def l10():
        cur = copia(base)
        propio(cur)["active"] = []
        e = bat.llamar("explicar_prediccion", observacion=cur, top=15)
        centinelas = [f["descripcion"] for f in e.get("a_favor", []) + e.get("en_contra", [])
                      if f["valor"] == -1 and "activo" in f["descripcion"]]
        en_texto = bool(CENTINELA_EN_TEXTO.search(e.get("texto") or ""))
        return (f"contribuciones con valor -1: {centinelas}; texto con '= -1': {en_texto}",
                not centinelas and not en_texto)

    def mazo_propio(cur):
        propio(cur)["deckCount"] = 0

    def mazo_rival(cur):
        rival(cur)["deckCount"] = 0

    def un_premio(cur):
        propio(cur)["prize"] = [None]

    def sin_banca(cur):
        propio(cur)["bench"] = []

    bat.caso("L-01", GRUPO, "preparacion: observacion real de turno 0", "None y sin_prediccion",
             lambda: sin_prediccion(datos.obs("preparacion")))
    bat.caso("L-02", GRUPO, f"{nombre} con 0 premios por tomar del jugador", "None y sin_prediccion",
             lambda: sin_prediccion(l02(copia(base))))
    bat.caso("L-03", GRUPO, f"{nombre} sin Pokemon en juego del jugador", "None y sin_prediccion",
             lambda: sin_prediccion(l03(copia(base))))
    bat.caso("L-04", GRUPO, f"{nombre} con la banca propia vacia", "probabilidad valida (direccion: registro)",
             lambda: cambio(sin_banca))
    bat.caso("L-05", GRUPO, f"{nombre} con el mazo propio en 0", "probabilidad valida (direccion: registro)",
             lambda: cambio(mazo_propio))
    bat.caso("L-06", GRUPO, f"{nombre} con el mazo del rival en 0", "probabilidad valida (direccion: registro)",
             lambda: cambio(mazo_rival))
    bat.caso("L-07", GRUPO, f"{nombre} con un premio por tomar del jugador",
             "probabilidad valida (direccion: registro)", lambda: cambio(un_premio))
    bat.caso("L-08", GRUPO, "turno 1", "etapa_inicio", l08)
    bat.caso("L-09", GRUPO, "partida mas larga de test de A con evaluar_partida", "verificada y < 30 s", l09)
    bat.caso("L-10", GRUPO, f"{nombre} sin activo propio, con banca, en explicar_prediccion",
             "la explicacion no muestra -1 como PV o energias", l10)