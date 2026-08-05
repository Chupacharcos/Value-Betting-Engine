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


## Integración, datos y licencia

**Licencia:** MIT (ver [LICENSE](LICENSE)) — uso libre, incluido comercial,
manteniendo el aviso de copyright. Sin garantía ni soporte incluidos.

### Exportación CSV

Las señales se sirven también en **CSV plano**, una fila por value bet, para
abrirlas en Excel o Google Sheets y cargarlas en un tracker sin aplanar el JSON
a mano:

```bash
curl "http://localhost:8003/ml/valuebet/signals.csv?min_ev=3" -o value_bets.csv
```

Columnas: `fixture_id, date, league, home_team, away_team, outcome, odd,
model_prob, implied_prob, edge, ev_pct, kelly, overround_pct`.

> **Sobre integrar una casa de apuestas:** ejecutar apuestas automáticamente
> exigiría credenciales de la API de un operador (Betfair y similares), que
> requieren cuenta aprobada y no se pueden implementar ni probar sin ellas. Este
> motor **no ejecuta órdenes reales**: detecta valor y lo expone. El paper
> trading es simulado.

### Tratamiento de datos

Sólo datos deportivos públicos: partidos, cuotas y probabilidades del modelo.
**Sin datos personales, sin cuentas de usuario, sin dinero real.** Las cuotas se
cachean en disco (`cache/`) para no golpear la fuente en cada petición.

**Qué sale del servidor:** nada hacia proveedores de IA. **Este proyecto no usa
ningún LLM**: la detección de valor es cálculo estadístico (probabilidad
calibrada del modelo frente a la probabilidad implícita de la cuota, criterio de
Kelly). La única salida es la descarga periódica de cuotas.

### Despliegue propio y costes

El repositorio es la aplicación completa. Depende de un **Sports Engine**
(`SPORTS_ENGINE_URL`, también MIT y en este portfolio) para las probabilidades.
Código gratuito (MIT); el coste es la infraestructura y, si se quiere, una
fuente de cuotas de pago. La implantación y el mantenimiento corren a cargo de
quien lo despliega — el autor no ofrece soporte ni consultoría.
