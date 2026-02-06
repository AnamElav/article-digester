FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run filesystem is read-only except /tmp
ENV CONCEPT_MEMORY_DIR=/tmp/concept_memory
ENV PROCESSED_ARTICLES_DIR=/tmp/processed_articles

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]