import time
from dotenv import load_dotenv
load_dotenv() 

from config import FETCH_INTERVAL, logger
from ingestion import fetch_price
from processing import calculate_metrics
from storage import init_db, load_history, save_record


def run_pipeline():
    init_db()  # create DB and table if they don't exist yet
    logger.info("Pipeline started — fetching every %ds", FETCH_INTERVAL)
    while True:
        try:
            price, timestamp = fetch_price()
            if price is None:
                # Fetch failed — log and retry next cycle
                logger.warning("Skipping this cycle — bad fetch")
                time.sleep(FETCH_INTERVAL)
                continue

            df      = load_history()              # load all past rows for metric calculation
            metrics = calculate_metrics(df, price)
            save_record(timestamp, price, metrics)

        except Exception as e:
            logger.error(f"Pipeline error: {e}")

        time.sleep(FETCH_INTERVAL)


if __name__ == "__main__":
    run_pipeline()