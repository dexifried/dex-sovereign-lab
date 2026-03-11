import os
from dotenv import load_dotenv
load_dotenv()
import json
import requests
import chromadb
import subprocess
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

# --- LAB CONFIG ---
DEEP_INFRA_KEY = os.getenv("DEEP_INFRA_KEY", "")
EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B-batch" 

# --- SIGNAL FILTER ---
# We ignore these because they are "Vendor Noise" and don't represent YOUR logic.
EXCLUDED_DIRS = {
    'node_modules', '__pycache__', '.git', '.venv', 'venv', 
    'env', 'dist', 'build', '.aider.tags.cache.v3', 'site-packages',
    'bin', 'lib', 'include', 'share'
}

class DeepInfraEmbeddingFunction(EmbeddingFunction):
    def __init__(self): pass 
    def __call__(self, input_texts: Documents) -> Embeddings:
        url = "https://api.deepinfra.com/v1/openai/embeddings"
        headers = {"Authorization": f"Bearer {DEEP_INFRA_KEY}", "Content-Type": "application/json"}
        payload = {"model": EMBEDDING_MODEL, "input": input_texts, "encoding_format": "float"}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return [item['embedding'] for item in response.json()['data']]

chroma_client = chromadb.PersistentClient(path=os.path.expanduser("~/dex-local/dex_vault"))
embed_func = DeepInfraEmbeddingFunction()

def get_collection(name):
    return chroma_client.get_or_create_collection(name=name, embedding_function=embed_func)

def chunk_text(text, chunk_size=400):
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def ingest_path(target_path, collection_name):
    collection = get_collection(collection_name)
    target_path = os.path.normpath(os.path.expanduser(target_path))
    print(f"[*] Ingesting into [{collection_name}]: {target_path}")
    
    valid_extensions = ['.py', '.md', '.txt', '.json', '.sh', '.js', '.html', '.css', '.yml', '.yaml']
    file_count = 0
    
    for root, dirs, files in os.walk(target_path):
        # Dynamically filter out junk directories to save money and time
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.')]
        
        for file in files:
            if any(file.endswith(ext) for ext in valid_extensions):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        text = f.read()
                    chunks = chunk_text(text)
                    if chunks:
                        ids = [f"{filepath}_chunk_{i}" for i in range(len(chunks))]
                        metadatas = [{"source": filepath, "type": "code"} for _ in chunks]
                        collection.upsert(documents=chunks, metadatas=metadatas, ids=ids)
                        print(f"  -> {file} OK")
                        file_count += 1
                except: continue
    print(f"[+] {file_count} relevant files stored in {collection_name}.")

def ingest_github_account(username, collection_name):
    api_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    repos = requests.get(api_url).json()
    base_clone_dir = os.path.expanduser(f"~/dex-local/staging/{username}")
    os.makedirs(base_clone_dir, exist_ok=True)
    
    for repo in repos:
        target_dir = os.path.join(base_clone_dir, repo['name'])
        if not os.path.exists(target_dir):
            subprocess.run(["git", "clone", repo['clone_url'], target_dir], capture_output=True)
        ingest_path(target_dir, collection_name)

if __name__ == "__main__":
    print("=== DEX MULTI-VAULT INGESTION (v1.3) ===")
    print("1. YOUR DATA (Digital Twin)")
    print("2. HARVEST DATA (Inspiration/Dreaming)")
    vault_choice = input("Target Vault (1/2): ")
    
    coll_name = "dex_omniscience" if vault_choice == "1" else "dex_inspiration"
    
    print("\n1. Single Path/Repo\n2. Entire GitHub User")
    mode = input("Mode: ")
    
    if mode == "1":
        path = input("Path or Repo URL: ")
        if path.startswith("http"):
            repo_name = path.split("/")[-1].replace(".git", "")
            target = os.path.expanduser(f"~/dex-local/staging/external/{repo_name}")
            if not os.path.exists(target):
                print(f"[*] Cloning {path}...")
                subprocess.run(["git", "clone", path, target])
            ingest_path(target, coll_name)
        else:
            ingest_path(path, coll_name)
    else:
        user = input("GitHub Username: ")
        ingest_github_account(user, coll_name)

