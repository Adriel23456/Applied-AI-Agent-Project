"""Particiones agrupadas por partida (escenarios A, B y C), cortes de etapa y cobertura de cartas.

Reglas que garantiza este modulo:
- Cada partida cae en UNA sola particion por escenario: sus estados nunca se reparten.
- Proporciones 60/15/10/15: train (entrenar), val (elegir hiperparametros),
  calib (ajustar la calibracion) y test (evaluacion final, se usa una sola vez).
- Todo es reproducible con la semilla SEED.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ptcg_wp.features import SENTINEL

# Semilla global del proyecto
SEED = 2026

# Proporciones de cada particion, en este orden
PROPORCIONES = {"train": 0.60, "val": 0.15, "calib": 0.10, "test": 0.15}
ORDEN = list(PROPORCIONES)


def load_games(data_dir):
    """Lee todas las tablas de partidas y deja solo las que tienen ganador (sin empates)."""
    files = sorted(Path(data_dir).glob("partidas_*.parquet"))
    games = pd.concat((pd.read_parquet(p) for p in files), ignore_index=True)
    return games[games["winner"] != -1].reset_index(drop=True)


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
    return pd.Series(labels, index=games.index)


def split_b(games):
    """Escenario B (cronologico): se ordena por dia y luego por game_id, y se corta.
    Train son las partidas mas antiguas y test las mas recientes.
    """
    order = np.lexsort((games["game_id"].to_numpy(), games["day"].to_numpy()))
    labels = np.empty(len(games), dtype=object)
    labels[order] = _cut(len(games))
    return pd.Series(labels, index=games.index)


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
    """Escenario C (mazos reservados): test = toda partida donde algun jugador usa un
    principal reservado. El resto se reparte al azar en train/val/calib (60/15/10 reescalado).
    Asi ningun mazo reservado aparece como principal en entrenamiento.
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
    return pd.Series(labels, index=games.index), reserved


def make_splits(games, seed=SEED):
    """Tabla con una fila por partida y su particion en cada escenario."""
    out = games[["game_id", "day"]].copy()
    out["split_A"] = split_a(games, seed)
    out["split_B"] = split_b(games)
    out["split_C"], reserved = split_c(games, seed)
    return out, reserved


def stage_cutoffs(train_turns, q=(1 / 3, 2 / 3)):
    """Cortes de etapa (inicio/medio/final) como terciles del turno, calculados SOLO con train."""
    c1, c2 = np.quantile(np.asarray(train_turns), q)
    return float(c1), float(c2)


def assign_stage(turns, cuts):
    """Etapa de cada fila segun los cortes: inicio (<= c1), medio (<= c2) o final."""
    c1, c2 = cuts
    turns = np.asarray(turns)
    return np.where(turns <= c1, "inicio", np.where(turns <= c2, "medio", "final"))


def card_coverage(states, split, cols=("own_active_card", "opp_active_card")):
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
    """Linea de comandos: genera particiones.parquet en la carpeta de datos."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/content/datos")
    args = ap.parse_args()
    games = load_games(args.dir)
    splits, reserved = make_splits(games)
    out = Path(args.dir) / "particiones.parquet"
    splits.to_parquet(out, index=False)
    print(f"{len(splits)} partidas -> {out}")
    print("principales reservados en C:", reserved)
    for s in ("split_A", "split_B", "split_C"):
        print(s, splits[s].value_counts(normalize=True).reindex(ORDEN).round(3).to_dict())


if __name__ == "__main__":
    main()