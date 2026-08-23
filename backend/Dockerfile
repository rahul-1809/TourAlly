FROM python:3.13-slim

# Prevent Python from writing .pyc files and buffer outputs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed for compiling certain Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source files
COPY . .

EXPOSE 8000

# Start server using the asyncio loop (incompatibility with uvloop and nest_asyncio)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]
