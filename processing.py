# Core analytics engine. Takes raw price data and produces trading indicators.
# All metric logic is isolated here so it can be tested independently.

import pandas as pd
from config import MA_WINDOW, EMA_PERIOD, SPIKE_THRESHOLD, logger


def calculate_metrics(df: pd.DataFrame, new_price: float) -> dict:
    """
    Given the full price history and the latest price, compute all indicators.

    Returns a dict containing:
        price_change, moving_avg, ema, volatility,
        upper_band, lower_band, trend, is_spike
    """
    # Combine history with the new price for rolling calculations
    prices = df["price"].tolist() + [new_price]
    series = pd.Series(prices)

    #  Price change % 
    # How much the price moved since the last recorded data point
    if len(df) == 0:
        price_change = 0.0  # no previous data to compare against
    else:
        last_price   = df.iloc[-1]["price"]
        price_change = ((new_price - last_price) / last_price) * 100



    #  Simple Moving Average (SMA) 
    # Average of the last MA_WINDOW prices — smooths out short-term noise
    window     = prices[-MA_WINDOW:]
    moving_avg = sum(window) / len(window)



    #  Exponential Moving Average (EMA) 
    # Weights recent prices more heavily than SMA — reacts faster to moves
    ema = series.ewm(span=EMA_PERIOD, adjust=False).mean().iloc[-1]

    #  Volatility 
    # Standard deviation of the last window — higher = more turbulent market
    volatility = pd.Series(prices[-MA_WINDOW:]).std() if len(prices) >= 2 else 0.0



    #  Bollinger Bands 
    # Upper/lower bands = SMA ± 2 standard deviations.
    # Price outside bands signals potential overbought / oversold conditions.
    std        = volatility
    upper_band = moving_avg + (2 * std)
    lower_band = moving_avg - (2 * std)



    #  Trend classification 
    # Compare current SMA to the previous SMA to determine direction
    if len(df) >= 2:
        last_ma = df.iloc[-1]["moving_avg"] if "moving_avg" in df.columns else moving_avg
        if moving_avg > last_ma:
            trend = "UPTREND"
        elif moving_avg < last_ma:
            trend = "DOWNTREND"
        else:
            trend = "SIDEWAYS"
    else:
        trend = "SIDEWAYS"  # not enough history to determine direction

    #  Spike detection 
    # Flag any sudden large price move that exceeds the configured threshold
    is_spike = abs(price_change) > SPIKE_THRESHOLD

    metrics = {
        "price_change": round(price_change, 4),
        "moving_avg":   round(moving_avg,   2),
        "ema":          round(ema,           2),
        "volatility":   round(volatility,    4),
        "upper_band":   round(upper_band,    2),
        "lower_band":   round(lower_band,    2),
        "trend":        trend,
        "is_spike":     is_spike,
    }

    logger.info(f"Metrics → MA: ${moving_avg:,.2f} | EMA: ${ema:,.2f} | Trend: {trend} | Spike: {is_spike}")
    return metrics


def generate_ai_insight(df: pd.DataFrame) -> str:
    """
    Rule-based market summary using the latest metrics.
    Used as the default insight mode and as a fallback when Groq is unavailable.
    """
    if len(df) < 3:
        return "Not enough data to generate insight."

    latest       = df.iloc[-1]
    price_change = latest.get("price_change", 0)
    trend        = latest.get("trend",        "SIDEWAYS")
    volatility   = latest.get("volatility",   0)
    price        = latest.get("price",        0)
    upper_band   = latest.get("upper_band",   price)
    lower_band   = latest.get("lower_band",   price)

    #  Momentum 
    if price_change > 1:
        momentum = "Strong bullish momentum"
    elif price_change > 0:
        momentum = "Mild bullish momentum"
    elif price_change < -1:
        momentum = "Strong bearish momentum"
    else:
        momentum = "Mild bearish momentum"

    #  Volatility comment 
    if volatility > 200:
        vol_comment = "High volatility — market is unstable."
    elif volatility > 50:
        vol_comment = "Moderate volatility."
    else:
        vol_comment = "Low volatility — market is calm."

    #  Bollinger Band position comment 
    if price > upper_band:
        band_comment = "Price is above the upper Bollinger band — potential overbought signal."
    elif price < lower_band:
        band_comment = "Price is below the lower Bollinger band — potential oversold signal."
    else:
        band_comment = "Price is within normal Bollinger band range."

    return f"{momentum} | {trend} | {vol_comment} {band_comment}"