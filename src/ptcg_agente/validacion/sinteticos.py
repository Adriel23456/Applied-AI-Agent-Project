"""S-01 a S-05: estados reales de test de A modificados para quedar lejos del dominio de
entrenamiento. Se usan los primeros 20 estados de medio y final con Pokemon activo propio."""

from ptcg_agente.validacion.comun import activo, codigos, copia, propio, proporcion

GRUPO = "sinteticos"
N = 20


def pv_por_10(cur):
    a = activo(propio(cur))
    a["hp"] = 10 * a.get("hp", 0)
    a["maxHp"] = 10 * a.get("maxHp", 0)


def mano_150(cur):
    propio(cur)["handCount"] = 150


def turno_500(cur):
    cur["turn"] = 500


def energias_60(cur):
    a = activo(propio(cur))
    actuales = a.get("energies") or [None]
    a["energies"] = [actuales[0]] * 60


def todas(cur):
    for cambiar in (pv_por_10, mano_150, turno_500, energias_60):
        cambiar(cur)


CASOS = (("S-01", "PV del activo x10", pv_por_10), ("S-02", "150 cartas en la mano", mano_150),
         ("S-03", "turno 500", turno_500), ("S-04", "60 energias en el activo", energias_60),
         ("S-05", "las cuatro modificaciones juntas", todas))


def bases(datos):
    casos = datos.grupo("normal_A")
    elegidos = [c for c, e in zip(casos["caso"], casos["stage"])
                if e != "inicio" and activo(propio(datos.obs(c)))]
    return elegidos[:N]


def correr(bat, datos):
    elegidos = bases(datos)
    for caso, descripcion, cambiar in CASOS:
        def funcion(cambiar=cambiar, caso=caso):
            con, extremas, ps = 0, 0, []
            for c in elegidos:
                cur = copia(datos.obs(c))
                cambiar(cur)
                s = bat.llamar("estimar_probabilidad", observacion=cur)
                con += "fuera_de_dominio" in codigos(s)
                p = s.get("probabilidad")
                if p is not None:
                    ps.append(p)
                    extremas += p >= 0.9 or p <= 0.1
            texto = f"fuera_de_dominio {proporcion(con, len(elegidos))}"
            if caso == "S-05":
                texto += f"; probabilidades extremas (>= 90 % o <= 10 %) {proporcion(extremas, len(ps))}"
            return texto, con == len(elegidos)
        bat.caso(caso, GRUPO, f"{len(elegidos)} estados con {descripcion}", "fuera_de_dominio en todos", funcion)