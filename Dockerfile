# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy app code
COPY app/ /app/

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Default command (Flask dev server)
CMD ["python", "app.py"]
