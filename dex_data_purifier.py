import pandas as pd
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
import shutil
import re

CSV_PATH = os.path.expanduser("~/dex-local/intent_dataset.csv")
BACKUP_PATH = os.path.expanduser("~/dex-local/intent_dataset.backup.csv")

GROQ_KEY = os.getenv("GROQ_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def run_neural_audit():
    if not os.path.exists(CSV_PATH):
        print("[-] Dataset not found.")
        return

    shutil.copy(CSV_PATH, BACKUP_PATH)
    print("[*] Dataset backed up to intent_dataset.backup.csv")

    df = pd.read_csv(CSV_PATH)
    start_count = len(df)
    
    # 1. THE MECHANICAL PURGE
    df = df.dropna(subset=['text', 'label'])
    df['text'] = df['text'].str.strip()
    df = df.drop_duplicates(subset=['text'], keep='last')
    mech_dropped = start_count - len(df)
    print(f"[*] Mechanical Purge Complete: Removed {mech_dropped} duplicates/nulls.")

    df = df.reset_index(drop=True)

    # 2. THE NEURAL AUDIT
    print("[*] Waking up Groq Auditor for Semantic Cleansing...")
    
    batch_size = 50
    kill_list = []

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        payload_data = [{"id": idx, "text": row['text'], "label": row['label']} for idx, row in batch.iterrows()]
        
        prompt = (
            "You are a ruthless data auditor for an AI lab. Your job is to clean training data. "
            "Review the following JSON list of text/intent pairs. "
            "Identify any pairs that are:\n"
            "1. Gibberish or contain hallucinated code/languages.\n"
            "2. Completely ambiguous or nonsensical.\n"
            "3. Clearly misclassified.\n\n"
            "Return ONLY a raw JSON list of the integer IDs that should be DELETED. "
            "Example output: [4, 12, 45]. If the batch is perfectly clean, return []. "
            "Do NOT include markdown blocks, explanations, or any other text.\n\n"
            f"DATA:\n{json.dumps(payload_data, indent=2)}"
        )

        try:
            r = requests.post(GROQ_URL, headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            }, json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0
            })
            
            response_text = r.json()['choices'][0]['message']['content'].strip()
            
            # BULLETPROOF REGEX PARSER
            match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if match:
                bad_ids = json.loads(match.group(0))
            else:
                # If it didn't output a list at all, assume it found nothing and got confused
                bad_ids = []
                
            if isinstance(bad_ids, list) and len(bad_ids) > 0:
                kill_list.extend(bad_ids)
                print(f"  -> Batch {i//batch_size + 1}: Found {len(bad_ids)} garbage anomalies.")
            else:
                print(f"  -> Batch {i//batch_size + 1}: Clean.")
            
        except Exception as e:
            print(f"  [-] Batch {i//batch_size + 1} Error: Parsing failed. Skipping batch.")
            continue

    # 3. THE EXECUTION
    if kill_list:
        df = df.drop(index=kill_list, errors='ignore')
        
    final_count = len(df)
    neural_dropped = (start_count - mech_dropped) - final_count
    
    df.to_csv(CSV_PATH, index=False)
    print("\n" + "="*40)
    print("🧹 AUDIT COMPLETE")
    print("="*40)
    print(f"Starting Records: {start_count}")
    print(f"Mechanical Drops: {mech_dropped}")
    print(f"Neural Drops:     {neural_dropped}")
    print(f"Final Clean DNA:  {final_count}")
    print("="*40)

if __name__ == "__main__":
    run_neural_audit()


