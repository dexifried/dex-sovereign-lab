import requests
import json
import time

# --- CONFIG ---
# Target your remote 3060 Node
OLLAMA_URL = "http://100.65.179.80:11434/api/create"

# We define the Modelfile as a list to control every single newline.
# We include a trailing newline on the FROM line, which is often the fix.
lines = [
    "FROM qwen3.5:9b",
    "PARAMETER temperature 1.3",
    "PARAMETER top_p 0.95",
    "SYSTEM \"You are the Dex Subconscious. Output ONLY a JSON list of technical queries.\"",
    "" # Ensuring a final newline
]

modelfile_string = "\n".join(lines)

def create():
    # We use the 'modelfile' field which expects the literal string content.
    payload = {
        "name": "qwen-dreamer",
        "modelfile": modelfile_string,
        "stream": False
    }
    
    print(f"[*] Attempting to inject 'qwen-dreamer' identity...")
    print(f"[*] Payload length: {len(modelfile_string)} bytes")
    
    try:
        # We explicitly set the timeout longer for model creation
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        
        if response.status_code == 200:
            print("[+] SUCCESS: 'qwen-dreamer' created on 100.65.179.80.")
        else:
            print(f"[-] FAILED (Status {response.status_code})")
            print(f"[-] Server Response: {response.text}")
            
            # Debugging step: Try a minimal Modelfile if the first one fails
            if "neither 'from' or 'files'" in response.text:
                print("[*] Retrying with absolute minimal Modelfile...")
                minimal_payload = {
                    "name": "qwen-dreamer",
                    "modelfile": "FROM qwen3.5:9b\n",
                    "stream": False
                }
                r2 = requests.post(OLLAMA_URL, json=minimal_payload, timeout=60)
                print(f"[*] Minimal result: {r2.status_code} | {r2.text}")

    except Exception as e:
        print(f"[-] Connection Error: {e}")

if __name__ == "__main__":
    create()


