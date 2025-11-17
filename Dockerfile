# Base image
FROM python:3.11-slim

# Set working directory to project root
WORKDIR /usr/src/app

# Copy requirements first for better caching
COPY requirements.txt ./

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the app folder
COPY app/ ./app

# Expose Flask port
EXPOSE 5000

# Default command (Flask dev server)
CMD ["python", "app/app.py"]
