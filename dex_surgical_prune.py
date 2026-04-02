import pandas as pd
import os

CSV_PATH = os.path.expanduser("~/dex-local/intent_dataset.csv")

# These words MUST be the exclusive property of IMAGE_GEN
# If these appear in SOCIAL_CHAT or AIDER_SURGERY, they are "Neural Poison"
HARD_VISUAL_WORDS = [
    "picture", "image", "photo", "draw", "visualize", 
    "rendering", "portrait", "sketch", "painting"
]

def run_pruning():
    if not os.path.exists(CSV_PATH):
        print("[-] Error: CSV not found.")
        return

    df = pd.read_csv(CSV_PATH)
    initial_count = len(df)
    
    print("==========================================================")
    print("✂️ DEX NEURAL SURGERY: PRUNING POISONED DNA")
    print("==========================================================")

    # 1. Identify the Poison
    # We find rows that are NOT Image Gen but use Hard Visual Words
    poison_mask = (
        (df['label'] != 'IMAGE_GEN') & 
        (df['text'].str.lower().str.contains('|'.join(HARD_VISUAL_WORDS), na=False))
    )
    
    poisoned_samples = df[poison_mask]
    
    if poisoned_samples.empty:
        print("[+] No poisoned samples found. The DNA is already clean.")
    else:
        print(f"[*] Found {len(poisoned_samples)} poisoned samples across other classes.")
        
        # 2. DELETE the poison
        df_cleaned = df[~poison_mask].copy()
        
        # 3. Save the stabilized DNA
        df_cleaned.to_csv(CSV_PATH, index=False)
        
        final_count = len(df_cleaned)
        print(f"[+] Successfully purged {initial_count - final_count} samples.")
        print(f"[+] Total DNA Samples remaining: {final_count}")
        
        print("\n[*] Breakdown of purged samples per class:")
        print(poisoned_samples['label'].value_counts())

    print("-" * 55)
    print("[?] NEXT STEP: 'The Synthetic Signal Boost'")
    print("Now that the other classes are 'Clean', you need to pump")
    print("IMAGE_GEN up to 200+ samples so it can compete in weight.")
    print("==========================================================")

if __name__ == "__main__":
    run_pruning()

