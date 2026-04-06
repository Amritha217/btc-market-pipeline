# FastAPI application — the main entry point for the project.

#   1. Starts the data pipeline in a background thread on launch
#   2. Broadcasts the latest market row to all WebSocket clients every 5s
#   3. Serves REST endpoints for the frontend dashboard
#   4. Serves both rule-based and Groq AI insight endpoints

import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import asyncio
import time
import threading

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()  

from config import FETCH_INTERVAL, logger
from processing import calculate_metrics, generate_ai_insight
from storage import init_db, load_history, save_record
from ingestion import fetch_price
from ai_integration import get_ai_insight

app = FastAPI()

# Allow the frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#  Background pipeline 
# Every FETCH_INTERVAL seconds: fetch price → compute metrics → save to DB.

def run_pipeline():
    init_db()
    logger.info("Background pipeline started")
    while True:
        try:
            price, timestamp = fetch_price()
            if price is None:
                # Binance call failed — skip this cycle and retry next interval
                time.sleep(FETCH_INTERVAL)
                continue
            df      = load_history()
            metrics = calculate_metrics(df, price)
            save_record(timestamp, price, metrics)
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
        time.sleep(FETCH_INTERVAL)

threading.Thread(target=run_pipeline, daemon=True).start()


#  WebSocket manager 
# Tracks all active browser connections and broadcasts new data to each one.

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info(f"WebSocket connected — total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        # Iterate over a copy so we can safely remove broken connections mid-loop
        for ws in list(self.active):
            try:
                await ws.send_json(data)
            except Exception:
                self.active.remove(ws)

manager = ConnectionManager()


async def broadcast_loop():
    """Push the latest DB row to all connected clients every FETCH_INTERVAL seconds."""
    while True:
        await asyncio.sleep(FETCH_INTERVAL)
        try:
            df = load_history()
            if not df.empty:
                await manager.broadcast(df.iloc[-1].to_dict())
        except Exception as e:
            logger.error(f"Broadcast error: {e}")

@app.on_event("startup")
async def startup():
    # Start the broadcast loop as a background async task alongside the server
    asyncio.create_task(broadcast_loop())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Accept and hold open WebSocket connections from the dashboard."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)


#  REST endpoints 

@app.get("/latest")
def get_latest():
    """Return the single most recent data row."""
    df = load_history()
    if df.empty:
        return []
    return df.tail(1).to_dict(orient="records")

@app.get("/history")
def get_history():
    """Return all stored rows in chronological order. Used to populate the chart on page load."""
    return load_history().to_dict(orient="records")

@app.get("/metrics")
def get_metrics():
    """Return aggregated statistics over the last 20 data points."""
    df = load_history().tail(20)
    if df.empty:
        return {"error": "No data"}
    return {
        "avg_price":      round(df["price"].mean(),      2),
        "max_price":      round(df["price"].max(),       2),
        "min_price":      round(df["price"].min(),       2),
        "avg_ema":        round(df["ema"].mean(),        2),
        "avg_volatility": round(df["volatility"].mean(), 4),
        "latest_trend":   df.iloc[-1]["trend"],
        "data_points":    len(df),
    }

@app.get("/insight")
def get_insight():
    """Rule-based market insight — instant, no external API call."""
    df = load_history()
    return {"insight": generate_ai_insight(df)}

@app.get("/ai_insight")
def get_ai_insight_endpoint():
    """
    LLM-powered insight via Groq.
    If the Groq call fails or the key is missing, falls back to rule-based insight
    and sets source accordingly so the frontend can show a warning.
    """
    df = load_history()
    if df.empty:
        return {"insight": "No data available yet.", "source": "none"}

    latest    = df.iloc[-1].to_dict()
    ai_result = get_ai_insight(latest)

    if ai_result:
        return {"insight": ai_result, "source": "groq"}

    # Groq unavailable — fall back silently
    return {"insight": generate_ai_insight(df), "source": "rule-based"}