import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()
import requests
import json
import re
import time
from typing import List

# --- Configuration ---
CSV_PATH = os.path.expanduser("~/dex-local/intent_dataset.csv")
CEREBRAS_KEY = os.getenv("CEREBRAS_KEY", "")
U_CER = "https://api.cerebras.ai/v1/chat/completions"

TARGET_COUNT = 35 
WEAK_INTENTS = ["IMAGE_GEN", "DYNAMIC_BROKER", "SOCIAL_CHAT"]

def get_current_counts():
    if not os.path.exists(CSV_PATH): return {}
    df = pd.read_csv(CSV_PATH)
    return df['label'].value_counts().to_dict()

def generate_synthetic_dna(intent: str, count_needed: int) -> List[str]:
    """Uses Cerebras 120B to generate high-variance synthetic prompts."""
    print(f"[*] Dreaming up {count_needed} specific samples for '{intent}'...")
    
    # Advanced Prompting for Data Diversity
    prompt = f"""You are a Neural Data Scientist. I am training a ModernBERT classifier.
    The '{intent}' class is under-represented. Generate {count_needed} unique, high-variance user prompts.
    
    Context for '{intent}':
    - If IMAGE_GEN: User wants to create, draw, or generate visuals (e.g., "Paint a...", "Draw...", "Make a photo of...").
    - If DYNAMIC_BROKER: User wants general knowledge, long-form explanations, or high-level non-technical help.
    - If SOCIAL_CHAT: Greetings, jokes, personal check-ins.
    
    REQUIREMENTS:
    1. Vary the tone: Slang, formal, terse, overly descriptive.
    2. Vary the length: 3 words to 20 words.
    3. Output ONLY a valid JSON list of strings. No keys, no markdown, no preamble.
    
    FORMAT: ["prompt1", "prompt2", ...]
    """

    try:
        r = requests.post(U_CER, 
            headers={"Authorization": f"Bearer {CEREBRAS_KEY}", "Content-Type": "application/json"}, 
            json={
                "model": "gpt-oss-120b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 1.1, # Higher temperature for more creative/diverse data
                "max_tokens": 4096
            }, timeout=90)
        
        if r.status_code != 200:
            print(f"[-] API Error {r.status_code}: {r.text}")
            return []

        raw_content = r.json()['choices'][0]['message']['content'].strip()
        
        # Robust Parsing: Clean any markdown blocks the LLM might have added
        if "```json" in raw_content:
            raw_content = re.search(r'```json\s*(.*?)\s*```', raw_content, re.DOTALL).group(1)
        elif "```" in raw_content:
            raw_content = re.search(r'```\s*(.*?)\s*```', raw_content, re.DOTALL).group(1)
            
        data = json.loads(raw_content)
        if isinstance(data, list):
            return [str(s) for s in data]
        return []
    except Exception as e:
        print(f"[-] Parsing Failure for {intent}: {e}")
        return []

def balance_dna():
    for intent in WEAK_INTENTS:
        counts = get_current_counts()
        current = counts.get(intent, 0)
        
        if current < TARGET_COUNT:
            needed = TARGET_COUNT - current
            samples = generate_synthetic_dna(intent, needed)
            
            if samples:
                # Append immediately to CSV to ensure state is saved
                rows = [[s, intent] for s in samples]
                with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
                print(f"[+] Successfully fused {len(samples)} new samples for {intent} into the DNA.")
            else:
                print(f"[!] Warning: Failed to generate samples for {intent}.")
        else:
            print(f"[+] Intent '{intent}' already at Lab-grade threshold ({current}).")

if __name__ == "__main__":
    import csv
    print("==========================================================")
    print("🧬 DEX DNA BALANCER V2 - RECURSIVE TARGET SEEKER")
    print("==========================================================\n")
    balance_dna()
    print("\n[!] Balancing Complete. Re-run Audit to verify.")

