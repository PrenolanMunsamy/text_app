from celery import Celery, chord
from models import classify_topic, analyze_sentiment
from email_utils import send_email
import os
import pandas as pd

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
RESULTS_DIR = os.getenv("RESULTS_DIR", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

app = Celery(
    "textapp",
    broker=REDIS_URL,
    backend=REDIS_URL
)

@app.task
def process_text(text):
    """Celery task to classify topic + sentiment."""
    try:
        topic = classify_topic(text)
        sentiment = analyze_sentiment(text)
        return {"text": text, "topic": topic, "sentiment": sentiment}
    except Exception as e:
        return {"text": text, "error": str(e)}

@app.task
def batch_complete(results, user_email=None, batch_id=None):
    """Callback when all tasks in a batch are done."""
    df = pd.DataFrame(results)
    
    if batch_id is None:
        batch_id = str(pd.Timestamp.now().timestamp()).replace(".", "")
    file_path = os.path.join(RESULTS_DIR, f"{batch_id}_full.csv")
    df.to_csv(file_path, index=False)

    if user_email:
        subject = "Your Text Analysis Results"
        body = "Hi,\n\nAttached is the CSV file with the topics and sentiment for your uploaded text.\n\nBest regards."
        send_email(user_email, subject, body, attachment_path=file_path)
    
    return {"status": "email_sent", "file": file_path}

@app.task
def process_batch_and_email(texts, user_email=None, batch_id=None):
    """Queue a batch of texts and send email when all done."""
    chord(process_text.s(text) for text in texts)(
        batch_complete.s(user_email=user_email, batch_id=batch_id)
    )
    return {"status": "batch_queued", "num_texts": len(texts)}
