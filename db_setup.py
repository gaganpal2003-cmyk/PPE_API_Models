import os
import sys

# Add necessary paths
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from Modules.Live.configRead import ConfigData
from Modules.DbManagerMysql import DatabaseMysqlmgr

def setup_database():
    print("Reading configuration...")
    config = ConfigData(current_dir)
    db_name = config.get_db_name()
    
    print(f"Connecting to MySQL database: {db_name}")
    db_mgr = DatabaseMysqlmgr(db_name)
    
    # 1. Create api_clients table
    create_api_clients_table = """
    CREATE TABLE IF NOT EXISTS api_clients (
        api_key VARCHAR(255) PRIMARY KEY,
        webhook_url TEXT NOT NULL,
        client_name VARCHAR(255)
    );
    """
    
    print("Creating api_clients table...")
    if db_mgr.execute(create_api_clients_table):
        print("Success.")
    else:
        print("Failed to create api_clients table.")
        
    # 2. Create webhook_logs table
    create_webhook_logs_table = """
    CREATE TABLE IF NOT EXISTS webhook_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        api_key VARCHAR(255) NOT NULL,
        camera_name TEXT,
        snapshot_path TEXT,
        detections_json JSON,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status ENUM('pending', 'success', 'failed') DEFAULT 'pending',
        retry_count INT DEFAULT 0,
        FOREIGN KEY (api_key) REFERENCES api_clients(api_key) ON DELETE CASCADE
    );
    """
    
    print("Creating webhook_logs table...")
    if db_mgr.execute(create_webhook_logs_table):
        print("Success.")
    else:
        print("Failed to create webhook_logs table.")

    # 3. Insert a dummy client for testing
    print("Inserting dummy client for testing...")
    insert_dummy = """
    REPLACE INTO api_clients (api_key, webhook_url, client_name) 
    VALUES ('client1_key_123', 'http://127.0.0.1:8001/test-endpoint', 'Test Client 1')
    """
    db_mgr.execute(insert_dummy)
    
    print("Database setup complete!")

if __name__ == "__main__":
    setup_database()
