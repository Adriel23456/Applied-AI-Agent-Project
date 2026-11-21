"""explicar_prediccion: por que el modelo da esa probabilidad, en lenguaje natural.

Usa SHAP sobre el modelo final (log-odds). Por construccion,
    valor base + suma de contribuciones = logit del modelo,
y el verificador lo comprueba en cada respuesta.

Para que un usuario no tecnico entienda cada contribucion se expresa tambien en puntos
porcentuales: cuanto bajaria (o subiria) la probabilidad si se quitara solo ese aporte.
"""

from ptcg_agente.entradas import resolver
from ptcg_agente.herramientas.comun import evaluar
from ptcg_agente.lenguaje import familia, frase, porcentaje
from ptcg_agente.modelo import sigmoide
from ptcg_wp.features import SENTINEL

NOMBRE = "explicar_prediccion"
DESCRIPCION = ("Explica la probabilidad con SHAP: las caracteristicas que mas la suben y la bajan, "
               "su aporte en puntos porcentuales y el resumen por familia (progreso, recursos y "
               "tablero, diferenciales).")


def ejecutar(modelo, observacion=None, archivo=None, paso=None, top=5):
    cur, origen = resolver(observacion, archivo, paso)
    salida, _ = evaluar(modelo, cur)
    if salida["probabilidad"] is None:
        return {"ok": True, "origen": origen, **salida, "contribuciones": [], "texto": None}
    top = max(1, min(int(top), 15))
    x = modelo.predictor.caracteristicas(cur)
    base, valores = modelo.shap(x)
    logit = modelo.logit(x)
    p = salida["probabilidad"]
    filas = []
    for nombre, valor, aporte in zip(modelo.features, x[0], valores):
        sin_activo = es_sin_activo(nombre, valor)
        filas.append({"caracteristica": nombre,
                      "descripcion": f"{frase(nombre)} (no hay Pokemon activo)" if sin_activo else frase(nombre),
                      "familia": familia(nombre), "valor": None if sin_activo else float(valor),
                      "shap": float(aporte),
                      "efecto_puntos": round(100 * (p - sigmoide(logit - float(aporte))), 1)})
    a_favor = sorted((f for f in filas if f["shap"] > 0), key=lambda f: -f["shap"])[:top]
    en_contra = sorted((f for f in filas if f["shap"] < 0), key=lambda f: f["shap"])[:top]
    por_familia = {}
    for f in filas:
        por_familia[f["familia"]] = por_familia.get(f["familia"], 0.0) + f["shap"]
    texto = _texto(p, a_favor, en_contra)
    return {"ok": True, "origen": origen, **salida,
            "valor_base_logit": base, "logit": logit, "suma_shap": float(sum(valores)),
            "a_favor": a_favor, "en_contra": en_contra,
            "por_familia_logit": {k: round(v, 4) for k, v in por_familia.items()},
            "texto": texto}


def es_sin_activo(nombre, valor):
    """El extractor pone -1 (centinela) en los campos del activo cuando no hay Pokemon activo.
    Ese -1 no es un dato del juego: se explica como 'no hay Pokemon activo' (caso L-10)."""
    return "active_" in nombre and not nombre.endswith("active_present") and float(valor) == SENTINEL


def _contribucion(f):
    valor = "" if f["valor"] is None else f" = {f['valor']:g}"
    return f"{f['descripcion']}{valor} ({f['efecto_puntos']:+.1f} puntos)"


def _texto(p, a_favor, en_contra):
    def lista(filas):
        return "; ".join(_contribucion(f) for f in filas) or "ninguna"
    return (f"Probabilidad de victoria: {porcentaje(p)}. "
            f"Lo que mas la sube: {lista(a_favor)}. Lo que mas la baja: {lista(en_contra)}.")