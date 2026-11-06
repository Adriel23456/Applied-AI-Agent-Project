"""Evaluacion final: test cerrado por defecto, intervalos, calibracion, reglas de hipotesis y curvas."""

from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
import pytest
from scipy.special import expit
from sklearn import __version__ as sklearn_version
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ptcg_wp import evaluacion_final as ef  # noqa: E402
from ptcg_wp.b4 import materialize_split  # noqa: E402
from ptcg_wp.data import ScenarioStream  # noqa: E402
from ptcg_wp.evaluation import metric_rows_codes  # noqa: E402
from ptcg_wp.experiments.h2 import vocabulario_ids  # noqa: E402


def _tabla(n_partidas=300, estados=9, senal=1.5, seed=0):
    """Partidas sinteticas: cada una con su desenlace, tres etapas y una probabilidad informativa."""
    rng = np.random.default_rng(seed)
    filas = []
    for partida in range(n_partidas):
        y = int(rng.integers(0, 2))
        for paso in range(estados):
            etapa = ef.STAGES[paso * 3 // estados]
            # La senal crece con la etapa, como afirma H1
            z = (2 * y - 1) * senal * (paso + 1) / estados + rng.normal()
            filas.append({"game_id": 1000 + partida, "step": paso, "turn": paso + 1, "stage": etapa, "y": y,
                          "day": "d1" if partida % 2 else "d2", "p_B4": expit(z),
                          "p_H2": expit(0.2 * z + rng.normal(0, 2)), "p_B0": 0.5})
    return pd.DataFrame(filas)


def _corpus(ruta, features, partidas=120):
    """Tablas minimas con las cuatro particiones."""
    rng = np.random.default_rng(3)
    filas, particiones = [], []
    for partida in range(partidas):
        particion = ("train", "train", "val", "calib", "test")[partida % 5]
        particiones.append({"game_id": partida, "split_A": particion})
        y = partida % 2
        for turno in range(1, 7):
            fila = {"game_id": partida, "turn": turno, "setup": 0, "decided": 0, "y": y}
            fila.update({f: float(rng.normal(y if f == features[0] else 0)) for f in features})
            filas.append(fila)
    pd.DataFrame(filas).to_parquet(ruta / "estados_1.parquet", index=False)
    pd.DataFrame(particiones).to_parquet(ruta / "particiones.parquet", index=False)


def test_calib_y_test_cerrados_salvo_evaluacion_final(tmp_path):
    _corpus(tmp_path, ["a", "b"])
    stream = ScenarioStream(tmp_path, "A", ("a", "b"))
    for particion in ("calib", "test"):
        with pytest.raises(ValueError, match="solo admite train y val"):
            next(stream.iter_batches(particion))
    final = ScenarioStream(tmp_path, "A", ("a", "b"), evaluacion_final=True)
    assert set(next(final.iter_batches("test"))["split"]) == {"test"}
    assert ef.cargar_particion(tmp_path, "A", "calib", ["a"])["game_id"].nunique() == 24


def test_intervalos_centrados_en_la_funcion_comun():
    tabla = _tabla()
    metricas, replicas = ef.evaluar_con_intervalos(tabla, ["B4", "H2"], {"escenario": "A"}, n_boot=200, seed=1)
    y, codigos = tabla["y"].to_numpy(), ef.codigos_partida(tabla["game_id"])
    esperado = metric_rows_codes(y, tabla["p_B4"], codigos, ef.codigos_etapa(tabla["stage"]), {})
    obtenido = metricas[metricas["modelo"].eq("B4")].reset_index(drop=True)
    for fila, referencia in zip(obtenido.to_dict("records"), esperado):
        assert fila["auc"] == pytest.approx(referencia["auc"])
        assert fila["auc_ic_inf"] < fila["auc"] < fila["auc_ic_sup"]
    # Con multiplicidad 1 el plan reproduce la metrica comun, incluida la de una etapa
    mascara = tabla["stage"].eq("inicio").to_numpy()
    plan = ef._PlanMetricas(y[mascara], tabla["p_B4"].to_numpy()[mascara], codigos[mascara], 300)
    medido = plan.medir(np.ones(300, dtype=np.int64))
    fila = metricas.query("modelo == 'B4' and etapa == 'inicio'").iloc[0]
    assert medido["auc"] == pytest.approx(fila["auc"]) and medido["brier"] == pytest.approx(fila["brier"])
    assert medido["log_loss"] == pytest.approx(fila["log_loss"])
    # Los remuestreos son reproducibles y no reparten una partida
    assert np.array_equal(next(ef.multiplicidades(5, 1, 7)), next(ef.multiplicidades(5, 1, 7)))
    assert len(replicas[("B4", "global", "auc")]) == 200


def test_comparacion_emparejada_y_criterio_b1():
    tabla = _tabla()
    metricas, replicas = ef.evaluar_con_intervalos(tabla, ["B4", "H2"], {}, n_boot=200, seed=1)
    comparacion = ef.comparar(metricas, replicas, "B4", ["H2"], {"escenario": "A"})
    fila = comparacion.query("etapa == 'global' and metrica == 'auc'").iloc[0]
    assert fila["delta"] == pytest.approx(fila["valor_principal"] - fila["valor_referencia"])
    assert fila["ic_inf"] <= fila["delta"] <= fila["ic_sup"]
    # Mismo modelo contra si mismo: diferencia exactamente cero en toda replica
    igual = ef.comparar(metricas, replicas, "B4", ["B4"], {})
    assert (igual["ic_inf"] == 0).all() and (igual["ic_sup"] == 0).all()
    # H2 decide con el intervalo de 'inicio'
    assert ef.decidir_h2(comparacion, "A")["resultado"] in ("sostenida", "refutada")
    assert ef.criterio_b1(metricas, "B4", "H2")["cumple"] is True
    assert ef.criterio_b1(metricas, "H2", "B4")["cumple"] is False


def test_auc_por_turno_y_primer_turno():
    tabla = _tabla()
    curva = ef.auc_por_turno(tabla, tope=7, n_boot=100)
    assert curva["turno"].max() == 7 and curva["auc"].iloc[-1] > curva["auc"].iloc[0]
    assert ef.primer_turno_banda(curva, 0.0) == 1 and ef.primer_turno_banda(curva, 1.1) is None


def test_calibrador_solo_usa_lo_que_recibe_y_corrige_sobreconfianza():
    rng = np.random.default_rng(0)
    verdad = rng.uniform(0.05, 0.95, 20000)
    y = (rng.uniform(size=len(verdad)) < verdad).astype(int)
    # Probabilidades sobreconfiadas: mismo orden, escala exagerada
    p = expit(3 * np.log(verdad / (1 - verdad)))
    codigos = np.arange(len(p)) // 4
    validacion = ef.validar_calibradores(p, y, codigos, n_pliegues=3)
    assert set(validacion["metodo"]) == set(ef.METODOS)
    assert ef.elegir_metodo(validacion) in ("isotonica", "platt")
    pesos = ef.pesos_partida(codigos)
    antes = ef.descomposicion_corp(y, p, codigos)
    for metodo in ("isotonica", "platt"):
        despues = ef.aplicar_calibrador(ef.ajustar_calibrador(metodo, p, y, pesos), p)
        assert np.all((despues >= 0) & (despues <= 1))
        assert ef.descomposicion_corp(y, despues, codigos)["brier_mcb"] < antes["brier_mcb"]
    identidad = ef.ajustar_calibrador("ninguna", p, y, pesos)
    assert np.array_equal(ef.aplicar_calibrador(identidad, p), p)
    with pytest.raises(ValueError):
        ef.ajustar_calibrador("otro", p, y, pesos)


def test_corp_suma_el_puntaje_y_coincide_con_la_metrica_comun():
    tabla = _tabla()
    y, p = tabla["y"].to_numpy(), tabla["p_B4"].to_numpy()
    codigos = ef.codigos_partida(tabla["game_id"])
    corp = ef.descomposicion_corp(y, p, codigos)
    comun = metric_rows_codes(y, p, codigos, None, {}, include_stages=False)[0]
    for s in ("log_loss", "brier"):
        assert corp[f"{s}_puntaje"] == pytest.approx(comun[s])
        assert corp[f"{s}_puntaje"] == pytest.approx(corp[f"{s}_mcb"] - corp[f"{s}_dsc"] + corp[f"{s}_unc"])
        assert corp[f"{s}_mcb"] >= -1e-12 and corp[f"{s}_dsc"] >= -1e-12


def test_fiabilidad_y_ece():
    rng = np.random.default_rng(0)
    p = rng.uniform(size=50000)
    y = (rng.uniform(size=len(p)) < p).astype(int)
    codigos = np.arange(len(p)) // 5
    bien = ef.tabla_fiabilidad(y, p, codigos)
    assert len(bien) == 10 and bien["peso"].sum() == pytest.approx(1.0)
    assert bien["peso"].between(0.09, 0.11).all() and ef.ece(bien) < 0.02
    assert ef.ece(ef.tabla_fiabilidad(y, np.clip(p + 0.2, 0, 1), codigos)) > 0.1


def test_h1_detecta_senal_y_controla_la_duracion():
    assert ef.prueba_h1(_tabla(), "A", n_boot=200)["resultado"] == "sostenida"
    # Sin senal en ninguna etapa: debilitada
    sin_senal = _tabla()
    sin_senal["p_B4"] = np.random.default_rng(1).uniform(0.4, 0.6, len(sin_senal))
    assert ef.prueba_h1(sin_senal, "A", n_boot=200)["resultado"] == "debilitada"
    # La cohorte excluye las partidas que no llegan a las tres etapas
    tabla = _tabla()
    corta = tabla["game_id"].eq(1000) & tabla["stage"].ne("inicio")
    assert ef.prueba_h1(tabla.loc[~corta], "A", n_boot=100)["partidas_cohorte"] == 299


def _test_ab(p_b_transformada):
    tabla = _tabla(400, seed=2)
    a = tabla.copy()
    b = tabla.copy()
    b["p_B4"] = p_b_transformada(tabla["p_B4"].to_numpy())
    # A trae partidas de otros dias que B no tiene; solo cuentan las comunes
    extra = tabla.loc[tabla["game_id"] < 1050].assign(game_id=lambda d: d["game_id"] + 90000)
    return pd.concat([a, extra], ignore_index=True), b


def test_h3_sostenida_si_solo_se_rompe_la_calibracion():
    # Mismo orden exacto (AUC identico) con probabilidades sesgadas: pierde calibracion, no orden
    a, b = _test_ab(lambda p: expit(np.log(p / (1 - p)) + 1.5))
    filas, decision = ef.prueba_h3(a, b, n_boot=200)
    medidas = filas.set_index("medida")
    assert decision["resultado"] == "sostenida" and decision["partidas_comunes"] == 400
    assert medidas.loc["delta_auc", "valor"] == pytest.approx(0, abs=1e-12)
    assert medidas.loc["delta_dsc_brier", "valor"] == pytest.approx(0, abs=1e-12)
    assert medidas.loc["delta_mcb_brier", "ic_inf"] > 0


def test_h3_refutada_si_solo_se_pierde_el_ordenamiento():
    # B mezcla ruido en las predicciones y queda bien calibrado por construccion: pierde orden
    rng = np.random.default_rng(5)
    a, b = _test_ab(lambda p: p)
    z = np.log(b["p_B4"] / (1 - b["p_B4"])).to_numpy() + rng.normal(0, 1.5, len(b))
    x = z.reshape(-1, 1)
    b["p_B4"] = LogisticRegression().fit(x, b["y"]).predict_proba(x)[:, 1]
    filas, decision = ef.prueba_h3(a, b, n_boot=200)
    assert decision["resultado"] == "refutada"
    assert filas.set_index("medida").loc["delta_auc", "valor"] < 0


def test_h3_exige_filas_comunes():
    a, b = _test_ab(lambda p: p)
    with pytest.raises(ValueError, match="no comparten"):
        ef.alinear_h3(a.assign(game_id=a["game_id"] + 10**7), b)
    with pytest.raises(ValueError, match="no coinciden"):
        ef.alinear_h3(a, b.loc[b["step"] != 3])


def test_serie_diaria_y_errores():
    tabla = _tabla()
    serie = ef.serie_diaria([tabla])
    assert list(serie["dia"]) == ["d1", "d2"] and "brier_mcb" in serie
    errores = ef.tabla_errores(tabla, "A")
    assert list(errores["etapa"]) == ["global", "inicio", "medio", "final"]
    fila = errores.iloc[0]
    falsos = ((tabla["p_B4"] >= 0.5) & (tabla["y"] == 0)).sum()
    assert fila["estados_falso_positivo"] == falsos and 0 < fila["tasa_falso_positivo"] < 1
    # Etapas sin errores seguros no rompen el perfil
    tabla["x"] = np.where(tabla["p_B4"] >= 0.5, 1.0, 0.0) + tabla["y"]
    tabla["constante"] = 1.0
    perfil = ef.perfil_errores(tabla, ["x", "constante"])
    assert perfil.iloc[0]["caracteristica"] == "x"
    assert ef.perfil_errores(tabla.assign(p_B4=0.5), ["x"]).empty


def test_h2_reproduce_la_prediccion_con_la_codificacion_del_ajuste():
    rng = np.random.default_rng(0)
    n = 4000
    tabla = pd.DataFrame({"game_turn": rng.integers(1, 20, n), "first_player_is_me": rng.integers(0, 2, n),
                          "own_active_card": rng.integers(0, 300, n), "opp_active_card": rng.integers(0, 300, n)})
    y = (tabla["own_active_card"] < 150).astype(int)
    vocabularios = {c: vocabulario_ids(tabla[c]).tolist() for c in ef.CARD_COLUMNS}
    artefacto = {"vocabularios": vocabularios, "categorias_por_bloque": 255}
    columnas = [tabla[["game_turn", "first_player_is_me"]].to_numpy(np.float32)]
    for c in ef.CARD_COLUMNS:
        columnas.append(ef.codificar_ids_por_bloques(tabla[c].to_numpy(), np.array(vocabularios[c])))
    x = np.hstack(columnas)
    mascara = [False, False] + [True] * (x.shape[1] - 2)
    artefacto["model"] = HistGradientBoostingClassifier(max_iter=10, categorical_features=mascara).fit(x, y)
    assert np.allclose(ef.predecir_h2(artefacto, tabla), artefacto["model"].predict_proba(x)[:, 1])


def test_predicciones_particion_reutiliza_los_artefactos(tmp_path):
    features = ["own_prizes", "opp_prizes", "diff_total_hp", "diff_bench_n", "game_turn", "first_player_is_me"]
    datos = tmp_path / "datos"
    datos.mkdir()
    _corpus(datos, features)
    estados = pd.read_parquet(datos / "estados_1.parquet")
    estados["day"], estados["step"] = "d", estados["turn"]
    estados["own_active_card"] = 1
    estados["opp_active_card"] = 2
    estados.to_parquet(datos / "estados_1.parquet", index=False)
    raiz = tmp_path / "res"
    x, y = estados[features].to_numpy(np.float32), estados["y"].to_numpy()
    arbol = HistGradientBoostingClassifier(max_iter=5, min_samples_leaf=5).fit(x, y)
    lineal = Pipeline([("s", StandardScaler()), ("l", LogisticRegression())]).fit(x, y)
    for patron, modelo in ((ef.MODELO_B2, lineal), (ef.MODELO_B3, arbol), (ef.MODELO_B4, arbol)):
        ruta = raiz / patron.format(e="A")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": modelo, "features": features}, ruta)
    h2 = {"game_turn": estados["game_turn"], "first_player_is_me": estados["first_player_is_me"]}
    h2x = np.column_stack([*h2.values(), np.ones(len(y)), np.zeros(len(y))]).astype(np.float32)
    ruta = raiz / ef.MODELO_H2.format(e="A")
    ruta.parent.mkdir(parents=True)
    joblib.dump({"model": HistGradientBoostingClassifier(max_iter=3, min_samples_leaf=5).fit(h2x, y),
                 "vocabularios": {"own_active_card": [9.0, 1.0], "opp_active_card": [2.0]},
                 "categorias_por_bloque": 255}, ruta)
    (raiz / "b0_b1").mkdir()
    pd.DataFrame([{"escenario": "A", "prevalencia_B0_train": 0.5, "hp_unit_train": 100.0, "intercepto_B1": 0.0,
                   "pendiente_B1": 1.0}]).to_csv(raiz / ef.AJUSTES_B0_B1, index=False)
    tabla = ef.predicciones_particion(datos, raiz, "A", "test", features)
    assert tabla["game_id"].nunique() == 24 and set(tabla["p_B0"]) == {0.5}
    assert all(tabla[f"p_{m}"].between(0, 1).all() for m in ef.MODELOS)
    assert not tabla["id_desconocido"].any()
    with pytest.raises(ValueError, match="caracteristicas esperadas"):
        ef.predicciones_particion(datos, raiz, "A", "test", features[::-1])


def test_shap_aditivo_y_revision_de_fuga():
    rng = np.random.default_rng(0)
    features = ["own_prizes", "game_turn", "diff_hand"]
    x = rng.normal(size=(3000, 3)).astype(np.float32)
    y = (x[:, 0] + 0.5 * x[:, 1] + rng.normal(size=3000) > 0).astype(int)
    codigos = np.arange(3000) // 3
    etapas = np.array(ef.STAGES)[np.arange(3000) % 3]
    modelo = HistGradientBoostingClassifier(max_iter=30, early_stopping=False).fit(x, y)
    valores, _ = ef.valores_shap(modelo, x[:300], n_jobs=1)
    assert valores.shape == (300, 3)
    importancia = ef.importancia_shap(valores, features, etapas[:300], codigos[:300])
    assert set(importancia["etapa"]) == set(ef.GRUPOS)
    assert importancia.query("etapa == 'global'")["fraccion"].sum() == pytest.approx(1.0)
    individual = ef.auc_individual(x, y, codigos, features)
    assert individual.iloc[0]["caracteristica"] == "own_prizes"
    assert individual.iloc[0]["auc"] == pytest.approx(
        roc_auc_score(y, x[:, 0], sample_weight=ef.pesos_partida(codigos)))
    # Una caracteristica que lo explica todo (o un desenlace colado) detiene el proceso
    domina = ef.revision_fuga(importancia, individual, features, limite_fraccion=0.01)
    assert not domina["aprobada"] and not domina["ninguna_domina"]
    colada = ef.revision_fuga(importancia, individual, [*features, "y"])
    assert not colada["aprobada"] and colada["prohibidas"] == ["y"]
    predice = individual.assign(auc_mejor_sentido=0.99)
    assert not ef.revision_fuga(importancia, predice, features)["aprobada"]
    assert ef.revision_fuga(importancia, individual, features, limite_fraccion=1.0)["aprobada"]


def test_muestra_partidas_completas():
    ids = np.repeat(np.arange(50), 3)
    assert len(ef.muestra_partidas(ids, 10)) == 10
    assert np.array_equal(ef.muestra_partidas(ids, 10), ef.muestra_partidas(ids, 10))
    assert len(ef.muestra_partidas(ids, 100)) == 50


def test_curva_de_aprendizaje_no_usa_test_y_reutiliza_el_final(tmp_path):
    features = ["a", "b"]
    datos = tmp_path / "datos"
    datos.mkdir()
    _corpus(datos, features, partidas=400)
    stream = ScenarioStream(datos, "A", tuple(features))
    train = materialize_split(stream, features, "train", tmp_path)
    assert len(train.games) == 160
    final = HistGradientBoostingClassifier(max_iter=7, early_stopping=False).fit(
        np.asarray(train.x), np.asarray(train.y))
    ruta = tmp_path / "final.joblib"
    joblib.dump({"model": final, "n_iter_vigilancia": 7, "version_sklearn": sklearn_version}, ruta)
    candidata = pd.DataFrame([{"seleccionada_por": "auc", "trial": 20, "learning_rate": 0.1, "max_leaf_nodes": 8,
                               "min_samples_leaf": 20, "l2_regularization": 0.1}])
    curva = ef.curva_aprendizaje(datos, "A", features, candidata, ruta, cache_dir=tmp_path,
                                 fracciones=(0.5, 1.0), max_partidas_train=30)
    assert set(curva["fraccion"]) == {0.5, 1.0} and set(curva["conjunto"]) == {"train", "val"}
    assert curva.query("conjunto == 'val' and etapa == 'global'")["n_partidas"].eq(80).all()
    assert curva.query("conjunto == 'train' and etapa == 'global'")["n_partidas"].eq(30).all()
    assert curva.query("fraccion == 1.0")["n_iter"].eq(7).all()
    assert curva.query("fraccion == 0.5")["partidas_train"].eq(80).all()
    diagnostico = ef.diagnostico_sobreajuste(curva)
    assert list(diagnostico["fraccion"]) == [0.5, 1.0]
    assert diagnostico["brecha_auc"].iloc[0] == pytest.approx(
        diagnostico["auc_train"].iloc[0] - diagnostico["auc_val"].iloc[0])
