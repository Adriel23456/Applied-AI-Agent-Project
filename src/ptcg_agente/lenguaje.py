"""Nombres en espanol de las 62 caracteristicas, para explicar al usuario sin jerga.

Las familias son las mismas del articulo: progreso, recursos y tablero, y diferenciales.
"""

PROGRESO = {
    "game_turn": "numero de turno",
    "turn_action_count": "acciones hechas en este turno",
    "energy_attached": "ya unio una energia este turno",
    "retreated": "ya se retiro este turno",
    "supporter_played": "ya jugo un partidario este turno",
    "stadium_played": "ya jugo un estadio este turno",
    "stadium_in_play": "hay un estadio en juego",
    "first_player_is_me": "empezo la partida",
}

BASE = {
    "deck": "cartas en el mazo",
    "hand": "cartas en la mano",
    "discard": "cartas en el descarte",
    "prizes": "premios por tomar",
    "bench_n": "Pokemon en la banca",
    "active_present": "tiene Pokemon activo",
    "active_card": "carta del Pokemon activo",
    "active_hp": "PV del Pokemon activo",
    "active_max_hp": "PV maximos del Pokemon activo",
    "active_hp_ratio": "fraccion de PV que le queda al activo",
    "active_energies": "energias del Pokemon activo",
    "active_tools": "herramientas del Pokemon activo",
    "active_evolved": "el activo es una evolucion",
    "active_new": "el activo entro este turno",
    "bench_hp": "PV en la banca",
    "bench_energies": "energias en la banca",
    "total_hp": "PV totales en juego",
    "total_energies": "energias totales en juego",
    "total_tools": "herramientas totales en juego",
    "damaged": "Pokemon con dano",
    "asleep": "activo dormido",
    "burned": "activo quemado",
    "confused": "activo confundido",
    "paralyzed": "activo paralizado",
    "poisoned": "activo envenenado",
}


def familia(nombre):
    if nombre.startswith("diff_"):
        return "diferenciales"
    if nombre in PROGRESO:
        return "progreso"
    return "recursos y tablero"


def frase(nombre):
    """Descripcion corta. 'jugador' es siempre el jugador que actua (cuya probabilidad se da)."""
    if nombre in PROGRESO:
        return PROGRESO[nombre]
    if nombre.startswith("own_"):
        return f"{BASE.get(nombre[4:], nombre[4:])} del jugador"
    if nombre.startswith("opp_"):
        return f"{BASE.get(nombre[4:], nombre[4:])} del rival"
    if nombre.startswith("diff_"):
        return f"diferencia de {BASE.get(nombre[5:], nombre[5:])} (jugador menos rival)"
    return nombre


def porcentaje(p):
    """0.6234 -> '62.3 %'. Un solo formato para que el verificador pueda comparar cifras."""
    return f"{100 * p:.1f} %"