import requests
import time

def test_server():
    print("Testing server connection...")
    
    # Try a few times with delays
    for i in range(5):
        try:
            print(f"Attempt {i+1}: Connecting to http://127.0.0.1:8000/health/")
            response = requests.get('http://127.0.0.1:8000/health/', timeout=5)
            print(f"✅ SUCCESS! Status: {response.status_code}")
            print(f"Response: {response.text[:100]}")
            return True
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed. Retrying in 2 seconds...")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    print("❌ All connection attempts failed")
    return False

if __name__ == "__main__":
    test_server()