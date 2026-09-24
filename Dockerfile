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

# Starts FastAPI when the container runs.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
