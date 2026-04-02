import os
from dotenv import load_dotenv
load_dotenv()
import requests
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

# --- API KEYS & CONFIG ---
DEEP_INFRA_KEY = os.getenv("DEEP_INFRA_KEY", "")
EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B-batch"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"

class DeepInfraEmbeddingFunction(EmbeddingFunction):
    def __init__(self): pass
    def __call__(self, input_texts: Documents) -> Embeddings:
        url = "https://api.deepinfra.com/v1/openai/embeddings"
        headers = {"Authorization": f"Bearer {DEEP_INFRA_KEY}", "Content-Type": "application/json"}
        payload = {"model": EMBEDDING_MODEL, "input": input_texts, "encoding_format": "float"}
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            return [item['embedding'] for item in res.json()['data']]
        except: return []

def query_vault(query, collection_name, top_k=3):
    vault_path = os.path.expanduser("~/dex-local/dex_vault")
    client = chromadb.PersistentClient(path=vault_path)
    try:
        collection = client.get_collection(name=collection_name, embedding_function=DeepInfraEmbeddingFunction())
        # Net: Pull top 12 results
        results = collection.query(query_texts=[query], n_results=12)
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        if not docs: return []

        # Scalpel: Prepare for reranking
        candidate_blocks = [f"FILE: {metas[i]['source']}\nCODE:\n{docs[i]}" for i in range(len(docs))]
        
        # Rerank via Deep Infra
        url = f"https://api.deepinfra.com/v1/inference/{RERANKER_MODEL}"
        headers = {"Authorization": f"Bearer {DEEP_INFRA_KEY}", "Content-Type": "application/json"}
        payload = {"query": query, "documents": candidate_blocks}
        
        rerank_res = requests.post(url, headers=headers, json=payload, timeout=15).json().get('results', [])
        
        # High-Fidelity Filter: Threshold 0.35
        final = [candidate_blocks[r['index']] for r in rerank_res if r['relevance_score'] > 0.35]
        return final[:top_k]
    except: return []

def get_dex_context(user_prompt):
    """The bridge between your DNA and External Inspiration."""
    my_dna = query_vault(user_prompt, "dex_omniscience")
    inspiration = query_vault(user_prompt, "dex_inspiration")
    
    context = ""
    if my_dna:
        context += "\n[YOUR TECHNICAL DNA (Relevant to current task)]:\n" + "\n\n".join(my_dna)
    if inspiration:
        context += "\n\n[EXTERNAL INSPIRATION (How the industry leaders do it)]:\n" + "\n\n".join(inspiration)
        
    return context

