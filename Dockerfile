# Base Image (Python 3.12 Slim)
FROM python:3.12-slim

# Set Working Directory
WORKDIR /app

# Install System Dependencies (Minimal)
# build-essential for compiling some python libs if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application Code
COPY app ./app
COPY .env .

# Copy Knowledge Base (Critical for "Out of Box" experience)
COPY chroma_db ./chroma_db

# Create non-root user for security
RUN useradd -m spacepedia && chown -R spacepedia:spacepedia /app
USER spacepedia

# Expose Ports (5000: Frontend, 8000: Backend)
EXPOSE 5000 8000

# Default Command (Use --target or override CMD in K8s)
# By default, we launch the help message or backend
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
