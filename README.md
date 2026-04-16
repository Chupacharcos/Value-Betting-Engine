# Value Betting Engine

Motor de detección de apuestas de valor que combina predicciones del **Sports Performance Engine** con cuotas en tiempo real de **OddsPapi** (350+ bookmakers). Calcula **Expected Value** y **Kelly Criterion** para identificar oportunidades donde el modelo supera al mercado.

## Demo en vivo

[adrianmoreno-dev.com/demo/value-betting](https://adrianmoreno-dev.com/demo/value-betting)

## Arquitectura

```
Sports Engine (prob predichas)
    ├── OddsPapi API (350+ bookmakers: Pinnacle, Bet365, Betfair...)
    │       └── Cuotas de mercado → implied probability
    └── EV = (prob_modelo × odd) - 1
            └── Kelly = (b×p - q)/b → Half-Kelly sizing
                    └── Solo señales EV > 0
```

## Stack

| Componente | Tecnología |
|---|---|
| Predicciones | Sports Performance Engine (HTTP) |
| Cuotas | OddsPapi API (350+ bookmakers) |
| Criterio de tamaño | Half-Kelly Criterion |
| Filtro | Solo EV positivo |
| API | FastAPI (puerto 8003) |

## Fórmulas clave

**Expected Value:**
```
EV = (prob_modelo × odd) - 1
```
Si EV > 0, existe ventaja matemática sobre el bookmaker.

**Kelly Criterion (Half-Kelly):**
```
Kelly completo = (b×p - q) / b
Half-Kelly     = Kelly / 2   ← usado para gestión de riesgo
```
Donde `b = odd - 1`, `p = prob_modelo`, `q = 1 - p`.

**Overround:**
```
overround = Σ(1/odd_i) - 1
```
Margen del bookmaker embebido en las cuotas.

## OddsPapi

- **350+ bookmakers** incluyendo Pinnacle (sharp), Bet365, Betfair Exchange
- Cuotas de mercado 1X2 para los principales partidos
- Usado para calcular `implied_prob = 1 / odd`

## Métricas (Backtesting 2022-2024)

| Métrica | Valor |
|---|---|
| ROI acumulado | Positivo |
| Bookmakers | 350+ |
| Filtro | EV > 0 únicamente |
| Tamaño de apuesta | Half-Kelly |

## Endpoints

```
GET /ml/valuebet/health    Estado del servicio
GET /ml/valuebet/signals   Señales de valor activas
GET /ml/valuebet/backtest  Resultados del backtesting
GET /ml/valuebet/stats     Métricas del motor
```

### Ejemplo response signals

```json
{
  "signals": [{
    "home_team": "Real Madrid",
    "away_team": "Barcelona",
    "league": "LaLiga",
    "value_bets": [{
      "outcome": "Empate",
      "odd": 3.4,
      "model_prob": 0.439,
      "ev": 0.49,
      "ev_pct": 49.26,
      "half_kelly": 0.10,
      "half_kelly_pct": 10.26
    }]
  }]
}
```

## Instalación

```bash
git clone https://github.com/Chupacharcos/Value-Betting-Engine.git
cd Value-Betting-Engine
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Requiere Sports Performance Engine en puerto 8001
# Añadir ODDSPAPI_KEY en .env
uvicorn api:app --port 8003
```

## Licencia

MIT
