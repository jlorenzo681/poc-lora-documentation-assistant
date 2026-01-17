
import requests
import time
import os
import sys

BACKEND_URL = "http://localhost:8000"
TEST_FILE_PATH = "test_document.txt"

def wait_for_backend():
    print("Waiting for backend...")
    for _ in range(30):
        try:
            response = requests.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                print("Backend is up!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    print("Backend failed to start.")
    return False

def test_pipeline():
    # Create dummy file
    with open(TEST_FILE_PATH, "w") as f:
        f.write("This is a test document for verification.")

    try:
        # Upload
        print("Uploading document...")
        with open(TEST_FILE_PATH, "rb") as f:
            files = {"file": (TEST_FILE_PATH, f, "text/plain")}
            data = {"api_key": "dummy", "embedding_type": "HuggingFace (Free)"}
            response = requests.post(f"{BACKEND_URL}/upload", files=files, data=data)
            
        if response.status_code != 200:
            print(f"Upload failed: {response.text}")
            return False

        task_id = response.json()["task_id"]
        print(f"Task ID: {task_id}")

        # Poll status
        print("Polling task status...")
        for _ in range(60):
            response = requests.get(f"{BACKEND_URL}/tasks/{task_id}")
            status_data = response.json()
            status = status_data["status"]
            print(f"Status: {status}")
            
            if status == "SUCCESS":
                print(f"Task succeeded! Result: {status_data.get('result')}")
                return True
            elif status == "FAILURE":
                print(f"Task failed: {status_data.get('error')}")
                return False
            
            time.sleep(1)
            
        print("Task timed out.")
        return False

    finally:
        if os.path.exists(TEST_FILE_PATH):
            os.remove(TEST_FILE_PATH)

if __name__ == "__main__":
    if not wait_for_backend():
        sys.exit(1)
    
    if test_pipeline():
        print("VERIFICATION SUCCESSFUL")
        sys.exit(0)
    else:
        print("VERIFICATION FAILED")
        sys.exit(1)
