# Central place for all constants and configuration.
# Changing a value here affects the entire pipeline .

import logging

# Data source
SYMBOL          = "BTCUSDT"
BINANCE_URL     = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
FETCH_INTERVAL  = 5   # seconds between each price fetch
REQUEST_TIMEOUT = 5   # seconds before giving up on a Binance request

# Storage
DB_PATH = "data/market_data.db"  # SQLite file, auto-created on first run

#  Indicator windows
MA_WINDOW  = 5   # number of periods for Simple Moving Average and Bollinger Bands
EMA_PERIOD = 5   # span for Exponential Moving Average

#  Spike detection 
SPIKE_THRESHOLD = 1.5   # price change % that triggers a spike alert on the dashboard

#  Logging 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)