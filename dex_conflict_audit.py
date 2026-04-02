import pandas as pd
import os

# --- Configuration ---
CSV_PATH = os.path.expanduser("~/dex-local/intent_dataset.csv")

# Keywords that should logically trigger IMAGE_GEN but might be hiding in SOCIAL_CHAT
VISUAL_TRIGGERS = [
    "picture", "image", "draw", "visualize", "render", 
    "photo", "art", "generate", "show me", "painting", "sketch"
]

def run_conflict_audit():
    if not os.path.exists(CSV_PATH):
        print(f"[-] Error: {CSV_PATH} not found.")
        return

    print("==========================================================")
    print("🔍 DEX NEURAL CONFLICT AUDIT: LOCATING POISONED SAMPLES")
    print("==========================================================")

    # Load the dataset
    df = pd.read_csv(CSV_PATH)
    total_samples = len(df)
    
    # 1. FIND CONFLICTS
    # We look for rows NOT labeled IMAGE_GEN that contain visual keywords
    conflicts = df[
        (df['label'] != 'IMAGE_GEN') & 
        (df['text'].str.lower().str.contains('|'.join(VISUAL_TRIGGERS), na=False))
    ]

    if conflicts.empty:
        print("[+] No direct linguistic overlaps found. The issue is likely hidden in the weights.")
    else:
        print(f"[!] Found {len(conflicts)} Poisoned Samples in other classes!")
        print("These samples are teaching BERT that 'Visual' words = 'Social/Code'.")
        print("-" * 55)
        # Group by label to see where the poison is concentrated
        report = conflicts.groupby('label').size()
        for label, count in report.items():
            print(f"{label:<25} | {count} samples")
        
        print("-" * 55)
        print("TOP 15 CONFLICTING SAMPLES (Sampled for review):")
        for _, row in conflicts.sample(min(len(conflicts), 15)).iterrows():
            print(f"[{row['label']}] -> {row['text']}")

    # 2. DUPLICATE CHECK
    # Check for identical prompts with different labels
    duplicates = df[df.duplicated(subset=['text'], keep=False)]
    if not duplicates.empty:
        print("\n[!] Found duplicate text entries with conflicting labels!")
        print(duplicates.sort_values(by='text').head(10))

    print("\n[?] LAB STRATEGY:")
    print("If you see many 'Social' samples mentioning 'pictures', we need to prune.")
    print("A clean split is required for the 9th neuron to stabilize.")
    print("==========================================================")

if __name__ == "__main__":
    run_conflict_audit()

