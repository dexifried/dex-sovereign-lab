import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

# --- Load your actual config ---
P_CONFIG = os.path.expanduser("~/dex-local/dex_config.json")
with open(P_CONFIG, 'r') as f:
    config = json.load(f)

API_KEY = os.getenv("DEEP_INFRA_KEY", "")
MODEL = config.get("models", {}).get("social_chat", "meta-llama/Llama-3.3-70B-Instruct")
URL = "https://api.deepinfra.com/v1/openai/chat/completions"

def run_diagnostic():
    print(f"[*] Testing DeepInfra Link...")
    print(f"[*] Target Model: {MODEL}")
    
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Connectivity test. Reply with 'OK'."}],
        "max_tokens": 10
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(URL, headers=headers, json=payload, timeout=20)
        
        print(f"[*] HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            print("[+] SUCCESS: DeepInfra is online and responsive.")
            print(f"[*] Response: {response.json()['choices'][0]['message']['content']}")
        else:
            print("[!] FAILURE: API returned an error.")
            print(f"[*] Raw Error: {response.text}")
            
            if response.status_code == 402:
                print(">>> DIAGNOSIS: Insufficient Funds. Top up your DeepInfra balance.")
            elif response.status_code == 404:
                print(">>> DIAGNOSIS: Model Not Found. Check the model name in dex_config.json.")
            elif response.status_code == 401:
                print(">>> DIAGNOSIS: Invalid API Key.")
                
    except Exception as e:
        print(f"[-] Network Error: {e}")

if __name__ == "__main__":
    run_diagnostic()

