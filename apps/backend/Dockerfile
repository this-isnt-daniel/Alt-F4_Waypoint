FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy optimizer module and pip install it in editable mode just in case
COPY optimization_engine ./optimization_engine
RUN pip install -e ./optimization_engine

# Copy application files
COPY alembic.ini .
COPY migrations ./migrations
COPY app ./app
COPY seed.py .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
