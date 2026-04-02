import json
from dex_infra import get_embeddings, rerank_query

def run_diagnostics():
    print("=== DEX HYBRID CLOUD DIAGNOSTICS ===\n")
    
    print("[*] 1. Testing Qwen3-Embedding-8B...")
    embed_text = "Dex is a multi-agentic framework evolving into a lab career."
    vector = get_embeddings(embed_text)
    if vector:
        print(f"    [+] Success! Received vector array of length: {len(vector)}")
        print(f"    [+] Data Snippet: {vector[:3]} ...")
    else:
        print("    [-] FAILED to get embeddings.")

    print("\n--------------------------------------------------\n")

    print("[*] 2. Testing Qwen3-Reranker-4B...")
    query = "How do I reboot the core neural router?"
    candidates = [
        "The capital of Canada is Ottawa.",
        "To restart the Gatekeeper, run pkill -f dex_gatekeeper.py and launch dex-gram.",
        "A neural network consists of layers of interconnected nodes or neurons."
    ]
    
    print(f"    Query: '{query}'")
    for i, doc in enumerate(candidates):
        print(f"    Doc {i}: {doc}")
        
    print("\n    [...] Waiting for Deep Infra Reranker...")
    results = rerank_query(query, candidates)
    
    if results and 'scores' in results:
        print("    [+] Success! Relevance Scores (Higher is better):")
        scores = results['scores']
        
        # Zip the scores with the original documents so we can sort them
        combined = []
        for idx, (score, doc) in enumerate(zip(scores, candidates)):
            combined.append({'index': idx, 'score': score, 'doc': doc})
            
        # Sort by score descending
        sorted_results = sorted(combined, key=lambda x: x['score'], reverse=True)
        
        for res in sorted_results:
            print(f"        -> Score: {res['score']:.4f} | Doc {res['index']}: {res['doc'][:40]}...")
    else:
        print("    [-] FAILED to get reranker results. Raw output:")
        print(f"    {results}")

if __name__ == "__main__":
    run_diagnostics()


