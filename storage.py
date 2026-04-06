# Handles all SQLite database operations.
# Three fns: initialise the schema, load history, save a new record.
# Each function opens and closes its own connection — safe for multi-threaded use.

import sqlite3
import pandas as pd
from config import DB_PATH, logger


def get_conn():
    """Open and return a new SQLite connection."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    """
    Create the market_data table if it doesn't already exist.
    Called once at pipeline startup.
    """
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS market_data (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp    TEXT,
            price        REAL,
            price_change REAL,
            moving_avg   REAL,
            ema          REAL,
            volatility   REAL,
            upper_band   REAL,
            lower_band   REAL,
            trend        TEXT,
            is_spike     INTEGER   -- stored as 0/1 since SQLite has no boolean type
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialised")


def load_history() -> pd.DataFrame:
    """
    Load all rows from the database in chronological order.
    Returns an empty DataFrame if no data has been collected yet.
    """
    conn = get_conn()
    df   = pd.read_sql("SELECT * FROM market_data ORDER BY id ASC", conn)
    conn.close()
    return df


def save_record(timestamp, price: float, metrics: dict):
    """
    Insert a new row into the database with the current price and all computed metrics.
    """
    conn = get_conn()
    conn.execute("""
        INSERT INTO market_data
            (timestamp, price, price_change, moving_avg, ema,
             volatility, upper_band, lower_band, trend, is_spike)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(timestamp),
        price,
        metrics["price_change"],
        metrics["moving_avg"],
        metrics["ema"],
        metrics["volatility"],
        metrics["upper_band"],
        metrics["lower_band"],
        metrics["trend"],
        int(metrics["is_spike"]),  # convert bool to int for SQLite
    ))
    conn.commit()
    conn.close()
    logger.info(f"Saved record — price: ${price:,.2f} | trend: {metrics['trend']}")