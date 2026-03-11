import pandas as pd
import os
import random

# --- Configuration ---
CSV_PATH = os.path.expanduser("~/dex-local/intent_dataset.csv")
TARGET_LABEL = "CODE_REVIEW"
PRUNE_TARGET = 200

def prune_dna():
    if not os.path.exists(CSV_PATH):
        print("[-] Error: intent_dataset.csv not found.")
        return

    print("==========================================================")
    print(f"✂️  DEX DNA PRUNER - TARGETING {TARGET_LABEL}")
    print("==========================================================")

    # Load the full dataset
    df = pd.read_csv(CSV_PATH)
    
    # Separate the target class from the rest
    target_df = df[df['label'] == TARGET_LABEL]
    others_df = df[df['label'] != TARGET_LABEL]
    
    current_count = len(target_df)
    
    if current_count <= PRUNE_TARGET:
        print(f"[!] {TARGET_LABEL} is already at {current_count} samples. No pruning needed.")
        return

    print(f"[*] Current {TARGET_LABEL} count: {current_count}")
    print(f"[*] Pruning down to: {PRUNE_TARGET}")

    # Randomly sample the target class
    # We use a fixed random_state if we want reproducibility, 
    # but for a dynamic lab, we'll keep it truly random or use a set seed.
    pruned_target_df = target_df.sample(n=PRUNE_TARGET, random_state=42)
    
    # Recombine
    final_df = pd.concat([others_df, pruned_target_df], ignore_index=True)
    
    # Shuffle the final dataset so the training batches aren't ordered by label
    final_df = final_df.sample(frac=1).reset_index(drop=True)
    
    # Save back to CSV
    final_df.to_csv(CSV_PATH, index=False)

    print(f"\n[+] Pruning Successful!")
    print(f"[+] New Total DNA Samples: {len(final_df)}")
    print("==========================================================")

if __name__ == "__main__":
    prune_dna()

