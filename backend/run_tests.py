import os
import json
import sys

# Load .env
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ai.agent import run_agent

print("=" * 60)
print("   FINAL AI CRM TESTS - ALL 5 TOOLS")
print("=" * 60)

test_cases = [
    ("LOG",      "Met Dr Mehta, discussed insulin, very interested"),
    ("FETCH",    "What did I discuss with Dr Mehta?"),
    ("EDIT",     "Update sentiment to highly interested"),
    ("SUGGEST",  "What should I do next?"),
    ("INSIGHTS", "Give me insights on Dr Mehta"),
]

for label, query in test_cases:
    print(f"\n[{label}] USER: {query}")
    try:
        res = run_agent(query)
        if isinstance(res, dict):
            print(f"AGENT:\n{json.dumps(res, indent=2, default=str)}")
        else:
            print(f"AGENT:\n{res}")
    except Exception as e:
        print(f"ERROR: {e}")
    print("-" * 60)

print("\nAll tests completed.")
