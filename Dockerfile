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

# Copy Knowledge Base (Critical for "Out of Box" experience)
COPY chroma_db ./chroma_db

# Copy startup script
COPY start.sh .

# Create non-root user for security (Required by HF Spaces to be consistently 1000)
RUN useradd -m -u 1000 user

# Fix permissions: Give user ownership of the application directory
RUN chown -R user:user /app

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose Ports (7860 for HF Spaces)
EXPOSE 7860

# Default Command
CMD ["bash", "start.sh"]
