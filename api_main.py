import os
import sys
import cv2
import numpy as np
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Security, WebSocket, WebSocketDisconnect, Query
from fastapi.security.api_key import APIKeyHeader
import asyncio
import json
from dotenv import load_dotenv

# Add necessary paths
yolo_root = os.path.join(os.getcwd(), 'Modules', 'ObjectDetectionModel', 'objectdetection')
if yolo_root not in sys.path:
    sys.path.insert(0, yolo_root)

# Import existing model logic
from Modules.Live.configRead import ConfigData
# pyrefly: ignore [missing-import]
from ObjectDet import get_model, predict_api, get_profile
# pyrefly: ignore [missing-import]
from utils.augmentations import letterbox

# Load environment variables
load_dotenv()

app = FastAPI(title="PPE Detection API")

# Setup Authentication
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_valid_api_keys():
    keys_str = os.getenv("VALID_API_KEYS", "")
    return [k.strip() for k in keys_str.split(",") if k.strip()]

async def get_api_key(api_key_header: str = Security(api_key_header)):
    valid_keys = get_valid_api_keys()
    if not valid_keys:
        # If no keys are configured, deny all for security, or allow for testing. Let's deny.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API keys are not configured on the server."
        )
    if api_key_header in valid_keys:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate API KEY"
        )

# Global variables to hold the loaded model
app_state = {}

@app.on_event("startup")
async def startup_event():
    print("Initializing PPE Detection Model...")
    config = ConfigData(os.getcwd())
    
    # Load the PPE model specifically to detect helmets and vests
    model_path = config.get_ppe_model_path()
    coco_path = config.get_coco_path()
    
    print(f"Loading PPE model from: {model_path}")
    device, model = get_model(model_path, coco_path)
    
    app_state["model"] = model
    app_state["device"] = device
    app_state["names"] = model.module.names if hasattr(model, 'module') else model.names
    app_state["threshold"] = float(config.get_threshold())
    app_state["config"] = config
    print("Model initialized successfully!")

import uuid
from Modules.DbManagerMysql import DatabaseMysqlmgr

def log_detection_if_needed(api_key: str, source_name: str, im0s, detections, config: ConfigData):
    if not detections:
        return
        
    imp_ppe_str = config.get_imp_ppe_name()
    imp_ppe = [x.strip() for x in imp_ppe_str.split(",")] if imp_ppe_str else ["no_helmet", "no_vest"]
    
    # Check if any detected class is in the important PPE list (violations)
    has_violation = any(det.get("class") in imp_ppe for det in detections)
    
    if has_violation:
        try:
            # 1. Save snapshot
            snapshot_dir = os.path.join(os.getcwd(), "snapshots")
            os.makedirs(snapshot_dir, exist_ok=True)
            snapshot_filename = f"snapshot_{uuid.uuid4().hex}.jpg"
            snapshot_path = os.path.join(snapshot_dir, snapshot_filename)
            cv2.imwrite(snapshot_path, im0s)
            
            # 2. Insert into webhook_logs database
            db_mgr = DatabaseMysqlmgr(config.get_db_name())
            query = """
            INSERT INTO webhook_logs (api_key, camera_name, snapshot_path, detections_json)
            VALUES (%s, %s, %s, %s)
            """
            data = (api_key, source_name, snapshot_path, json.dumps(detections))
            db_mgr.insert(query, data)
            print(f"Logged violation to database for {source_name}")
        except Exception as e:
            print(f"Failed to log detection: {e}")

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "PPE Detection API",
        "documentation": "/docs"
    }

@app.post("/detect")
async def detect_ppe(file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    # Read image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    im0s = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if im0s is None:
        raise HTTPException(status_code=400, detail="Could not parse image.")

    # Prepare image for YOLO (resize, pad, BGR to RGB, HWC to CHW)
    img_size = 640
    stride = int(app_state["model"].stride.max()) if hasattr(app_state["model"].stride, 'max') else int(app_state["model"].stride)
    im = letterbox(im0s, img_size, stride=stride, auto=True)[0]
    im = im.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
    im = np.ascontiguousarray(im)

    dt = get_profile(app_state["device"])
    
    # Run prediction
    try:
        detections = predict_api(
            model=app_state["model"],
            names=app_state["names"],
            dt=dt,
            im=im,
            im0s=im0s,
            thres_h=app_state["threshold"]
        )
        
        # Log to database if violations found
        log_detection_if_needed(api_key, "image_upload", im0s, detections, app_state["config"])
        
    except Exception as e:
        print(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail="Error processing image.")

    return {"status": "success", "detections": detections}

@app.websocket("/ws/detect")
async def websocket_detect(websocket: WebSocket, api_key: str = Query(...), video_url: str = Query(...)):
    await websocket.accept()
    
    valid_keys = get_valid_api_keys()
    if api_key not in valid_keys:
        await websocket.send_json({"status": "error", "message": "Invalid API Key"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    cap = cv2.VideoCapture(video_url)
    if not cap.isOpened():
        await websocket.send_json({"status": "error", "message": f"Could not open video stream: {video_url}"})
        await websocket.close()
        return
        
    frame_count = 0
    process_every_n_frames = 5  # Process 1 out of 5 frames to save resources
    
    try:
        while True:
            ret, im0s = cap.read()
            if not ret:
                await websocket.send_json({"status": "info", "message": "Video stream ended"})
                break
                
            frame_count += 1
            if frame_count % process_every_n_frames != 0:
                continue
                
            # Prepare image for YOLO
            img_size = 640
            stride = int(app_state["model"].stride.max()) if hasattr(app_state["model"].stride, 'max') else int(app_state["model"].stride)
            im = letterbox(im0s, img_size, stride=stride, auto=True)[0]
            im = im.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
            im = np.ascontiguousarray(im)

            dt = get_profile(app_state["device"])
            
            # Run prediction
            detections = predict_api(
                model=app_state["model"],
                names=app_state["names"],
                dt=dt,
                im=im,
                im0s=im0s,
                thres_h=app_state["threshold"]
            )
            
            # Log to database if violations found
            log_detection_if_needed(api_key, video_url, im0s, detections, app_state["config"])
            
            # Send results back
            await websocket.send_json({
                "frame": frame_count,
                "detections": detections
            })
            
            # Allow other async tasks to run
            await asyncio.sleep(0.01)
            
    except WebSocketDisconnect:
        print(f"Client disconnected from {video_url}")
    except Exception as e:
        print(f"Error in websocket loop: {e}")
        try:
            await websocket.send_json({"status": "error", "message": str(e)})
        except:
            pass
    finally:
        cap.release()
        try:
            await websocket.close()
        except:
            pass
