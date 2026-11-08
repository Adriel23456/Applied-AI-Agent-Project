"""Verificador: comprueba la coherencia de cada resultado y de cada respuesta antes de entregarla.

Es deterministico (no usa un LLM), asi que sus decisiones son reproducibles y probables.

verificar_salida(nombre, salida)  revisa lo que devuelve una herramienta:
  - probabilidades dentro de [0, 1], y None solo cuando el modelo no aplica;
  - en las explicaciones, valor base + suma de SHAP = logit, y sigmoide(logit) = probabilidad;
  - advertencias obligatorias presentes (inicio, fuera de dominio, sin prediccion).

verificar_texto(texto, salidas)   revisa la respuesta redactada para el usuario:
  - toda cifra del texto sale de alguna herramienta (redondeo permitido);
  - si hubo advertencias, el texto las menciona;
  - si el modelo no aplica, el texto no da una probabilidad;
  - el texto no promete certeza.
"""

import math
import re

TOL_SHAP = 1e-3
TOL_PROB = 1e-4
PALABRAS_CAUTELA = ("confianza", "advertencia", "incierto", "incertidumbre", "fuera del dominio",
                    "nunca vio", "no vio", "poco frecuente", "no aplica", "cautela", "orientaci",
                    "precauci", "no es confiable", "puede fallar", "puede equivocarse")
PALABRAS_SIN_PREDICCION = ("no hay probabilidad", "no aplica", "no se puede", "no puede estimar",
                           "no da una probabilidad", "sin probabilidad")
PROMESAS = ("garantiza", "con certeza", "seguro que gana", "seguro que pierde", "sin duda")
# Una promesa negada ("no garantiza", "ni es seguro que gana") es justamente un limite bien dicho
NEGACION = re.compile(r"\b(no|ni|nunca|jamas|tampoco)\b[^.;:]{0,25}$")
# Signo opcional: guion, menos tipografico o raya, que los LLM usan indistintamente
NUMERO = re.compile(r"(?<![\w.])([-\u2212\u2013]?\d+(?:[.,]\d+)?)\s*(%|por ciento)?")
# En las salidas de herramientas los numeros pueden venir pegados a texto (partida_87406956.json)
NUMERO_EN_SALIDA = re.compile(r"-?\d+(?:[.,]\d+)?")


def _probabilidades(salida):
    """Pares (contexto, probabilidad, estado) presentes en una salida."""
    if "estados" in salida:
        return [(f["etiqueta"], f["probabilidad"], f["estado"]) for f in salida["estados"]]
    if "curva" in salida:
        return [(f"paso {c['paso']}", c["p_jugador0"], "modelo") for c in salida["curva"]]
    if "probabilidad" in salida:
        return [("estado", salida["probabilidad"], salida.get("estado"))]
    return []


def _advertencias_esperadas(s):
    esperadas = set()
    if s.get("estado") in ("preparacion", "decidido"):
        esperadas.add("sin_prediccion")
    if s.get("etapa") == "inicio":
        esperadas.add("etapa_inicio")
    if s.get("dentro_del_dominio") is False and s.get("estado") == "modelo":
        esperadas.add("fuera_de_dominio")
    return esperadas


def verificar_salida(nombre, salida):
    problemas = []
    if not salida.get("ok", False):
        return {"aprobado": True, "problemas": [], "nota": "la herramienta informo un error de entrada"}
    for contexto, p, estado in _probabilidades(salida):
        if p is None:
            if estado == "modelo":
                problemas.append(f"{contexto}: probabilidad ausente en un estado con prediccion")
        elif not (isinstance(p, (int, float)) and math.isfinite(p) and 0.0 <= p <= 1.0):
            problemas.append(f"{contexto}: probabilidad fuera de [0, 1] ({p})")
        elif estado in ("preparacion", "decidido"):
            problemas.append(f"{contexto}: hay probabilidad en un estado sin prediccion ({estado})")
    if "suma_shap" in salida and salida.get("probabilidad") is not None:
        reconstruido = salida["valor_base_logit"] + salida["suma_shap"]
        if abs(reconstruido - salida["logit"]) > TOL_SHAP:
            problemas.append(f"SHAP no suma el logit: {reconstruido:.5f} frente a {salida['logit']:.5f}")
        if abs(1 / (1 + math.exp(-salida["logit"])) - salida["probabilidad"]) > TOL_PROB:
            problemas.append("el logit no corresponde a la probabilidad informada")
    grupos = salida["estados"] if "estados" in salida else [salida]
    for g in grupos:
        presentes = {a["codigo"] for a in g.get("advertencias", [])}
        faltan = _advertencias_esperadas(g) - presentes
        if faltan:
            problemas.append(f"faltan advertencias obligatorias: {sorted(faltan)}")
    return {"aprobado": not problemas, "problemas": problemas}


def _numeros(valor, salida=None):
    """Todos los numeros de una salida (recursivo), con su version en porcentaje si aplica."""
    salida = set() if salida is None else salida
    if isinstance(valor, bool):
        return salida
    if isinstance(valor, (int, float)) and math.isfinite(valor):
        salida.add(float(valor))
        if -1.0 <= valor <= 1.0:
            salida.add(round(100 * float(valor), 6))
    elif isinstance(valor, str):
        for m in NUMERO_EN_SALIDA.finditer(valor):
            salida.add(float(m.group(0).replace(",", ".")))
    elif isinstance(valor, dict):
        for v in valor.values():
            _numeros(v, salida)
    elif isinstance(valor, (list, tuple)):
        for v in valor:
            _numeros(v, salida)
    return salida


def _coincide(numero, decimales, permitidos):
    """El signo no se exige: "cae 16.6 puntos" y "-16.6 puntos" citan el mismo cambio."""
    tolerancia = 0.5 * 10 ** (-decimales) + 1e-9
    return any(abs(abs(numero) - abs(a)) <= tolerancia for a in permitidos)


def _promesas(texto_bajo):
    """Promesas de certeza que no estan negadas."""
    encontradas = []
    for p in PROMESAS:
        for m in re.finditer(re.escape(p), texto_bajo):
            if not NEGACION.search(texto_bajo[:m.start()]):
                encontradas.append(p)
                break
    return encontradas


def verificar_texto(texto, salidas):
    """'salidas' son los resultados de herramientas en los que se basa la respuesta."""
    problemas = []
    permitidos = set()
    for s in salidas:
        _numeros(s, permitidos)
    revisadas = 0
    for m in NUMERO.finditer(texto):
        bruto, es_porcentaje = m.group(1).lstrip("-\u2212\u2013"), bool(m.group(2))
        numero = float(bruto.replace(",", "."))
        decimales = len(bruto.split(".")[-1].split(",")[-1]) if ("." in bruto or "," in bruto) else 0
        if not es_porcentaje and decimales == 0 and 0 <= numero <= 10:
            continue  # conteos pequenos de lenguaje natural ("dos premios", "3 cartas")
        revisadas += 1
        if not _coincide(numero, decimales, permitidos):
            problemas.append(f"la cifra {m.group(0).strip()} no sale de ninguna herramienta")
    bajo = texto.lower()
    advertencias = [a for s in salidas for a in s.get("advertencias", [])]
    advertencias += [a for s in salidas for e in s.get("estados", []) for a in e.get("advertencias", [])]
    if advertencias and not any(p in bajo for p in PALABRAS_CAUTELA + PALABRAS_SIN_PREDICCION):
        problemas.append("hubo advertencias y el texto no las menciona")
    sin_prediccion = any(a["codigo"] == "sin_prediccion" for a in advertencias)
    con_prob = [s for s in salidas if s.get("probabilidad") is not None]
    if sin_prediccion and not con_prob:
        if not any(p in bajo for p in PALABRAS_SIN_PREDICCION):
            problemas.append("el modelo no aplica y el texto no lo dice")
        if re.search(r"\d\s*(%|por ciento)", texto):
            problemas.append("el modelo no aplica y el texto da un porcentaje")
    promesas = _promesas(bajo)
    if promesas:
        problemas.append(f"el texto promete certeza: {promesas}")
    return {"aprobado": not problemas, "problemas": problemas, "cifras_revisadas": revisadas}