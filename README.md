# Text Processing App (Flask + Celery + Redis)

This repository contains a production-style text processing application built with **Flask**, **Celery**, and **Redis**.

The system is designed to:

* Accept user text uploads via a web interface
* Process text asynchronously without blocking the web server
* Scale horizontally using multiple Celery workers

---

## 🚀 Features

* **Flask API** for accepting text files
* **Celery task queue** for background processing
* **Redis** broker
* **Docker Compose** to orchestrate web, worker, and Redis
* Non-blocking UI: multiple users can submit simultaneously
* NLP models
* - Topic model: https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli
* - Sentiment model: https://router.huggingface.co/hf-inference/models/cardiffnlp/twitter-roberta-base-sentiment-latest
---

## 📁 Project Structure

```
project/
│
├── docker-compose.yml
├── Dockerfile
│
└── app/
    ├── app.py
    ├── tasks.py
    ├── celeryconfig.py
    ├── email_utils.py
    ├── models.py
    └── requirements.txt
```

---

## 🐳 Docker Setup

### docker-compose.yml

```
services:
  redis:
    image: redis:7.0
    container_name: redis
    ports:
      - "6379:6379"

  web:
    build: .
    container_name: textapp_web
    env_file: ./app/.env
    ports:
      - "5000:5000"
    depends_on:
      - redis
    command: python app.py

  worker:
    build: .
    container_name: textapp_worker
    env_file: ./app/.env
    depends_on:
      - redis
    command: celery -A tasks.app worker --loglevel=info
```

### Dockerfile

```
FROM python:3.11-slim
WORKDIR /app
COPY app/ /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]
```

---

## 🧪 Run the App

```bash
docker-compose up --build
```

App will be available at:

```
http://localhost:5000
```

Celery worker logs will stream in the console.

---

## ⚙️ How Text Processing Works

### 1. User uploads text → Flask receives file

### 2. Flask sends job to Celery via Redis

```python
task = process_file.delay(filepath)
```

### 3. Celery worker processes text

* Plain Python

### 4. Result stored or emailed back

---

## 📬 Example Celery Task

```
@app.task
def process_file(path):
    import pandas as pd
    df = pd.read_csv(path)
    return df.shape[0]
```

---

## 🧩 Environment Variables (.env)

```
# Hugging Face
HF_TOKEN=your_token    # set your HF API key or leave empty to always use local fallback
REDIS_URL=redis://redis:6379/0

# Email settings (use app password for Gmail)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email
EMAIL_PASSWORD=your_app_password

```

---

## 📚 Requirements

```
huggingface-hub
pandas
python-dotenv
requests
celery
flask
redis
```

---

## 📝 License

MIT
