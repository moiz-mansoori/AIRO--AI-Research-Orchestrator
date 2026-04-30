# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files
# and to ensure stdout is logged immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install system dependencies required for WeasyPrint (PDF generation) and compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libffi-dev \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy requirement files first to leverage Docker layer caching
COPY core.txt ml.txt agents.txt requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create necessary ephemeral directories that the agents expect to exist
RUN mkdir -p data/raw data/processed data/splits models reports logs mlruns

# Expose the port (Render will inject the PORT environment variable)
EXPOSE $PORT

# Command to run the FastAPI application
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
