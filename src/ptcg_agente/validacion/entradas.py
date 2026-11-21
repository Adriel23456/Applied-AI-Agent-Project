"""E-01 a E-09: entradas inesperadas. Todas deben terminar en ok=False con un mensaje claro
(o, en E-07 y E-08, con la advertencia fuera_de_dominio), nunca en una excepcion."""

import tempfile
from pathlib import Path

from ptcg_agente.validacion.comun import codigos, copia, propio, activo

GRUPO = "entradas"


def _rechazo(salida, *palabras):
    error = salida.get("error") or ""
    return (f"ok={salida.get('ok')}; error={error!r}",
            salida.get("ok") is False and all(p.lower() in error.lower() for p in palabras))


def _todos(resultados):
    textos = [t for t, _ in resultados]
    return " | ".join(textos), all(a for _, a in resultados)


def correr(bat, datos):
    base_caso = next(c for c in datos.grupo("normal_A", "medio")["caso"] if activo(propio(datos.obs(c))))
    base = datos.obs(base_caso)
    tmp = Path(tempfile.mkdtemp(prefix="ptcg-entradas-"))
    repeticion = str(next(iter(sorted(datos.repeticiones.values()))))

    def e01():
        ruta = tmp / "mal_formado.json"
        ruta.write_text('{"players": [', encoding="utf-8")
        return _rechazo(bat.llamar("estimar_probabilidad", archivo=str(ruta)), "no es un JSON valido")

    def e02():
        return _rechazo(bat.llamar("estimar_probabilidad", archivo=str(tmp / "no_existe.json")), "no existe")

    def e03():
        turno = copia(base)
        turno["turn"] = "3"
        mazo = copia(base)
        propio(mazo)["deckCount"] = -1
        jugadores = copia(base)
        jugadores["players"] = {"0": base["players"][0], "1": base["players"][1]}
        return _todos([_rechazo(bat.llamar("estimar_probabilidad", observacion=turno), "turn"),
                       _rechazo(bat.llamar("estimar_probabilidad", observacion=mazo), "deckCount"),
                       _rechazo(bat.llamar("estimar_probabilidad", observacion=jugadores), "players")])

    def e04():
        sin_indice = copia(base)
        del sin_indice["yourIndex"]
        sin_mano = copia(base)
        del sin_mano["players"][0]["handCount"]
        return _todos([_rechazo(bat.llamar("estimar_probabilidad", observacion=sin_indice), "yourIndex"),
                       _rechazo(bat.llamar("estimar_probabilidad", observacion=sin_mano), "handCount")])

    def e05():
        return _rechazo(bat.llamar("estimar_probabilidad", observacion={"current": None}), "jugador que espera")

    def e06():
        return _todos([_rechazo(bat.llamar("estimar_probabilidad", archivo=repeticion, paso=10 ** 6), "paso"),
                       _rechazo(bat.llamar("estimar_probabilidad", archivo=repeticion), "paso")])

    def fuera(cur):
        s = bat.llamar("estimar_probabilidad", observacion=cur)
        mensajes = " ".join(a["mensaje"] for a in s.get("advertencias", []))
        return s, mensajes

    def e07():
        cur = copia(base)
        activo(propio(cur))["id"] = 999999
        s, mensajes = fuera(cur)
        return (f"advertencias={codigos(s)}",
                "fuera_de_dominio" in codigos(s) and "nunca vista" in mensajes)

    def e08():
        resultados = []
        for etiqueta, cambiar in (("PV 9999", lambda c: activo(propio(c)).update(hp=9999)),
                                  ("9 premios", lambda c: propio(c).update(prize=[None] * 9)),
                                  ("200 cartas en mano", lambda c: propio(c).update(handCount=200))):
            cur = copia(base)
            cambiar(cur)
            s, _ = fuera(cur)
            resultados.append((f"{etiqueta}: {codigos(s)}", "fuera_de_dominio" in codigos(s)))
        return _todos(resultados)

    def e09():
        return _rechazo(bat.llamar("estimar_probabilidad", observacion=base, color="rojo"), "argumentos invalidos")

    bat.caso("E-01", GRUPO, "archivo con JSON mal formado", "ok=False: no es un JSON valido", e01)
    bat.caso("E-02", GRUPO, "archivo que no existe", "ok=False: no existe", e02)
    bat.caso("E-03", GRUPO, "turn como texto, deckCount negativo, players como objeto",
             "3/3 ok=False con el campo nombrado", e03)
    bat.caso("E-04", GRUPO, "sin yourIndex; jugador sin handCount", "2/2 ok=False con el campo nombrado", e04)
    bat.caso("E-05", GRUPO, "observacion del jugador que espera (current vacio)",
             "ok=False y menciona al jugador que espera", e05)
    bat.caso("E-06", GRUPO, "repeticion con paso fuera de rango y sin paso", "2/2 ok=False", e06)
    bat.caso("E-07", GRUPO, f"{base_caso} con carta activa 999999", "fuera_de_dominio con carta nunca vista", e07)
    bat.caso("E-08", GRUPO, f"{base_caso} con PV 9999, 9 premios y 200 cartas en mano",
             "fuera_de_dominio en 3/3", e08)
    bat.caso("E-09", GRUPO, "argumento que la herramienta no acepta", "ok=False sin excepcion", e09)