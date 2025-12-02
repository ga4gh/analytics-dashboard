FROM python:3.13-bookworm AS base

# Fail fast if any command errors
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

############################
# System dependencies
############################
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

############################
# Set work directory
############################
WORKDIR /app

############################
# Install Python dependencies
############################
COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

############################
# Copy application code
############################
COPY . .

############################
# Expose API port
############################
EXPOSE 8000

############################
# Start FastAPI (production-friendly)
############################
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]