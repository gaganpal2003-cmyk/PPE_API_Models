# PPE Detection API - Render Deployment Guide
**How to Host & Make Your API Public on Render (render.com)**

This guide provides step-by-step instructions to deploy your PPE Detection API to [Render](https://render.com/) so that any remote client or external computer (regardless of Wi-Fi or local network) can access your API over the public internet with automated HTTPS encryption.

---

## 1. How Render Works
- **Render does not assign a raw static IP address**; instead, it assigns a **Public HTTPS Domain URL** (e.g., `https://ppe-detection-api.onrender.com`).
- A public HTTPS URL is better than a public IP because:
  - It includes free, automatic SSL/TLS encryption (`https://`).
  - Clients won't receive insecure connection warnings.
  - It works seamlessly across firewalls and corporate proxies.

---

## 2. Prerequisites & Preparation

### 2.1 File & Model Sizes Check
- Your YOLO models in `Detection/model/` (`person_detection.pt` and `ppe_detection.pt`) are **~14.5 MB each** (~29 MB total).
- GitHub allows files up to **100 MB**, so you can commit and push these models directly to your repository without needing Git LFS.

### 2.2 Cross-Platform Compatibility Fix (Windows vs Linux)
Render runs on **Ubuntu Linux**. Because models were saved on Windows, PyTorch can raise a `WindowsPath` error on Linux.
To fix this, ensure this patch is included in `Modules/ObjectDetectionModel/objectdetection/ObjectDet.py`:
```python
import platform
import pathlib

if platform.system() != 'Windows':
    pathlib.WindowsPath = pathlib.PosixPath
```

---

## 3. Deployment Methods on Render

### Method A: Docker Deployment (Recommended)
Using Docker guarantees all OpenCV C++ libraries (`libglib2.0`, `libgomp1`) and CPU-optimized PyTorch work without library missing errors.

#### 1. Create a `Dockerfile` in the root of your project:
```dockerfile
FROM python:3.10-slim

# Install system dependencies required for OpenCV and YOLO
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyTorch CPU first (saves ~1.5 GB bandwidth compared to CUDA)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install
COPY requirements_render.txt .
RUN pip install --no-cache-dir -r requirements_render.txt

# Copy project files
COPY . .

# Render exposes the port in the $PORT environment variable
ENV PORT=10000
EXPOSE 10000

# Start command
CMD ["sh", "-c", "uvicorn api_main:app --host 0.0.0.0 --port ${PORT}"]
```

#### 2. Create `requirements_render.txt`:
```txt
fastapi
uvicorn[standard]
python-multipart
python-dotenv
requests
websockets
opencv-python-headless
numpy
pyyaml
tqdm
pandas
seaborn
matplotlib
Pillow
mysql-connector-python
```

---

## 4. Step-by-Step Render Setup

### Step 1: Push Code to GitHub or GitLab
1. Initialize Git (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Prepare PPE API for Render deployment"
   ```
2. Create a repository on [GitHub](https://github.com/new) (can be Private or Public).
3. Push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/ppe-detection-api.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Create a New Web Service on Render
1. Go to [https://dashboard.render.com](https://dashboard.render.com/) and sign in.
2. Click **New +** in the top right corner and select **Web Service**.
3. Choose **Build and deploy from a Git repository** and connect your GitHub account.
4. Select your `ppe-detection-api` repository.

### Step 3: Configure Web Service Settings
- **Name**: `ppe-detection-api` (or any name you choose)
- **Region**: Choose the region closest to you (e.g., *Singapore* or *Frankfurt*)
- **Branch**: `main`
- **Runtime**:
  - If using Docker: Select **Docker**.
  - If using Native Python: Select **Python 3**.
    - *Build Command*: `pip install -r requirements_render.txt`
    - *Start Command*: `uvicorn api_main:app --host 0.0.0.0 --port $PORT`
- **Instance Type**: 
  - *Starter* ($7/mo with 1 CPU, 512MB RAM) or *Standard* ($25/mo with 2GB RAM for faster YOLO CPU inference).
  *(Note: Free tier has 512MB RAM which may run out of memory during YOLO model weight loading).*

### Step 4: Set Environment Variables
Scroll to the **Environment Variables** section and add:
- `VALID_API_KEYS`: `client1_key_123,remote_client_456`
- `PYTHONUNBUFFERED`: `1`

### Step 5: Deploy
Click **Create Web Service**.
Render will build the container, install packages, and load the YOLO model. Once complete, you will see a green **"Live"** badge with your public URL:
```
https://ppe-detection-api.onrender.com
```

---

## 5. Verifying the Deployment

1. **Open Swagger API Docs in your browser**:
   ```
   https://ppe-detection-api.onrender.com/docs
   ```
2. **Test Detection Endpoint via Python from Any Computer**:
   ```python
   import requests

   url = "https://ppe-detection-api.onrender.com/detect"
   headers = {"X-API-Key": "client1_key_123"}
   files = {"file": open("test_image.jpg", "rb")}

   response = requests.post(url, headers=headers, files=files)
   print(response.json())
   ```

---

## 6. What to Give to the External Client
Provide the external client with:
1. **API Endpoint**: `https://ppe-detection-api.onrender.com/detect`
2. **Their Assigned API Key**: `remote_client_456`
3. **Client Script**: The example script in `Client_Integration_Guide.docx`.
