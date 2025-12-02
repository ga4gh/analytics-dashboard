FROM python:3.13-bookworm AS base

# Fail fast if any command errors
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

############################  System dependencies
RUN apt-get update         \
 && apt-get install -y --no-install-recommends build-essential \
 && apt-get clean          \
 && rm -rf /var/lib/apt/lists/*

############################  Set work directory
WORKDIR /app

############################  Copy Python deps separately for better caching
COPY requirements.txt .

# Upgrade pip first, then install deps
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

############################  Copy application code
COPY . .

############################  Expose API port
EXPOSE 8000

############################  Start the FastAPI server
CMD ["python", "-m", "src.main"]
