import os
import time
import requests
from dotenv import load_dotenv

# === Load token ===
load_dotenv()
API_TOKEN = os.getenv("HF_API_TOKEN")
if not API_TOKEN:
    raise ValueError("Add HF_API_TOKEN to .env file!")

# === API URLs ===
ZERO_SHOT_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli"
SENTIMENT_URL = "https://router.huggingface.co/hf-inference/models/cardiffnlp/twitter-roberta-base-sentiment-latest"

headers = {"Authorization": f"Bearer {API_TOKEN}"}

# === DATA ===
dummy_texts = [
    "I love this new smartphone! The camera is amazing and battery lasts all day.",
    "The service at the restaurant was terrible, food was cold and overpriced.",
    "Scientists discover new exoplanet that could support life.",
    "Stock market crashes due to inflation fears.",
    "This movie was boring and predictable, waste of time.",
    "Great team effort! We won the championship after an intense match."
]

candidate_topics = ["technology", "food", "science", "finance", "entertainment", "sports"]

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

# === MAIN ===
print("Analyzing text with Hugging Face Inference API\n")
print(f"{'Text':<70} | {'Topic':<12} | {'Sentiment'}")
print("-" * 100)

for i, text in enumerate(dummy_texts):
    topic = classify_topic(text)
    sentiment = analyze_sentiment(text)
    print(f"{text[:68]:<70} | {topic:<12} | {sentiment}")
    time.sleep(1.5)
