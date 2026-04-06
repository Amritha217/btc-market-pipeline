# Handles LLM-powered market insight using the Groq API (llama3-8b-8192).


import os
import requests
from config import logger

# Groq's OpenAI-compatible endpoint and model selection
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama3-8b-8192"


def get_ai_insight(metrics: dict) -> str:
    """
    Takes the latest row of market metrics and sends them to Groq's LLM.
    Returns a 2-3 sentence plain-English market summary, or None on failure.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY not set — falling back to rule-based insight")
        return None

    # Extract all relevant fields from the metrics dict
    price      = metrics.get("price",        "N/A")
    trend      = metrics.get("trend",        "N/A")
    change     = metrics.get("price_change", "N/A")
    volatility = metrics.get("volatility",   "N/A")
    ema        = metrics.get("ema",          "N/A")
    ma         = metrics.get("moving_avg",   "N/A")
    upper      = metrics.get("upper_band",   "N/A")
    lower      = metrics.get("lower_band",   "N/A")
    is_spike   = metrics.get("is_spike",     False)

    # Prompt engineered to produce short, direct analyst-style summaries
    prompt = f"""You are a concise market analyst. Given the following real-time BTC/USDT metrics, write a 2-3 sentence human-readable market summary. Be direct, no bullet points, no headers.

Metrics:
- Price: ${price}
- Price Change: {change}%
- Trend: {trend}
- EMA: ${ema}
- Moving Average: ${ma}
- Volatility: {volatility}
- Upper Bollinger Band: ${upper}
- Lower Bollinger Band: ${lower}
- Spike Detected: {is_spike}

Summary:"""

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model":       GROQ_MODEL,
                "messages":    [{"role": "user", "content": prompt}],
                "max_tokens":  120,
                "temperature": 0.4,   # low temperature = focused, less creative output
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        logger.error("Groq API timed out")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to Groq API")
        return None
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return None