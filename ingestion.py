# Responsible for fetching the live BTC/USDT price from Binance.
# Returns (price, timestamp) on success or (None, None) on any failure,
# so the pipeline can skip the cycle cleanly without crashing.

import requests
from datetime import datetime
from config import BINANCE_URL, REQUEST_TIMEOUT, logger


def fetch_price():
    """
    Make a GET request to the Binance ticker endpoint.
    Returns:
        (float, datetime) on success
        (None, None)      on timeout, connection error, or bad response
    """
    try:
        response = requests.get(BINANCE_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # raises on 4xx / 5xx status codes
        data  = response.json()
        price = float(data["price"])
        ts    = datetime.now()
        logger.info(f"Fetched price: ${price:,.2f}")
        return price, ts

    except requests.exceptions.Timeout:
        logger.error("Binance API timed out")
        return None, None

    except requests.exceptions.ConnectionError:
        logger.error("No internet connection")
        return None, None

    except Exception as e:
        logger.error(f"Unexpected fetch error: {e}")
        return None, None