"""Particiones agrupadas por partida (escenarios A, B y C), cobertura de cartas y cortes de etapa.

Reglas que garantiza este modulo:
- Cada partida cae en UNA sola particion por escenario: sus estados nunca se reparten.
- Particiones: train (entrenar), val (elegir hiperparametros), calib (ajustar la calibracion)
  y test (evaluacion final, se usa una sola vez). "fuera" = partida no usada en ese escenario.
- A: azar por partida, 60/15/10/15.
- B: cronologico por DIAS COMPLETOS segun configs/particiones.yaml (primer dia excluido).
- C: arquetipos reservados (Pokemon principal) solo en test; el resto al azar 60/15/10.
- Cobertura de cartas (A y C): toda carta activa del corpus aparece en train; si falta alguna,
  se mueve a train la partida mas corta que la contiene. En B no se mueve nada (romperia la
  cronologia): se reporta la cobertura efectiva.
- Todo es reproducible con la semilla SEED.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ptcg_wp.features import CARD_COLUMNS, SENTINEL

# Semilla global del proyecto
SEED = 2026

# Proporciones de cada particion, en este orden
PROPORCIONES = {"train": 0.60, "val": 0.15, "calib": 0.10, "test": 0.15}
ORDEN = list(PROPORCIONES)
FUERA = "fuera"


def load_games(data_dir):
    """Lee todas las tablas de partidas y deja solo las que tienen ganador (sin empates)."""
    files = sorted(Path(data_dir).glob("partidas_*.parquet"))
    games = pd.concat((pd.read_parquet(p) for p in files), ignore_index=True)
    return games[games["winner"] != -1].reset_index(drop=True)


def load_card_pairs(data_dir):
    """Pares (game_id, carta) de las cartas que estuvieron activas en cada partida (ambos lados).
    Solo se leen 3 columnas de las tablas de estados, asi que es rapido y usa poca memoria.
    """
    parts = []
    for p in sorted(Path(data_dir).glob("estados_*.parquet")):
        df = pd.read_parquet(p, columns=["game_id"] + CARD_COLUMNS)
        for c in CARD_COLUMNS:
            parts.append(df[["game_id", c]].rename(columns={c: "card"}).drop_duplicates())
    pairs = pd.concat(parts, ignore_index=True).drop_duplicates()
    return pairs[pairs["card"] != SENTINEL].reset_index(drop=True)


def load_b_config(path):
    """Lee la asignacion de dias del escenario B desde configs/particiones.yaml."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)["escenario_B"]


def _cut(n, props=PROPORCIONES):
    """Etiquetas para n elementos ya ordenados: los primeros van a train, luego val, etc."""
    bounds = np.round(np.cumsum(list(props.values())) * n).astype(int)
    bounds[-1] = n
    labels = np.empty(n, dtype=object)
    start = 0
    for name, end in zip(props, bounds):
        labels[start:end] = name
        start = end
    return labels


def split_a(games, seed=SEED):
    """Escenario A (partidas nuevas): reparto al azar por partida."""
    order = np.random.default_rng(seed).permutation(len(games))
    labels = np.empty(len(games), dtype=object)
    labels[order] = _cut(len(games))
    return labels


def split_b(games, b_config):
    """Escenario B (cronologico): cada dia completo va a la particion que indica la config.
    Los dias de 'excluir' (y cualquier dia no listado) quedan como 'fuera'.
    """
    day_to_split = {}
    for name in ORDEN:
        for d in b_config.get(name, []):
            day_to_split[str(d)] = name
    for d in b_config.get("excluir", []):
        day_to_split[str(d)] = FUERA
    return games["day"].map(day_to_split).fillna(FUERA).to_numpy(dtype=object)


def reserve_mains(games, target=0.15, tol=0.03, seed=SEED):
    """Elige Pokemon principales (arquetipos de mazo) reservados para el escenario C.
    Se recorren los principales en orden aleatorio y se agregan mientras las partidas
    que los usan (en cualquiera de los dos jugadores) no pasen de target + tol.
    Devuelve (lista de principales reservados, mascara de partidas reservadas).
    """
    m0, m1 = games["main_0"].to_numpy(), games["main_1"].to_numpy()
    mains = np.array(sorted((set(m0.tolist()) | set(m1.tolist())) - {SENTINEL}))
    np.random.default_rng(seed + 1).shuffle(mains)
    reserved_games = np.zeros(len(games), dtype=bool)
    reserved = []
    for m in mains:
        candidate = reserved_games | (m0 == m) | (m1 == m)
        if candidate.mean() > target + tol:
            continue
        reserved_games = candidate
        reserved.append(int(m))
        if reserved_games.mean() >= target:
            break
    return reserved, reserved_games


def split_c(games, seed=SEED):
    """Escenario C (arquetipos reservados): test = toda partida donde algun jugador usa un
    principal reservado. El resto se reparte al azar en train/val/calib (60/15/10 reescalado).
    Devuelve (etiquetas, principales reservados, mascara de partidas reservadas).
    """
    reserved, is_test = reserve_mains(games, seed=seed)
    rest = np.flatnonzero(~is_test)
    order = np.random.default_rng(seed + 2).permutation(rest)
    props = {k: v for k, v in PROPORCIONES.items() if k != "test"}
    total = sum(props.values())
    props = {k: v / total for k, v in props.items()}
    labels = np.empty(len(games), dtype=object)
    labels[is_test] = "test"
    labels[order] = _cut(len(order), props)
    return labels, reserved, is_test


def ensure_coverage(games, labels, pairs, movable):
    """Regla de cobertura del articulo: toda carta activa del corpus debe aparecer en train.
    Por cada carta que falte en train, se mueve a train la partida MAS CORTA (menos pasos)
    que la contiene, entre las partidas permitidas ('movable').
    Devuelve (etiquetas corregidas, partidas movidas, cartas que siguen sin cubrir).
    """
    labels = labels.copy()
    idx = pd.Series(np.arange(len(games)), index=games["game_id"].to_numpy())
    pos = idx.reindex(pairs["game_id"].to_numpy()).to_numpy()
    ok = ~np.isnan(pos)
    pos, cards = pos[ok].astype(int), pairs["card"].to_numpy()[ok]
    n_steps = games["n_steps"].to_numpy()

    in_train = labels[pos] == "train"
    train_cards = set(cards[in_train].tolist())
    missing = sorted(set(cards.tolist()) - train_cards)
    moved, uncovered = [], []
    for card in missing:
        if card in train_cards:
            continue
        cand = np.unique(pos[(cards == card) & movable[pos]])
        if len(cand) == 0:
            uncovered.append(int(card))
            continue
        g = cand[np.argmin(n_steps[cand])]
        labels[g] = "train"
        moved.append(int(games["game_id"].iat[g]))
        train_cards |= set(cards[pos == g].tolist())
    return labels, moved, uncovered


def make_splits(games, pairs, b_config, seed=SEED):
    """Tabla con una fila por partida y su particion en cada escenario, mas un reporte."""
    out = games[["game_id", "day"]].copy()
    report = {}

    a = split_a(games, seed)
    out["split_A"], report["A_movidas"], report["A_sin_cubrir"] = ensure_coverage(
        games, a, pairs, movable=np.ones(len(games), dtype=bool))

    out["split_B"] = split_b(games, b_config)
    _, _, report["B_sin_cubrir"] = ensure_coverage(
        games, out["split_B"].to_numpy(), pairs, movable=np.zeros(len(games), dtype=bool))

    c, reserved, is_test = split_c(games, seed)
    out["split_C"], report["C_movidas"], report["C_sin_cubrir"] = ensure_coverage(
        games, c, pairs, movable=~is_test)
    report["C_reservados"] = reserved

    cards_per_game = pairs.groupby("card")["game_id"].nunique()
    report["cartas_en_corpus"] = int(len(cards_per_game))
    report["cartas_en_una_sola_partida"] = int((cards_per_game == 1).sum())
    return out, report


def stage_cutoffs(train_turns, q=(1 / 3, 2 / 3)):
    """Cortes de etapa (inicio/medio/final) como terciles del turno, calculados SOLO con train."""
    c1, c2 = np.quantile(np.asarray(train_turns), q)
    return float(c1), float(c2)


def assign_stage(turns, cuts):
    """Etapa de cada fila segun los cortes: inicio (<= c1), medio (<= c2) o final."""
    c1, c2 = cuts
    turns = np.asarray(turns)
    return np.where(turns <= c1, "inicio", np.where(turns <= c2, "medio", "final"))


def card_coverage(states, split, cols=CARD_COLUMNS):
    """Auditoria de cobertura: por particion, que tanto aparecen cartas activas no vistas en train.
    states: filas utiles; split: particion de cada fila (misma longitud).
    """
    split = np.asarray(split)
    seen = set()
    for c in cols:
        seen |= set(states.loc[split == "train", c].unique().tolist())
    rows = {}
    for name in ORDEN:
        part = states[split == name]
        if part.empty:
            continue
        unseen = np.zeros(len(part), dtype=bool)
        new_cards = set()
        for c in cols:
            mask = ~part[c].isin(seen).to_numpy()
            unseen |= mask
            new_cards |= set(part.loc[mask, c].unique().tolist())
        rows[name] = {"filas": len(part), "pct_filas_carta_no_vista": round(100 * unseen.mean(), 3),
                      "cartas_no_vistas": len(new_cards)}
    return pd.DataFrame(rows).T


def main():
    """Linea de comandos: genera particiones.parquet en la carpeta de datos e imprime el reporte."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/content/datos")
    ap.add_argument("--config", default="configs/particiones.yaml")
    args = ap.parse_args()
    games = load_games(args.dir)
    pairs = load_card_pairs(args.dir)
    splits, report = make_splits(games, pairs, load_b_config(args.config))
    out = Path(args.dir) / "particiones.parquet"
    splits.to_parquet(out, index=False)
    print(f"{len(splits)} partidas -> {out}")
    for s in ("split_A", "split_B", "split_C"):
        frac = splits[s].value_counts(normalize=True).reindex(ORDEN + [FUERA]).fillna(0).round(3)
        print(s, frac.to_dict())
    print("dias de B:", splits.groupby("split_B")["day"].unique().apply(sorted).to_dict())
    print("cartas activas en el corpus:", report["cartas_en_corpus"],
          "| en una sola partida:", report["cartas_en_una_sola_partida"])
    print("A: partidas movidas a train por cobertura:", len(report["A_movidas"]),
          "| cartas sin cubrir:", report["A_sin_cubrir"])
    print("B: cartas sin cubrir (no se mueve nada en B):", report["B_sin_cubrir"])
    print("C: principales reservados:", report["C_reservados"])
    print("C: partidas movidas a train por cobertura:", len(report["C_movidas"]),
          "| cartas sin cubrir:", report["C_sin_cubrir"])


if __name__ == "__main__":
    main()