import requests
import json
import time

API_URL = "http://127.0.0.1:8000/chat/"

print("=" * 60)
print("   FINAL AI CRM TESTS - API HTTP E2E")
print("=" * 60)

test_cases = [
    ("LOG", "Met Dr Mehta, discussed insulin, very interested"),
    ("FETCH", "What did I discuss with Dr Mehta?"),
    ("EDIT", "Update sentiment to highly interested"),
    ("SUGGEST", "What should I do next?"),
    ("UNKNOWN", "Tell me a joke")
]

payloads = [{"message": q} for _, q in test_cases]

# Give the server a small moment to ensure it has successfully hot-reloaded
time.sleep(2)

for i, payload in enumerate(payloads):
    label = test_cases[i][0]
    query = test_cases[i][1]
    
    print(f"\n[{label}] POST /chat | USER: {query}")
    try:
        response = requests.post(API_URL, json=payload, timeout=20)
        print(f"STATUS CODE: {response.status_code}")
        
        try:
            res_json = response.json()
            print(f"AGENT:\n{json.dumps(res_json, indent=2)}")
        except Exception as e:
            print("AGENT (Raw Text):\n", response.text)
            
    except Exception as e:
        print(f"ERROR: {e}")
        
    print("-" * 60)

print("\nAll HTTP tests completed.")
