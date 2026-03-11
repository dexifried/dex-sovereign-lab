import os
from dotenv import load_dotenv
load_dotenv()

import requests

# --- SOVEREIGN CREDENTIALS ---
API_KEY = os.getenv("DEEP_INFRA_KEY", "")
TEXT_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
IMAGE_MODEL = "black-forest-labs/FLUX-1-schnell" # common default

def check_link(label, url, payload):
    print(f"[*] Testing {label}...")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        print(f"    -> Status: {response.status_code}")
        if response.status_code == 200:
            print(f"    -> [OK] {label} is active.")
        else:
            print(f"    -> [FAIL] Error: {response.text}")
            if "balance" in response.text.lower() or response.status_code == 402:
                print("    !!! DIAGNOSIS: YOUR DEEPINFRA ACCOUNT IS OUT OF CREDITS.")
    except Exception as e:
        print(f"    -> [ERROR] Connection Failed: {e}")

if __name__ == "__main__":
    print("==========================================================")
    print("🛰️ DEX HARDLINE DIAGNOSTIC - DEEPINFRA")
    print("==========================================================")
    
    # Test Text Generation (Social Chat)
    check_link("TEXT CORTEX", 
               "https://api.deepinfra.com/v1/openai/chat/completions",
               {"model": TEXT_MODEL, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5})

    # Test Image Generation (Visual Cortex)
    check_link("VISUAL CORTEX", 
               "https://api.deepinfra.com/v1/inference/black-forest-labs/FLUX-1-dev",
               {"prompt": "a simple dot"})
    
    print("==========================================================")

