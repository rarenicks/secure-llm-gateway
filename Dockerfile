# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TARGET_LLM_URL="http://host.docker.internal:11434/v1/chat/completions"
ENV WHYLOGS_NO_ANALYTICS="True"

# Set work directory
WORKDIR /app

# Install system dependencies (if any needed for sentence-transformers/build)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_lg

# Copy project
COPY . .

# Create a non-root user and switch to it
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
