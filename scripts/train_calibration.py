#!/usr/bin/env python3
"""
Value Betting Engine — Calibración de probabilidades
Ajusta los pesos del modelo de Sports Engine para value betting óptimo.
"""
import json
import numpy as np
from pathlib import Path

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


def calibrate_kelly(history_proba, history_odds, history_result):
    """
    Calibra el umbral Kelly usando datos históricos.
    history_proba: probs del modelo [p_home, p_draw, p_away]
    history_odds: decimal odds [o_home, o_draw, o_away]
    history_result: 0/1/2
    """
    results = []
    for proba, odds, result in zip(history_proba, history_odds, history_result):
        best_bet = np.argmax(proba)
        ev = proba[best_bet] * odds[best_bet] - 1
        kelly = (proba[best_bet] * odds[best_bet] - 1) / (odds[best_bet] - 1)
        won = 1 if best_bet == result else 0
        results.append({"ev": ev, "kelly": kelly, "won": won,
                        "odds": odds[best_bet], "prob": proba[best_bet]})

    # Filtrar por EV positivo
    ev_positive = [r for r in results if r["ev"] > 0]
    if not ev_positive:
        return {"min_ev_threshold": 0.05, "min_kelly_threshold": 0.02,
                "half_kelly": True, "hit_rate": 0.5}

    ev_threshold = np.percentile([r["ev"] for r in ev_positive], 25)
    kelly_threshold = np.percentile([r["kelly"] for r in ev_positive], 25)
    hit_rate = np.mean([r["won"] for r in ev_positive])

    return {
        "min_ev_threshold": max(0.03, float(ev_threshold)),
        "min_kelly_threshold": max(0.02, float(kelly_threshold)),
        "half_kelly": True,  # Usar medio Kelly para gestión de riesgo
        "hit_rate_ev_positive": float(hit_rate),
        "n_value_bets": len(ev_positive),
        "n_total": len(results),
    }


def generate_calibration_from_synthetic():
    """Genera calibración desde datos históricos sintéticos."""
    rng = np.random.RandomState(42)
    n = 500

    # Simular distribución realista de fútbol europeo
    # Frecuencias reales LaLiga: 45% local, 25% empate, 30% visitante
    results = rng.choice([0, 1, 2], size=n, p=[0.45, 0.25, 0.30])

    # Probs del modelo (ligeramente mejores que azar)
    probas = []
    for r in results:
        base = [0.35, 0.28, 0.37]
        # Añadir algo de "edge" al modelo
        base[r] += rng.uniform(0.05, 0.15)
        total = sum(base)
        probas.append([p / total for p in base])

    # Cuotas de bookmaker (con margen ~5%)
    odds_list = []
    for prob in probas:
        margin = 0.05
        raw_odds = [1 / (p + margin / 3) for p in prob]
        odds_list.append(raw_odds)

    cal = calibrate_kelly(probas, odds_list, results)

    # ROI simulado
    stake = 1.0
    bankroll = 100.0
    for prob, odds, result in zip(probas, odds_list, results):
        best_bet = np.argmax(prob)
        ev = prob[best_bet] * odds[best_bet] - 1
        kelly = (prob[best_bet] * odds[best_bet] - 1) / (odds[best_bet] - 1)
        if ev >= cal["min_ev_threshold"] and kelly >= cal["min_kelly_threshold"]:
            half_k = min(kelly * 0.5, 0.05)  # Max 5% del bankroll
            bet_amount = bankroll * half_k
            if best_bet == result:
                bankroll += bet_amount * (odds[best_bet] - 1)
            else:
                bankroll -= bet_amount

    roi = (bankroll - 100) / 100 * 100
    cal["simulated_roi_pct"] = round(roi, 2)
    cal["simulated_final_bankroll"] = round(bankroll, 2)
    return cal


if __name__ == "__main__":
    print("=== Value Betting Engine — Calibración ===")
    cal = generate_calibration_from_synthetic()
    print(f"Configuración calibrada:")
    for k, v in cal.items():
        print(f"  {k}: {v}")

    with open(MODELS_DIR / "calibration.json", "w") as f:
        json.dump(cal, f, indent=2)
    print(f"\n✓ Calibración guardada en {MODELS_DIR}/calibration.json")
