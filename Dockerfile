FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system deps (if you later need them for pandas, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app

# Default envs (can be overridden at runtime)
ENV PYTHONUNBUFFERED=1
ENV DATA_ROOT=/app/data
ENV DB_PATH=/app/roster_tracker.db

# Run the main script
CMD ["python", "-m", "app.main"]
