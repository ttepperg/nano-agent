# Starting environment
FROM python:3.12-slim

# Where our app lives inside the container.
WORKDIR /app

# Install our dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project in.
COPY . .

# app listens on port 8000
EXPOSE 8000

# Check that the web service is responding
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python3.12", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

# Starts FastAPI when the container runs.
CMD ["uvicorn", "server_ui:app", "--host", "0.0.0.0", "--port", "8000"]
