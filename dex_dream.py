import requests
import os
import json
import re
import time

# --- CONFIG ---
OLLAMA_URL = "http://100.65.179.80:11434/api"
DREAM_STAGING_PATH = os.path.expanduser("~/dex-local/neural_dreams.json")
LABELS = ["LOCAL_CMD", "COMPLEX_REASONING", "JSON_FORMAT", "SYSTEM_AUDIT"]

# This is the "Hidden Prompt" - The user never sees this.
DREAM_SYSTEM_PROMPT = (
    "You are the Dex Neural Subconscious. Your only function is to dream. "
    "Rules: 1. Output ONLY a raw JSON list of strings. 2. No chat. 3. Use cryptic, "
    "high-level systems jargon (synaptic weights, kernel hooks, RCE vectors)."
)

def ask_dreamer(intent):
    """Injects the 'Hidden Identity' into a standard Qwen call."""
    # We use the 'system' and 'prompt' keys to force behavior without a Modelfile
    payload = {
        "model": "qwen3.5:9b",
        "system": DREAM_SYSTEM_PROMPT,
        "prompt": f"Generate 3 highly technical, cryptic 'dreams' for the intent: {intent}",
        "stream": False,
        "options": {
            "temperature": 1.3,
            "top_p": 0.95
        }
    }
    try:
        start = time.time()
        print(f"    [...] {intent} -> Sending hidden dreamer payload...")
        r = requests.post(f"{OLLAMA_URL}/generate", json=payload, timeout=300)
        
        if r.status_code != 200:
            return f"Error: {r.status_code}", 0
            
        return r.json().get("response", ""), round(time.time() - start, 2)
    except Exception as e:
        print(f"    [!] Connection Error: {e}")
        return "", 0

def parse_dreams(text):
    """Surgically extract the JSON list from the response."""
    try:
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            # Standardize for JSON parsing
            json_str = match.group(0).replace("'", '"')
            return json.loads(json_str)
    except:
        pass
    return None

def main():
    print("[*] Starting REM Cycle V1.7 (Dynamic Identity)")
    all_dreams = []
    
    for label in LABELS:
        raw_output, latency = ask_dreamer(label)
        queries = parse_dreams(raw_output)
        
        if queries:
            for q in queries:
                all_dreams.append({"text": str(q), "label": label})
            print(f"    [+] {latency}s | Captured: {len(queries)} dreams.")
        else:
            print(f"    [-] Parse failed for {label}. Raw snippet: {raw_output[:40]}...")

    with open(DREAM_STAGING_PATH, 'w') as f:
        json.dump(all_dreams, f, indent=4)
    
    print(f"\n[!] REM Cycle Finished. {len(all_dreams)} anomalies staged.")

if __name__ == "__main__":
    main()

