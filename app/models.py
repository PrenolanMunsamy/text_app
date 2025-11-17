import os
import requests
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

ZERO_SHOT_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli"
SENTIMENT_URL = "https://router.huggingface.co/hf-inference/models/cardiffnlp/twitter-roberta-base-sentiment-latest"

candidate_topics = ["technology", "food", "science", "finance", "entertainment", "sports"]

# def classify_topic(text):
#     payload = {"inputs": text, "parameters": {"candidate_labels": CANDIDATE_TOPICS}}
#     r = requests.post(ZERO_SHOT_URL, headers=HEADERS, json=payload)
#     data = r.json()
#     return data.get("labels", [data.get("label", "unknown")])[0]

# def analyze_sentiment(text):
#     payload = {"inputs": text}
#     r = requests.post(SENTIMENT_URL, headers=HEADERS, json=payload)
#     data = r.json()
#     if isinstance(data, list) and len(data) > 0:
#         return data[0].get("label", "unknown").replace("LABEL_", "").lower()
#     return "unknown"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# === HELPERS ===
def post_request(url, payload):
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


# === TOPIC CLASSIFICATION ===
def classify_topic(text):
    try:
        payload = {"inputs": text, "parameters": {"candidate_labels": candidate_topics}}
        data = post_request(ZERO_SHOT_URL, payload)

        # router wrapping: [{"outputs": {...}}]
        if isinstance(data, list):
            if "outputs" in data[0]:
                data = data[0]["outputs"]
            else:
                data = data[0]

        # case 1: normal zero-shot => {"labels": [...], "scores": [...]}
        if isinstance(data, dict) and "labels" in data:
            return data["labels"][0]

        # case 2: simplified output => {"label": "food", "score": 0.97}
        if isinstance(data, dict) and "label" in data:
            return data["label"]

        return f"TopicErr: Unexpected format ({list(data.keys()) if isinstance(data, dict) else type(data)})"

    except Exception as e:
        return f"TopicErr: {str(e)[:60]}"

# === SENTIMENT ANALYSIS ===
def analyze_sentiment(text):
    try:
        payload = {"inputs": text}
        data = post_request(SENTIMENT_URL, payload)

        if isinstance(data, list):
            if "outputs" in data[0]:
                data = data[0]["outputs"]
            else:
                data = data[0]

        if isinstance(data, list) and len(data) > 0 and "label" in data[0]:
            label = data[0]["label"]
        elif isinstance(data, dict) and "label" in data:
            label = data["label"]
        else:
            return "SentErr: Unexpected resp format"

        return label.replace("LABEL_", "").lower()
    except Exception as e:
        return f"SentErr: {str(e)[:60]}"
