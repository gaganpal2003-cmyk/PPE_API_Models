from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.post("/test-endpoint")
async def receive_webhook(request: Request):
    data = await request.json()
    print(f"\n[Webhook Received] ID: {data.get('id')}")
    print(f"Camera: {data.get('camera_name')}")
    print(f"Time: {data.get('timestamp')}")
    print(f"Detections: {data.get('detections')}")
    
    # Do not print the entire base64 string because it's huge
    snapshot = data.get('snapshot_base64')
    if snapshot:
        print(f"Snapshot received: Yes, {len(snapshot)} chars long")
    else:
        print("Snapshot received: No")
    print("-" * 40)
    
    return {"status": "success", "message": "Webhook received correctly"}

if __name__ == "__main__":
    print("Starting Dummy Webhook Receiver on port 8001...")
    uvicorn.run(app, host="127.0.0.1", port=8001)
