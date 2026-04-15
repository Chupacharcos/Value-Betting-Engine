#!/usr/bin/env python3
"""
Value Betting Engine — OddsPapi Integration
Descarga cuotas de LaLiga vía OddsPapi API y las guarda en cache.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

ODDSPAPI_KEY = os.getenv("ODDSPAPI_KEY", "")
ODDSPAPI_BASE = "https://api.oddspapi.io/v4"


def fetch_sports():
    """Lista de deportes disponibles."""
    if not ODDSPAPI_KEY:
        return []
    r = requests.get(f"{ODDSPAPI_BASE}/sports",
                     params={"apiKey": ODDSPAPI_KEY}, timeout=10)
    if r.status_code == 200:
        return r.json()
    return []


def fetch_laliga_odds():
    """Descarga cuotas de LaLiga (próximos 7 días)."""
    if not ODDSPAPI_KEY:
        print("ODDSPAPI_KEY no configurada. Usando odds de demo.")
        return generate_demo_odds()

    try:
        # Obtener fixtures de LaLiga
        r_fix = requests.get(f"{ODDSPAPI_BASE}/fixtures",
                             params={"apiKey": ODDSPAPI_KEY,
                                     "sport": "football",
                                     "league": "spain-la-liga"},
                             timeout=15)
        if r_fix.status_code != 200:
            print(f"Error fixtures: {r_fix.status_code}. Usando demo.")
            return generate_demo_odds()

        fixtures = r_fix.json().get("data", [])[:20]
        odds_data = []
        for fixture in fixtures:
            try:
                r_odds = requests.get(f"{ODDSPAPI_BASE}/odds",
                                      params={"apiKey": ODDSPAPI_KEY,
                                              "fixtureId": fixture["id"]},
                                      timeout=10)
                if r_odds.status_code == 200:
                    odds_data.append({"fixture": fixture, "odds": r_odds.json()})
                time.sleep(0.1)  # Rate limit
            except Exception:
                pass

        cache = {"updated": str(datetime.now()), "source": "oddspapi", "data": odds_data}
        with open(CACHE_DIR / "odds_cache.json", "w") as f:
            json.dump(cache, f, indent=2)
        print(f"✓ {len(odds_data)} partidos con cuotas descargados")
        return odds_data
    except Exception as e:
        print(f"Error OddsPapi: {e}. Usando demo.")
        return generate_demo_odds()


def generate_demo_odds():
    """Genera cuotas de demostración basadas en datos reales históricos."""
    matches = [
        ("Real Madrid", "Barcelona", 2.20, 3.40, 3.10),
        ("Atlético de Madrid", "Sevilla", 1.75, 3.50, 4.50),
        ("Valencia", "Real Betis", 2.40, 3.20, 2.90),
        ("Athletic Club", "Villarreal", 2.10, 3.30, 3.40),
        ("Girona", "Osasuna", 2.00, 3.20, 3.80),
        ("Real Sociedad", "Celta de Vigo", 1.80, 3.40, 4.20),
        ("Getafe", "Rayo Vallecano", 2.60, 3.10, 2.65),
        ("Las Palmas", "Mallorca", 2.20, 3.20, 3.20),
        ("Alavés", "Cádiz", 2.30, 3.30, 3.00),
        ("Almería", "Granada", 2.50, 3.20, 2.80),
    ]
    data = []
    base_date = datetime.now()
    for i, (home, away, h_odd, d_odd, a_odd) in enumerate(matches):
        from datetime import timedelta
        match_date = base_date + timedelta(days=i // 3 + 1)
        data.append({
            "fixture": {
                "id": 10000 + i,
                "home_team": home,
                "away_team": away,
                "date": match_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "league": "LaLiga",
                "season": "2024/25",
            },
            "odds": {
                "1x2": {
                    "home": h_odd,
                    "draw": d_odd,
                    "away": a_odd,
                    "bookmaker": "Pinnacle",
                }
            },
        })

    cache = {"updated": str(datetime.now()), "source": "demo", "data": data}
    with open(CACHE_DIR / "odds_cache.json", "w") as f:
        json.dump(cache, f, indent=2)
    print(f"✓ Demo odds generadas: {len(data)} partidos")
    return data


if __name__ == "__main__":
    fetch_laliga_odds()
