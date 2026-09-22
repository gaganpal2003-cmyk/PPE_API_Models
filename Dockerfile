FROM python:3.10-slim

# Install system dependencies required for OpenCV and YOLO
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install CPU-only PyTorch first (reduces image size significantly and prevents CUDA bloat)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install python packages
COPY requirements_render.txt .
RUN pip install --no-cache-dir -r requirements_render.txt

# Copy application source code and models
COPY . .

# Render exposes the port in the $PORT environment variable (default: 10000)
ENV PORT=10000
EXPOSE 10000

# Launch Uvicorn bound to 0.0.0.0 and dynamic $PORT
CMD ["sh", "-c", "uvicorn api_main:app --host 0.0.0.0 --port ${PORT}"]
