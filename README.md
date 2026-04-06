# Real-Time Market Data Pipeline & Analytics System

## Overview

A real-time data engineering pipeline that ingests live BTC/USDT prices from Binance, computes trading indicators, stores them in SQLite, serves them through a FastAPI backend, and streams everything to a browser dashboard via WebSocket.

Built as a full end-to-end data project covering ingestion → processing → storage → API → frontend.

---

## Features

- Live price ingestion from the Binance API every 5 seconds
- Real-time processing: SMA, EMA, Bollinger Bands, volatility, spike detection
- SQLite storage with a clean schema (no ORM overhead)
- FastAPI REST endpoints + WebSocket broadcast
- Chart.js dashboard with a live-updating price chart
- Flip cards on hover — each metric card reveals a plain-English definition
- Emerge pulse animation on every new data point
- Rule-based AI market insight refreshed every 30 seconds
- Groq LLM (LLaMA3) powered insight via toggle — falls back to rule-based if unavailable
- Auto-reconnecting WebSocket client
- pytest unit test suite for all processing logic
- Fully containerised with Docker — one-command setup

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Data processing | Pandas |
| API framework | FastAPI + Uvicorn |
| Database | SQLite |
| Frontend | HTML / CSS / JavaScript |
| Charting | Chart.js |
| Data source | Binance REST API |
| LLM Insight | Groq API (LLaMA3-8b) |
| Testing | pytest |
| Containerisation | Docker |

---

## Architecture

```
Binance API
    ↓
ingestion.py   →  fetch_price()
    ↓
processing.py  →  calculate_metrics()
                  (SMA, EMA, Bollinger Bands, trend, spike)
    ↓
storage.py     →  save_record()  →  data/market_data.db (SQLite)
    ↓
api.py         →  FastAPI REST endpoints + WebSocket broadcast
    ↓
index.html     →  Live browser dashboard
```

---

## Project Structure

```
project/
├── api.py               # FastAPI app — REST + WebSocket
├── ai_integration.py    # Groq LLM insight module
├── config.py            # All constants (symbol, intervals, thresholds)
├── ingestion.py         # Fetch live price from Binance
├── main.py              # Standalone pipeline runner (no server)
├── processing.py        # SMA, EMA, volatility, Bollinger Bands, trend
├── storage.py           # SQLite init / load / save
├── index.html           # Frontend dashboard
├── Dockerfile           # Container definition
├── .dockerignore        # Files excluded from Docker image
├── requirements.txt     # Python dependencies
├── .env                 # API keys — never committed to git
├── data/
│   └── market_data.db   # Auto-created SQLite database
├── code.ipynb           # Original prototype notebook (reference only)
└── tests/
    └── test_processing.py
```

---

## How to Run

### Option A — Docker (recommended)

**Requirements:** Docker Desktop installed and running.

```bash
# 1. Build the image
docker build -t btc-pipeline .

# 2. Run the container
# Windows Command Prompt:
docker run -p 8000:8000 --env GROQ_API_KEY=your_key_here -v "%cd%/data:/app/data" btc-pipeline

# Mac / Linux:
docker run -p 8000:8000 --env GROQ_API_KEY=your_key_here -v $(pwd)/data:/app/data btc-pipeline
```

Then open `index.html` in your browser.

### Option B — Local (without Docker)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create a .env file in the project root
echo GROQ_API_KEY=your_key_here > .env

# 3. Start the server
uvicorn api:app --reload
```

Then open `index.html` in your browser.

### Run tests

```bash
pytest tests/test_processing.py -v
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/latest` | Most recent row from the database |
| GET | `/history` | All rows in ascending order |
| GET | `/metrics` | Aggregated stats over the last 20 points |
| GET | `/insight` | Rule-based market summary |
| GET | `/ai_insight` | Groq LLM market summary (falls back to rule-based) |
| WS | `/ws` | WebSocket — pushes new rows every 5 seconds |

---

## Configuration

All tunable values live in `config.py`:

| Variable | Default | Description |
|---|---|---|
| `SYMBOL` | `BTCUSDT` | Trading pair |
| `FETCH_INTERVAL` | `5` | Seconds between fetches |
| `REQUEST_TIMEOUT` | `5` | Binance API timeout |
| `MA_WINDOW` | `5` | SMA / Bollinger window |
| `EMA_PERIOD` | `5` | EMA span |
| `SPIKE_THRESHOLD` | `1.5` | % change that triggers a spike alert |
| `DB_PATH` | `data/market_data.db` | SQLite file path |

---

## Metrics Reference

| Metric | Calculation | Meaning |
|---|---|---|
| Price Change % | `(new − last) / last × 100` | Momentum since last data point |
| SMA | Mean of last 5 prices | Smoothed trend direction |
| EMA | Exponentially weighted mean | Faster-reacting trend line — useful for short-term signals |
| Volatility | Std deviation of last 5 prices | Market turbulence — high volatility = unstable conditions |
| Upper Bollinger Band | `SMA + 2 × std` | Price above this = potential overbought signal |
| Lower Bollinger Band | `SMA − 2 × std` | Price below this = potential oversold signal |
| Trend | Current SMA vs previous SMA | UPTREND / DOWNTREND / SIDEWAYS |
| Spike | `abs(change) > 1.5%` | Flags sudden large moves |

---

## AI Insight

The dashboard has two insight modes toggled via a button:

- **Rule-based** — instant, no external call, uses the latest metrics to generate a structured summary
- **AI (Groq)** — sends metrics to LLaMA3-8b via the Groq API and returns a plain-English market summary in 2-3 sentences. Falls back to rule-based automatically if the API is unavailable.

Get a free Groq API key at [console.groq.com](https://console.groq.com).

---

## Database Schema

Table: `market_data`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `timestamp` | TEXT | ISO datetime |
| `price` | REAL | BTC/USDT price |
| `price_change` | REAL | % change from previous |
| `moving_avg` | REAL | 5-period SMA |
| `ema` | REAL | 5-period EMA |
| `volatility` | REAL | Std deviation |
| `upper_band` | REAL | Bollinger upper |
| `lower_band` | REAL | Bollinger lower |
| `trend` | TEXT | UPTREND / DOWNTREND / SIDEWAYS |
| `is_spike` | INTEGER | 1 if spike, 0 otherwise |

Storage is lightweight: ~17,000 rows/day ≈ 1–2 MB. SQLite handles this comfortably for years.

---

## Known Quirks

**Trend flips rapidly when price is flat** — when BTC barely moves, tiny EMA floating-point drift causes the trend to oscillate. Fix in `processing.py`:

```python
TREND_THRESHOLD = 0.01

delta = moving_avg - last_ma
if delta > TREND_THRESHOLD:
    trend = "UPTREND"
elif delta < -TREND_THRESHOLD:
    trend = "DOWNTREND"
else:
    trend = "SIDEWAYS"
```

**Price line looks flat in short sessions** — BTC moves very little over 5-second windows. After 30–60 minutes the chart shows meaningful curves.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | No | Enables AI insight mode. Rule-based is used if not set. |

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

Never commit `.env` to git — it is listed in `.dockerignore` and should also be in `.gitignore`.

---

## Running Without the API Server

To collect data in the terminal without starting the web server:

```bash
python main.py
```

---

## Future Ideas

- Deploy backend to Railway or Render for a public live URL
- Replace SQLite with PostgreSQL for multi-instance deployments
- Add a `/alerts` endpoint for recent spike events
- Add a `/export` endpoint to download data as CSV
- Support additional trading pairs via a config switch