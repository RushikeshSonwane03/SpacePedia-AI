
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

def print_result(test_name, success, details=""):
    symbol = "✅" if success else "❌"
    print(f"{symbol} {test_name}: {details}")
    if not success:
        print(f"    ERROR: {details}")

def run_tests():
    print("🚀 Starting End-to-End API Verification...")
    
    # 1. Health Check
    try:
        r = requests.get(f"http://localhost:8000/health")
        print_result("Health Check", r.status_code == 200, f"Status {r.status_code}")
    except Exception as e:
        print_result("Health Check", False, f"Connection Failed: {e}")
        return

    # 2. Status Check
    try:
        r = requests.get(f"http://localhost:8000/status")
        print_result("App Status", r.status_code == 200, r.json())
    except:
        print_result("App Status", False)

    # 3. Create Chat
    chat_id = None
    try:
        r = requests.post(f"{BASE_URL}/chats", json={"title": "E2E Test Chat"})
        if r.status_code == 200:
            data = r.json()
            chat_id = data['id']
            print_result("Create Chat", True, f"Created ID: {chat_id}, Title: {data['title']}")
        else:
            print_result("Create Chat", False, f"Status {r.status_code}")
    except Exception as e:
        print_result("Create Chat", False, str(e))

    if not chat_id:
        print("❌ Critical: Cannot proceed without chat ID.")
        return

    # 4. Check Duplicate Title (Should Exist)
    try:
        r = requests.get(f"{BASE_URL}/chats/check-title?title=E2E Test Chat")
        data = r.json()
        print_result("Check Duplicate (Positive)", data.get('exists') == True, f"Exists={data.get('exists')}")
    except:
        print_result("Check Duplicate (Positive)", False)

    # 5. Check Duplicate Title (Should Not Exist)
    try:
        r = requests.get(f"{BASE_URL}/chats/check-title?title=NonExistentRandomTitle12345")
        data = r.json()
        print_result("Check Duplicate (Negative)", data.get('exists') == False, f"Exists={data.get('exists')}")
    except:
        print_result("Check Duplicate (Negative)", False)

    # 6. Send Message
    try:
        r = requests.post(f"{BASE_URL}/chats/{chat_id}/messages", json={"content": "Hello E2E", "role": "user"})
        if r.status_code == 200:
            data = r.json()
            print_result("Send Message", True, f"AI Response: {data['content'][:30]}...")
        else:
             print_result("Send Message", False, f"Status {r.status_code}")
    except:
        print_result("Send Message", False)

    # 7. Get Chat Details (verify message saved)
    try:
        r = requests.get(f"{BASE_URL}/chats/{chat_id}")
        if r.status_code == 200:
            data = r.json()
            msgs = data.get('messages', [])
            has_user = any(m['content'] == "Hello E2E" for m in msgs)
            print_result("Get Chat Details", has_user, f"Total Messages: {len(msgs)}")
        else:
            print_result("Get Chat Details", False)
    except:
        print_result("Get Chat Details", False)

    # 8. List Chats
    try:
        r = requests.get(f"{BASE_URL}/chats")
        if r.status_code == 200:
            chats = r.json()
            found = any(c['id'] == chat_id for c in chats)
            print_result("List Chats", found, f"Total Chats: {len(chats)}")
        else:
            print_result("List Chats", False)
    except:
        print_result("List Chats", False)
        
    # 9. Rename Chat
    try:
        r = requests.patch(f"{BASE_URL}/chats/{chat_id}", json={"title": "Renamed E2E Chat"})
        if r.status_code == 200:
            data = r.json()
            print_result("Rename Chat", data['title'] == "Renamed E2E Chat", f"New Title: {data['title']}")
        else:
            print_result("Rename Chat", False, f"Status {r.status_code}")
    except:
        print_result("Rename Chat", False)

    print("\n✅ API Verification Complete.")

if __name__ == "__main__":
    run_tests()
