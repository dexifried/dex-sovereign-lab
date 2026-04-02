import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

# --- CONFIG ---
API_KEY = os.getenv("DEEP_INFRA_KEY", "")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def generate_image(prompt):
    print(f"[*] Deep Infra: Visualizing '{prompt}' via PrunaAI...")
    url = "https://api.deepinfra.com/v1/inference/PrunaAI/p-image"
    data = {"prompt": prompt}
    
    try:
        r = requests.post(url, headers=HEADERS, json=data, timeout=60)
        if r.status_code != 200:
            print(f"[-] Deep Infra API Rejected! Status: {r.status_code}")
            return None
        print("[+] Deep Infra: Raw image data received.")
        images = r.json().get("images", [])
        return images[0] if images else None
    except Exception as e:
        print(f"[-] Image Gen Connection Failed: {e}")
        return None

def rerank_query(query, candidates):
    """Uses Qwen3-Reranker-4B to score a list of documents against a query."""
    url = "https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-4B"
    # LAB PATCH: 'queries' must be a list, based on raw curl telemetry
    data = {
        "queries": [query],
        "documents": candidates
    }
    try:
        r = requests.post(url, headers=HEADERS, json=data, timeout=30)
        if r.status_code != 200:
            print(f"[-] Reranker API Error {r.status_code}: {r.text}")
            return None
        return r.json()
    except Exception as e:
        print(f"[-] Reranker Failed: {e}")
        return None

def get_embeddings(text):
    url = "https://api.deepinfra.com/v1/openai/embeddings"
    data = {"input": text, "model": "Qwen/Qwen3-Embedding-8B"}
    try:
        r = requests.post(url, headers=HEADERS, json=data, timeout=30)
        if r.status_code != 200: return None
        return r.json().get("data", [{}])[0].get("embedding")
    except: return None


