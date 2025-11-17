from celery import Celery, chord
from app.models import classify_topic, analyze_sentiment
from app.email_utils import send_email
from app.logger import logger   # <-- logging added
import os
import pandas as pd

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
RESULTS_DIR = os.getenv("RESULTS_DIR", "/usr/src/app/results")
os.makedirs(RESULTS_DIR, exist_ok=True)

app = Celery(
    "textapp",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# --------------------------
# Process a single text
# --------------------------
@app.task
def process_text(text):
    """Celery task to classify topic + sentiment."""
    logger.info(f"Processing text: {text[:50]!r}...")

    try:
        topic = classify_topic(text)
        sentiment = analyze_sentiment(text)
        logger.info("Completed text classification")
        return {"text": text, "topic": topic, "sentiment": sentiment}

    except Exception as e:
        logger.error(f"Error processing text: {e}", exc_info=True)
        return {"text": text, "error": str(e)}

# --------------------------
# Batch complete callback
# --------------------------
@app.task
def batch_complete(results, user_email=None, batch_id=None):
    """Callback when all tasks in a batch are done."""
    logger.info(
        f"Batch complete triggered – batch_id={batch_id}, "
        f"email={user_email}, results={len(results)}"
    )

    try:
        df = pd.DataFrame(results)

        if batch_id is None:
            batch_id = str(pd.Timestamp.now().timestamp()).replace(".", "")

        file_path = os.path.join(RESULTS_DIR, f"{batch_id}.csv")
        df.to_csv(file_path, index=False)

        logger.info(f"Results saved to {file_path}")

        if user_email:
            subject = "Your Text Analysis Results"
            body = (
                "Hi,\n\nAttached is the CSV file with the topics and sentiment "
                "for your uploaded text.\n\nBest regards."
            )

            try:
                send_email(user_email, subject, body, attachment_path=file_path)
                logger.info(f"Email sent successfully to {user_email}")
            except Exception as e:
                logger.error(f"Failed to send email to {user_email}: {e}", exc_info=True)

        return {"status": "complete", "file": f"{batch_id}.csv"}

    except Exception as e:
        logger.error(f"Error in batch_complete: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

# --------------------------
# Start batch processing
# --------------------------
@app.task
def process_batch_and_email(texts, user_email=None, batch_id=None):
    logger.info(
        f"Queuing batch – batch_id={batch_id}, email={user_email}, "
        f"num_texts={len(texts)}"
    )

    try:
        chord(process_text.s(text) for text in texts)(
            batch_complete.s(user_email=user_email, batch_id=batch_id)
        )
        logger.info(f"Batch {batch_id} successfully queued")
        return {"status": "batch_queued", "num_texts": len(texts)}

    except Exception as e:
        logger.error(f"Error queuing batch: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
