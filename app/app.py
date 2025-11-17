from flask import Flask, request, jsonify, send_file
import pandas as pd
import os
from app.tasks import process_batch_and_email
from celery.result import AsyncResult

app = Flask(__name__)

# Temporary storage for results
#RESULTS_DIR = "results"
#os.makedirs(RESULTS_DIR, exist_ok=True)
RESULTS_DIR = os.environ.get("RESULTS_DIR", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# === HTML form page ===
@app.route("/", methods=["GET"])
def home():
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
    file = request.files.get("file")
    user_email = request.form.get("email")
    if not file:
        return "No file uploaded", 400

    df = pd.read_csv(file)
    if 'text' not in df.columns:
        return "CSV must have a 'text' column", 400

    # Create a unique batch ID
    batch_id = str(pd.Timestamp.now().timestamp()).replace('.', '')

    # Queue batch with email using apply_async to fix argument error
    process_batch_and_email.apply_async(kwargs={
        "texts": df['text'].tolist(),
        "user_email": user_email,
        "batch_id": batch_id
    })

    return f"Upload successful! Results will be emailed to {user_email} when ready."

# === Download CSV ===
@app.route("/download/<batch_id>", methods=["GET"])
def download(batch_id):
    file_path = os.path.join(RESULTS_DIR, f"{batch_id}.csv")  # use RESULTS_DIR
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_file(file_path, as_attachment=True)


# === Check task result (JSON) ===
@app.route("/result/<task_id>", methods=["GET"])
def get_result(task_id):
    res = AsyncResult(task_id)
    if res.ready():
        return jsonify(res.result)
    else:
        return jsonify({"status": "pending"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
