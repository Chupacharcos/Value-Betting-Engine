#!/usr/bin/env python3
"""
Backtest REAL del Value Betting Engine sobre LaLiga.

Usa: el modelo de sports-engine (entrenado hasta 22/23, validado en 23/24) y
las cuotas de cierre REALES de football-data.co.uk para las temporadas de test
(24/25 y 25/26) — 758 partidos que el modelo nunca vio.

Estrategia evaluada (la que describe el producto):
  EV = p_modelo × cuota − 1 ; se apuesta cuando EV > umbral, con stake plano
  (1 unidad) y también con half-Kelly. Cuotas: media de mercado al cierre (Avg)
  — más alcanzables para retail que el máximo del mercado.

El resultado se publica TAL CUAL en models/backtest_real.json: si la estrategia
pierde dinero (lo esperable: el cierre del mercado es más preciso que un modelo
de stats públicas), se muestra el ROI negativo. Ese es el punto del proyecto:
enseñar el mecanismo de EV/Kelly y por qué 'batir al cierre' es tan difícil.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

SPORTS = Path("/var/www/sports-engine")
OUT = Path(__file__).resolve().parent.parent / "models" / "backtest_real.json"

TEST_SEASONS = {"2425", "2526"}
EV_THRESHOLD = 0.05          # apostar si EV > 5%
KELLY_FRACTION = 0.5         # half-Kelly
START_BANKROLL = 100.0

FEATURE_COLS = [
    "home_elo", "away_elo", "elo_diff",
    "home_gf_avg5", "home_ga_avg5", "home_sot_avg5", "home_sota_avg5", "home_form5",
    "away_gf_avg5", "away_ga_avg5", "away_sot_avg5", "away_sota_avg5", "away_form5",
    "home_gf_home_avg", "away_gf_away_avg",
    "form_diff", "sot_diff",
]
LABELS = {"H": 0, "D": 1, "A": 2}


def main():
    feats = pd.read_parquet(SPORTS / "data" / "features.parquet")
    raw = pd.read_parquet(SPORTS / "data" / "matches_real.parquet")
    odds = raw[["match_id", "avg_h", "avg_d", "avg_a"]]
    df = feats.merge(odds, on="match_id", how="left")
    df = df[df["season"].isin(TEST_SEASONS)].dropna(subset=["avg_h", "avg_d", "avg_a"])
    print(f"Partidos de test con cuotas reales: {len(df)}")

    lgbm = joblib.load(SPORTS / "models" / "lgbm_outcome.pkl")
    xgbc = joblib.load(SPORTS / "models" / "xgb_outcome.pkl")
    proba = (lgbm.predict_proba(df[FEATURE_COLS]) + xgbc.predict_proba(df[FEATURE_COLS])) / 2

    odds_mat = df[["avg_h", "avg_d", "avg_a"]].to_numpy(dtype=float)
    y = df["result"].map(LABELS).to_numpy()

    ev = proba * odds_mat - 1.0          # EV por resultado

    # ── Estrategia stake plano ────────────────────────────────────────────────
    flat_pnl, flat_bets, flat_wins = [], 0, 0
    # ── Half-Kelly sobre bankroll ─────────────────────────────────────────────
    bankroll = START_BANKROLL
    bank_curve = [bankroll]

    for i in range(len(df)):
        j = int(np.argmax(ev[i]))
        if ev[i][j] <= EV_THRESHOLD:
            continue
        flat_bets += 1
        won = (y[i] == j)
        flat_wins += int(won)
        o = odds_mat[i][j]
        flat_pnl.append((o - 1.0) if won else -1.0)

        # Kelly: f* = (p·o − 1) / (o − 1), recortado y half
        p = proba[i][j]
        f = max(0.0, (p * o - 1.0) / (o - 1.0)) * KELLY_FRACTION
        f = min(f, 0.10)  # cap 10% bankroll por apuesta
        stake = bankroll * f
        bankroll += stake * ((o - 1.0) if won else -1.0)
        bank_curve.append(bankroll)

    flat_pnl = np.array(flat_pnl)
    roi_flat = float(flat_pnl.sum() / max(1, flat_bets) * 100)
    curve = np.array(bank_curve)
    peak = np.maximum.accumulate(curve)
    max_dd = float(((curve - peak) / peak).min() * 100)

    result = {
        "descripcion": "Backtest real: modelo sports-engine vs cuotas de cierre medias (Avg) de football-data.co.uk",
        "test_seasons": sorted(TEST_SEASONS),
        "n_matches": int(len(df)),
        "ev_threshold": EV_THRESHOLD,
        "n_bets": int(flat_bets),
        "hit_rate_pct": round(flat_wins / max(1, flat_bets) * 100, 1),
        "roi_flat_pct": round(roi_flat, 2),
        "units_pnl_flat": round(float(flat_pnl.sum()), 2),
        "kelly": {
            "fraction": KELLY_FRACTION,
            "start_bankroll": START_BANKROLL,
            "final_bankroll": round(float(bankroll), 2),
            "return_pct": round((bankroll / START_BANKROLL - 1) * 100, 2),
            "max_drawdown_pct": round(max_dd, 2),
        },
        "honest_note": (
            "Resultado sin maquillaje sobre 2 temporadas no vistas. Las cuotas de "
            "cierre agregan información que un modelo de stats públicas no tiene; "
            "un ROI negativo aquí es el resultado esperable y honesto — el valor "
            "del proyecto es el mecanismo (EV, Kelly, calibración), no una promesa "
            "de beneficio."
        ),
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
