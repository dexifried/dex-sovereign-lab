import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.optim import AdamW  # <-- FIXED: Using PyTorch's native AdamW

# --- FULL SOVEREIGN LAB TOPOLOGY ---
LABEL_MAP = {
    "LOCAL_CMD": 0, 
    "AIDER_SURGERY": 1, 
    "STRATEGIC_PLANNER": 2, 
    "CODE_REVIEW": 3, 
    "SOCIAL_CHAT": 4, 
    "DYNAMIC_BROKER": 5, 
    "UPDATE_MEMORY": 6,
    "ACCESS_MEMORY": 7
}

MODEL_PATH = os.path.expanduser("~/dex-local/dex_router_model")
DATASET_PATH = os.path.expanduser("~/dex-local/intent_dataset.csv")
BASE_MODEL = "answerdotai/ModernBERT-base"

def train_synapse():
    if not os.path.exists(DATASET_PATH): 
        print("[-] No dataset found. Please create intent_dataset.csv.")
        return
    
    df = pd.read_csv(DATASET_PATH)
    if len(df) < 5: 
        print("[-] Log more feedback first. Need at least 5 rows.")
        return

    print(f"[*] Training on {len(df)} samples...")
    print(f"[*] New Label Map Size: {len(LABEL_MAP)} Domains")
    
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    load_from = MODEL_PATH if os.path.exists(MODEL_PATH) else BASE_MODEL
    
    # ignore_mismatched_sizes=True automatically handles the transition from 7 to 8 labels
    model = AutoModelForSequenceClassification.from_pretrained(
        load_from, 
        num_labels=len(LABEL_MAP), 
        ignore_mismatched_sizes=True
    )

    # Convert text to tensors
    texts = df['text'].tolist()
    labels = [LABEL_MAP.get(l.strip(), 5) for l in df['label'].tolist()] 

    encodings = tokenizer(texts, truncation=True, padding=True, max_length=128, return_tensors='pt')
    
    optimizer = AdamW(model.parameters(), lr=5e-5)
    model.train()
    
    # 5 Fast Epochs to wire the new 8-domain topology
    for epoch in range(5):
        optimizer.zero_grad()
        outputs = model(encodings['input_ids'], attention_mask=encodings['attention_mask'], labels=torch.tensor(labels))
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        print(f"    Epoch {epoch+1} | Loss: {loss.item():.4f}")

    # Save the newly evolved brain
    model.save_pretrained(MODEL_PATH)
    tokenizer.save_pretrained(MODEL_PATH)
    print("[+] ModernBERT evolved. Topology mapped to 8 Sovereign Domains. Reboot dex-gram.")

if __name__ == "__main__":
    train_synapse()


