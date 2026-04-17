"""
run_pipeline.py — Master orchestrator for the full data pipeline
"""

import time
import logging
import os
import subprocess

# Secure logs directory
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


STEPS = [
    "scraper/amazon_scraper.py",
    "scraper/flipkart_scraper.py",
    "scraper/adlers_scraper.py",
    "data/merge.py",
    "processing/run_cleaning.py",
    "processing/scoring.py",
    "database/db.py",
]


def run_step(script_path):
    """Run a single pipeline step with timing and error handling."""
    start = time.time()
    logger.info(f"Starting {script_path}...")
    print(f"\n▶ Running {script_path}...")

    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            check=True,
        )
        duration = round(time.time() - start, 2)
        logger.info(f"Completed {script_path} in {duration}s")
        print(f"  ✅ Done in {duration}s")

        if result.stdout.strip():
            logger.info(f"Output: {result.stdout.strip()}")

        if result.stderr.strip():
            logger.warning(f"Warnings from {script_path}: {result.stderr.strip()}")

    except subprocess.CalledProcessError as e:
        duration = round(time.time() - start, 2)
        logger.error(f"FAILED {script_path} after {duration}s — {e.stderr}")
        print(f"  ❌ Failed after {duration}s (see logs/app.log)")


def run_all():
    total_start = time.time()
    logger.info("=" * 60)
    logger.info("PIPELINE STARTED")
    logger.info("=" * 60)
    print("\n🚀 Pipeline started\n" + "=" * 40)

    for step in STEPS:
        if os.path.exists(step):
            run_step(step)
        else:
            logger.warning(f"Script not found, skipping: {step}")
            print(f"  ⚠️ Skipped (not found): {step}")

    total_duration = round(time.time() - total_start, 2)
    
    if total_duration > 120:
        logger.warning(f"Pipeline running longer than expected: {total_duration}s")
        
    logger.info(f"PIPELINE COMPLETED in {total_duration}s")
    logger.info("=" * 60)

    print("\n" + "=" * 40)
    print(f"Pipeline completed successfully in {total_duration}s")
    print("Check logs/app.log for detailed metrics")


if __name__ == "__main__":
    run_all()
