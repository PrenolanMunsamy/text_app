from flask import Flask, request, jsonify, send_file
import pandas as pd
import os
from app.tasks import process_batch_and_email
from celery.result import AsyncResult
from app.logger import logger  # make sure logger.py uses logs/ folder

app = Flask(__name__)

# === Results directory (separate from logs) ===
RESULTS_DIR = os.environ.get("RESULTS_DIR", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
logger.info(f"Results directory set to: {RESULTS_DIR}")

# === HTML form page ===
@app.route("/", methods=["GET"])
def home():
    logger.info("Home page requested")
    return """
    <h1>Text Analysis App</h1>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <label>Upload CSV (must have a 'text' column):</label><br>
        <input type="file" name="file"><br><br>
        <label>Your Email:</label><br>
        <input type="email" name="email" required><br><br>
        <input type="submit" value="Upload & Analyze">
    </form>
    """

# === Upload CSV and process texts ===
@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files.get("file")
        user_email = request.form.get("email")

        if not file:
            logger.warning("Upload attempted with no file")
            return "No file uploaded", 400

        df = pd.read_csv(file)
        if 'text' not in df.columns:
            logger.warning("CSV upload missing 'text' column")
            return "CSV must have a 'text' column", 400

        # Create a unique batch ID
        batch_id = str(pd.Timestamp.now().timestamp()).replace('.', '')
        logger.info(f"Received batch {batch_id} from {user_email}, {len(df)} rows")

        # Queue batch with email using apply_async
        process_batch_and_email.apply_async(kwargs={
            "texts": df['text'].tolist(),
            "user_email": user_email,
            "batch_id": batch_id
        })
        logger.info(f"Batch {batch_id} queued for processing")

        return f"Upload successful! Results will be emailed to {user_email} when ready."

    except Exception as e:
        logger.error(f"Error in upload route: {e}", exc_info=True)
        return "Internal server error", 500

# === Download CSV ===
@app.route("/download/<batch_id>", methods=["GET"])
def download(batch_id):
    try:
        file_path = os.path.join(RESULTS_DIR, f"{batch_id}.csv")
        if not os.path.exists(file_path):
            logger.warning(f"Download attempted for missing batch {batch_id}")
            return "File not found", 404
        logger.info(f"Batch {batch_id} downloaded")
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Error in download route for batch {batch_id}: {e}", exc_info=True)
        return "Internal server error", 500

# === Check task result (JSON) ===
@app.route("/result/<task_id>", methods=["GET"])
def get_result(task_id):
    try:
        res = AsyncResult(task_id)
        if res.ready():
            logger.info(f"Task {task_id} completed")
            return jsonify(res.result)
        else:
            logger.info(f"Task {task_id} still pending")
            return jsonify({"status": "pending"})
    except Exception as e:
        logger.error(f"Error checking task {task_id}: {e}", exc_info=True)
        return "Internal server error", 500

if __name__ == "__main__":
    logger.info("Starting Flask app")
    app.run(host="0.0.0.0", port=5000, debug=True)
