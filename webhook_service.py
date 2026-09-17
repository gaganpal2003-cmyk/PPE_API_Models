import os
import sys
import time
import json
import base64
import requests

# Add necessary paths
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from Modules.Live.configRead import ConfigData
from Modules.DbManagerMysql import DatabaseMysqlmgr

def get_webhook_url(db_mgr, api_key):
    # Fetch webhook URL for this API key
    query = f"SELECT webhook_url FROM api_clients WHERE api_key = '{api_key}'"
    result = db_mgr.select(query)
    if result and len(result) > 0:
        return result[0][0]
    return None

def update_status(db_mgr, record_id, status, increment_retry=False):
    if increment_retry:
        query = "UPDATE webhook_logs SET status = %s, retry_count = retry_count + 1 WHERE id = %s"
    else:
        query = "UPDATE webhook_logs SET status = %s WHERE id = %s"
    
    # We use the insert method because it supports parameterized queries (cursor.execute(query, data))
    db_mgr.insert(query, (status, record_id))

def process_pending_webhooks():
    config = ConfigData(current_dir)
    db_name = config.get_db_name()
    db_mgr = DatabaseMysqlmgr(db_name)
    
    print("Starting Webhook Worker Service...")
    print(f"Monitoring database '{db_name}' for pending webhook events...")
    
    while True:
        try:
            # Fetch pending or failed (with retry < 3) logs
            query = "SELECT id, api_key, camera_name, snapshot_path, detections_json, timestamp FROM webhook_logs WHERE status = 'pending' OR (status = 'failed' AND retry_count < 3)"
            records = db_mgr.select(query)
            
            for record in records:
                log_id = record[0]
                api_key = record[1]
                camera_name = record[2]
                snapshot_path = record[3]
                detections_json = record[4]
                timestamp_str = str(record[5])
                
                webhook_url = get_webhook_url(db_mgr, api_key)
                if not webhook_url:
                    print(f"[Log {log_id}] No webhook URL found for api_key: {api_key}. Marking failed.")
                    update_status(db_mgr, log_id, "failed")
                    continue
                
                print(f"[Log {log_id}] Processing webhook for {camera_name} -> {webhook_url}")
                
                # Encode snapshot
                encoded_image = ""
                if snapshot_path and os.path.exists(snapshot_path):
                    with open(snapshot_path, "rb") as image_file:
                        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                        
                payload = {
                    "id": log_id,
                    "camera_name": camera_name,
                    "timestamp": timestamp_str,
                    "detections": json.loads(detections_json) if detections_json else [],
                    "snapshot_base64": encoded_image
                }
                
                try:
                    response = requests.post(webhook_url, json=payload, timeout=10)
                    if response.status_code in [200, 201, 202]:
                        print(f"[Log {log_id}] Webhook delivered successfully!")
                        update_status(db_mgr, log_id, "success")
                        
                        # Optionally delete the snapshot file to save space after success
                        if os.path.exists(snapshot_path):
                            os.remove(snapshot_path)
                    else:
                        print(f"[Log {log_id}] Webhook failed with status {response.status_code}")
                        update_status(db_mgr, log_id, "failed", increment_retry=True)
                except Exception as e:
                    print(f"[Log {log_id}] Error sending webhook: {e}")
                    update_status(db_mgr, log_id, "failed", increment_retry=True)
                    
        except Exception as e:
            print(f"Error in webhook loop: {e}")
            
        time.sleep(3)  # Wait 3 seconds before checking again

if __name__ == "__main__":
    process_pending_webhooks()
