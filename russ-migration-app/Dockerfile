FROM python:3.12-slim


WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y build-essential libxml2-dev libxslt-dev && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /app/uploads /app/outputs /app/backend /app/worker /app/frontend \
    && chmod -R 777 /app/uploads /app/outputs

# Copy code
COPY . /app

# Install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
RUN pip install --no-cache-dir beautifulsoup4 lxml pandas openpyxl matplotlib python-pptx fastapi uvicorn

# Expose port
EXPOSE 8000

# Start FastAPI
CMD ["python3", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]

