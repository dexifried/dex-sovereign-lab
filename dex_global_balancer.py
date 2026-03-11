import pandas as pd
import os
import random

CSV_PATH = os.path.expanduser("~/dex-local/intent_dataset.csv")
TARGET_MIN = 200

# --- SYNTHETIC DNA TEMPLATES ---
# Designed to be distinct to prevent "Neural Poisoning"

DNA_MAP = {
    "SOCIAL_CHAT": {
        "templates": ["Hey Dex, {t}", "Yo, {t}", "Dex, {t}?", "Tell me {t}", "{t}"],
        "subjects": [
            "how are you doing today?", "what's your favorite color?", "tell me a joke",
            "who created you?", "good morning", "give me a fun fact", "what do you think of AI?",
            "how's the weather in the digital void?", "say something philosophical",
            "tell me a short story", "you're doing a great job", "what's the meaning of life?",
            "chat with me for a bit", "what are you up to?", "are you sentient?"
        ]
    },
    "DYNAMIC_BROKER": {
        "templates": ["Search the web for {t}", "Check OpenRouter for {t}", "Ask the swarm about {t}", "Broker this: {t}", "Can you search for {t}"],
        "subjects": [
            "the latest news on spaceX", "current bitcoin price", "best pizza in NYC",
            "who won the game last night?", "how to fix a leaky faucet", "latest research on fusion",
            "wikipedia entry for quantum physics", "search for top 10 movies 2024",
            "find me a tutorial on cooking pasta", "what is the current population of Tokyo?"
        ]
    },
    "UPDATE_MEMORY": {
        "templates": ["Remember that {t}", "Note down: {t}", "Save this to the vault: {t}", "Log this fact: {t}", "I want you to remember {t}"],
        "subjects": [
            "my sister's birthday is June 5th", "I prefer python over javascript", 
            "my favorite food is sushi", "I am working on the Dex project",
            "my dog's name is Apollo", "I live in the Pacific Time Zone",
            "the server password is changed to X", "I like my coffee black",
            "remind me that I have a meeting at 2pm", "I am a lab director"
        ]
    },
    "LOCAL_CMD": {
        "templates": ["Execute: {t}", "Run shell command: {t}", "Terminal: {t}", "In bash, {t}", "System: {t}"],
        "subjects": [
            "ls -la", "pwd", "grep -r 'error' .", "cat config.json", "python3 test.py",
            "git status", "mkdir test_folder", "rm temp.txt", "ps aux", "df -h",
            "chmod +x script.sh", "find . -name '*.py'", "tail -f access.log"
        ]
    },
    "ACCESS_MEMORY": {
        "templates": ["Check the vault for {t}", "What do I remember about {t}", "Access memory regarding {t}", "Scan the ledger for {t}", "Do I have notes on {t}?"],
        "subjects": [
            "my previous project details", "that code snippet I saved", "my preferences",
            "the last meeting notes", "my favorite libraries", "server credentials",
            "the dragon ball conversation", "my work schedule", "historical logs"
        ]
    },
    "STRATEGIC_PLANNER": {
        "templates": ["Strategize {t}", "Plan a roadmap for {t}", "Analyze the impact of {t}", "Oracle, what about {t}", "Give me a high-level plan for {t}"],
        "subjects": [
            "scaling the dex framework", "moving to a new server", "adversarial training",
            "security posture for the lab", "operational visibility", "long term AI safety",
            "the future of human-AI collaboration", "migrating to a cloud-native architecture"
        ]
    }
}

def balance_dna():
    if not os.path.exists(CSV_PATH):
        print("[-] Error: CSV not found.")
        return

    df = pd.read_csv(CSV_PATH)
    counts = df['label'].value_counts()
    
    print("==========================================================")
    print("🧬 DEX NEURAL BALANCER: INITIATING GLOBAL EQUILIBRIUM")
    print("==========================================================")

    new_rows = []
    
    for label, config in DNA_MAP.items():
        current = counts.get(label, 0)
        if current < TARGET_MIN:
            needed = TARGET_MIN - current
            print(f"[*] Boosting {label:<20} | {current:>3} -> {TARGET_MIN} (+{needed})")
            
            for _ in range(needed):
                text = random.choice(config['templates']).format(t=random.choice(config['subjects']))
                new_rows.append({"text": text, "label": label})
        else:
            print(f"[ ] Skipping {label:<20} | {current:>3} (Already balanced)")

    if new_rows:
        boost_df = pd.DataFrame(new_rows)
        final_df = pd.concat([df, boost_df], ignore_index=True)
        # Final Shuffle to ensure the weights learn non-sequentially
        final_df = final_df.sample(frac=1).reset_index(drop=True)
        final_df.to_csv(CSV_PATH, index=False)
        print("-" * 55)
        print(f"[+] Global Equilibrium Reached. Total Samples: {len(final_df)}")
    else:
        print("[+] Already at Equilibrium.")

    print("==========================================================")

if __name__ == "__main__":
    balance_dna()

