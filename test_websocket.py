import asyncio
import websockets
import json

async def test_video_stream():
    import urllib.parse
    
    # Use 'r' before the string so backslashes (\) are not treated as special characters
    video_url = r"E:\Adani_Khavda_project\Traning_data\4_PPE_Detection\Input_video\video_04.mp4" 
    api_key = "client1_key_123"
    
    # We must encode the URL (especially Windows paths) so it can safely be sent over the network
    encoded_url = urllib.parse.quote(video_url)
    
    uri = f"ws://127.0.0.1:8000/ws/detect?api_key={api_key}&video_url={encoded_url}"
    
    print(f"Connecting to API and starting video processing for: {video_url}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            
            # Keep listening for results
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                
                if data.get("status") in ["error", "info"]:
                    print(f"Server message: {data['message']}")
                    break
                    
                frame_number = data.get("frame")
                detections = data.get("detections", [])
                
                print(f"--- Frame {frame_number} ---")
                if not detections:
                    print("  No detections")
                for det in detections:
                    print(f"  Detected {det['class']} at {det['bbox']} with {det['confidence']:.2f} confidence")
                    
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed by server.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_video_stream())
