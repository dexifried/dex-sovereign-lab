import os
from dotenv import load_dotenv
load_dotenv(), json, random, re, requests, chromadb

# --- CONFIG ---
VAULT_DIR = os.path.expanduser("~" + "/dex-local/dex_vault")
DATASET_OUT = os.path.expanduser("~" + "/dex-local/intent_dataset.csv")

# Exact DeepInfra DeepSeek-V3.2 Endpoint
API_URL = "https://" + "api.deepinfra.com/v1/inference/deepseek-ai/DeepSeek-V3.2"
API_KEY = os.getenv("DEEP_INFRA_KEY", "") 

LABELS = [
    "LOCAL_CMD", "AIDER_SURGERY", "STRATEGIC_PLANNER", 
    "CODE_REVIEW", "SOCIAL_CHAT", "DYNAMIC_BROKER", 
    "UPDATE_MEMORY", "ACCESS_MEMORY"
]

def pull_vault_chunks(num_chunks=20): # Increased count for a bigger bake
    try:
        client = chromadb.PersistentClient(path=VAULT_DIR)
        coll = client.get_collection(name="dex_omniscience")
        data = coll.get()
        all_docs = data.get('documents', [])
        if not all_docs: return []
        return [doc[:1000] for doc in random.sample(all_docs, min(num_chunks, len(all_docs)))]
    except Exception as e:
        print(f"[-] Vault Error: {e}")
        return []

def generate_synthetic_intents(chunk):
    # THE ENTROPY INJECTOR: Specifically targeting the Audit vs Surgery boundary
    prompt = f"""You are an adversarial training data generator.
Analyze this code from the Dex Framework:

{chunk}

Generate 5 natural language queries. 
- 2 queries must be 'Surgical Crossovers': Start with words like 'Audit', 'Check', or 'Review', but explicitly end with an instruction to 'fix', 'refactor', 'apply', or 'overwrite' the file (Label: AIDER_SURGERY).
- 2 queries must be 'Pure Audits': Ask for an explanation, a security review, or an analysis WITHOUT any request to change the files (Label: CODE_REVIEW).
- 1 query must be a 'Logic Bridge': Ask a complex strategic question about the code's role in the larger lab (Label: STRATEGIC_PLANNER).

Format: JSON array of objects. Keys: "text", "label". No markdown.
"""
    
    # Shielded DeepSeek Prompt Tags
    BOS = "<" + "\uff5cbegin\u2581of\u2581sentence\uff5c>"
    USER = "<" + "\uff5cUser\uff5c>"
    ASST = "<" + "\uff5cAssistant\uff5c>"
    EOS = "<" + "\uff5cend\u2581of\u2581sentence\uff5c>"
    
    formatted_prompt = f"{BOS}{USER}{prompt}{ASST}"

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"input": formatted_prompt, "stop": [EOS]}
    
    try:
        res = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        raw_output = res.json().get("results", [{}])[0].get("generated_text", "")
        # Strip  tags
        raw_output = re.sub(r'.*?', '', raw_output, flags=re.DOTALL)
        
        match = re.search(r'\[.*\]', raw_output, re.DOTALL)
        if match: return json.loads(match.group(0))
        return []
    except Exception as e:
        print(f"[-] API Error: {e}")
        return []

def generate_adversarial_intents():
    """Generate 15 adversarial training pairs distinguishing AIDER_SURGERY vs UPDATE_MEMORY"""
    
    prompt = f"""You are an adversarial training data generator for the Dex Framework.
Your task is to create 15 natural language queries that explicitly teach a neural network 
the difference between two intent categories:

AIDER_SURGERY: Commands that edit, refactor, write code, or modify files (e.g., "fix this bug", "add a function", "refactor this module")
UPDATE_MEMORY: Commands that remember facts, save information, store passwords, or update knowledge (e.g., "remember that...", "save this to memory", "store the API key")

Generate exactly 15 pairs. Each pair must be a distinct query with its corresponding label.

Format: JSON array of objects. Keys: "text", "label". No markdown.
"""
    
    BOS = "<" + "\uff5cbegin\u2581of\u2581sentence\uff5c>"
    USER = "<" + "\uff5cUser\uff5c>"
    ASST = "<" + "\uff5cAssistant\uff5c>"
    EOS = "<" + "\uff5cend\u2581of\u2581sentence\uff5c>"
    
    formatted_prompt = f"{BOS}{USER}{prompt}{ASST}"
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"input": formatted_prompt, "stop": [EOS]}
    
    try:
        res = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        raw_output = res.json().get("results", [{}])[0].get("generated_text", "")
        raw_output = re.sub(r'.*?', '', raw_output, flags=re.DOTALL)
        
        match = re.search(r'\[.*\]', raw_output, re.DOTALL)
        if not match:
            print(f"[-] No JSON output from API")
            return []
        
        new_data = json.loads(match.group(0))
        
        # Validate we got exactly 15 pairs with correct labels
        valid_pairs = [item for item in new_data 
                       if item.get("label") in ["AIDER_SURGERY", "UPDATE_MEMORY"]]
        
        if len(valid_pairs) < 15:
            print(f"[-] Only {len(valid_pairs)} valid pairs generated, expected 15")
            return []
        
        return valid_pairs[:15]
    except Exception as e:
        print(f"[-] API Error: {e}")
        return []

def mine_synapses():
    print("[*] Accessing Omniscience Vault for High-Entropy Mining...")
    chunks = pull_vault_chunks(20)
    if not chunks: return
    
    new_data = []
    for i, chunk in enumerate(chunks):
        print(f"  -> Mining Crossover {i+1}/{len(chunks)}...")
        new_data.extend(generate_synthetic_intents(chunk))
        
    if not new_data: return

    # Generate adversarial pairs
    adv_data = generate_adversarial_intents()
    if adv_data:
        new_data.extend(adv_data)
    
    if not new_data: return

    file_exists = os.path.isfile(DATASET_OUT)
    with open(DATASET_OUT, 'a', encoding='utf-8') as f:
        if not file_exists: f.write("text,label\n")
        for item in new_data:
            text = item['text'].replace('"', '""') 
            f.write(f'"{text}",{item["label"]}\n')
            
    print(f"\n[SUCCESS] Mined {len(new_data)} high-entropy intent pairs.")

if __name__ == "__main__":
    mine_synapses()
