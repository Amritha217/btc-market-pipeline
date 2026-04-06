# Unit tests for the processing module.

# Tests cover: price change calculation, moving average, spike detection,
# Bollinger Band ordering, trend direction, and the rule-based insight generator.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from processing import calculate_metrics, generate_ai_insight


#  calculate_metrics 

def test_first_record_returns_zero_change():
    # With no history, price change should be 0
    df = pd.DataFrame(columns=["price", "moving_avg"])
    m  = calculate_metrics(df, 50000)
    assert m["price_change"] == 0.0

def test_price_change_is_correct():
    # 50000 → 51000 = exactly 2% increase
    df = pd.DataFrame({"price": [50000], "moving_avg": [50000]})
    m  = calculate_metrics(df, 51000)
    assert round(m["price_change"], 4) == 2.0

def test_moving_avg_within_window():
    # SMA should be a positive number within the price range
    prices = [100, 102, 101, 103, 105]
    df     = pd.DataFrame({"price": prices, "moving_avg": prices})
    m      = calculate_metrics(df, 107)
    assert m["moving_avg"] > 0

def test_spike_detected():
    # 2% change exceeds the 1.5% threshold — should flag as spike
    df = pd.DataFrame({"price": [50000], "moving_avg": [50000]})
    m  = calculate_metrics(df, 51000)
    assert m["is_spike"] is True

def test_no_spike_on_small_change():
    # 0.2% change is well below the threshold — should not flag
    df = pd.DataFrame({"price": [50000], "moving_avg": [50000]})
    m  = calculate_metrics(df, 50100)
    assert m["is_spike"] is False

def test_upper_band_above_lower_band():
    # Upper Bollinger Band must always be >= lower band
    prices = [100, 102, 98, 101, 103]
    df     = pd.DataFrame({"price": prices, "moving_avg": prices})
    m      = calculate_metrics(df, 104)
    assert m["upper_band"] >= m["lower_band"]

def test_trend_uptrend():
    # Rising SMA should produce UPTREND classification
    df = pd.DataFrame({"price": [100, 101], "moving_avg": [100, 100.5]})
    m  = calculate_metrics(df, 103)
    assert m["trend"] == "UPTREND"


#  generate_ai_insight 

def test_insight_not_enough_data():
    # Fewer than 3 rows should return the "not enough data" message
    df = pd.DataFrame({"price": [100], "moving_avg": [100]})
    assert "Not enough" in generate_ai_insight(df)

def test_insight_returns_string():
    # With sufficient data, insight should return a non-empty string
    rows = [{"price": 50000+i*100, "moving_avg": 50000+i*90,
             "ema": 50000+i*95, "price_change": 0.2,
             "volatility": 50, "upper_band": 51000,
             "lower_band": 49000, "trend": "UPTREND", "is_spike": 0}
            for i in range(5)]
    df     = pd.DataFrame(rows)
    result = generate_ai_insight(df)
    assert isinstance(result, str) and len(result) > 0