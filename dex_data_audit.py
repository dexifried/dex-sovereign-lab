import pandas as pd
import os
import collections

# --- Path Configuration ---
CSV_PATH = os.path.expanduser("~/dex-local/intent_dataset.csv")

def audit_brain_dna():
    if not os.path.exists(CSV_PATH):
        print("[-] Error: intent_dataset.csv not found.")
        return

    print("==========================================================")
    print("📊 DEX NEURAL DATA AUDIT")
    print("==========================================================")

    # Load the dataset
    df = pd.read_csv(CSV_PATH)
    
    # Count distributions
    counts = df['label'].value_counts().to_dict()
    total = len(df)

    print(f"Total DNA Samples: {total}\n")
    print(f"{'INTENT':<25} | {'COUNT':<6} | {'PERCENTAGE'}")
    print("-" * 50)

    for intent, count in counts.items():
        percentage = (count / total) * 100
        print(f"{intent:<25} | {count:<6} | {percentage:>8.2f}%")

    # Check for the 9th Neuron
    if "IMAGE_GEN" not in counts:
        print("\n[!] WARNING: 'IMAGE_GEN' is missing from the dataset. Use /feedback to add it.")
    elif counts["IMAGE_GEN"] < 15:
        print(f"\n[!] ADVISORY: 'IMAGE_GEN' only has {counts['IMAGE_GEN']} samples.")
        print("    For Lab-grade routing, aim for at least 20 samples to ensure the 9th neuron fires reliably.")
    else:
        print("\n[+] SUCCESS: 'IMAGE_GEN' has reached generalization threshold.")

    print("==========================================================")

if __name__ == "__main__":
    audit_brain_dna()

