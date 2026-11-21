"""describir_modelo: que modelo responde, que tan bien funciona y cuales son sus limites.

Las metricas son las de la evaluacion unica en test de la Etapa 2 (B4, por escenario y etapa).
Los limites son los declarados en el articulo; el agente debe citarlos cuando corresponda.
"""

NOMBRE = "describir_modelo"
DESCRIPCION = ("Ficha del modelo final: tipo, datos de entrenamiento, metricas en prueba por escenario "
               "y etapa, veredicto de las hipotesis y limites declarados.")

LIMITES = [
    "Estima la probabilidad de que gane el jugador que actua; no recomienda jugadas ni conoce las reglas.",
    "Solo usa informacion publica: nunca ve la mano del rival ni el contenido de los premios.",
    "No aplica en la preparacion (turno 0) ni en estados ya resueltos.",
    "Al inicio de la partida distingue poco entre posiciones ganadoras y perdedoras.",
    "Se entreno con partidas entre agentes automaticos de diez dias de 2026; no representa el juego entre personas.",
    "Con poblaciones nuevas (dias posteriores, arquetipos no vistos) pierde capacidad y se vuelve algo sobreconfiado.",
    "Las probabilidades no estan recalibradas para otros periodos.",
]

ESCENARIOS = {"A": "partidas nuevas", "B": "dias posteriores", "C": "arquetipos de mazo no vistos"}


def ejecutar(modelo):
    ficha = modelo.ficha
    metricas = {e: {"descripcion": ESCENARIOS[e], **v} for e, v in modelo.metricas_test.items()}
    return {"ok": True,
            "modelo": ficha.get("modelo"),
            "entrenado_con": f"train del escenario {ficha.get('escenario_de_entrenamiento')}",
            "perspectiva": ficha.get("perspectiva"),
            "n_caracteristicas": ficha.get("n_caracteristicas"),
            "version_sklearn": ficha.get("version_sklearn"),
            "modelo_sha256": modelo.modelo_sha256,
            "cortes_etapa": {"inicio_hasta_turno": modelo.cortes[0], "medio_hasta_turno": modelo.cortes[1]},
            "metricas_test_B4": metricas,
            "veredicto_hipotesis": modelo.veredicto,
            "limites": LIMITES}