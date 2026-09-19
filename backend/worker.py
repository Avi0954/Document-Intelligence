import sys
import os
import time
import signal
import logging

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.services.redis_queue import redis_queue_service
from app.services.document_service import document_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Worker] %(message)s"
)
logger = logging.getLogger("worker")

running = True

def handle_shutdown(signum, frame):
    global running
    logger.info("Shutdown signal received. Stopping worker loop gracefully...")
    running = False

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def run_worker():
    logger.info("Starting Pragati Bharati Document Processing Worker...")
    logger.info("Listening for document jobs on Redis queue 'docu_intel:jobs'...")

    while running:
        try:
            document_id = redis_queue_service.dequeue_document_processing(timeout=3)
            if not document_id:
                continue

            logger.info(f"Processing job for document_id: {document_id}")

            # Each worker job uses its own dedicated DB session
            db = SessionLocal()
            try:
                document_service.process_document_pipeline(db, document_id)
                logger.info(f"Successfully processed document_id: {document_id}")
            except Exception as e:
                logger.error(f"Failed processing document_id {document_id}: {str(e)}")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Unexpected error in worker loop: {str(e)}")
            time.sleep(1)

    logger.info("Worker stopped.")

if __name__ == "__main__":
    run_worker()
