import os
import pandas as pd

CSV_PATH = os.path.expanduser("~/dex-local/intent_dataset.csv")

# 🧬 THE V2.1 GENESIS DNA (Expanded Baseline)
genesis_data = [
    # 🩺 MEDICAL_SUPPORT (Anxiety De-escalation & Clinical Reasoning)
    {"text": "My chest feels tight, am I having a heart attack?", "label": "MEDICAL_SUPPORT"},
    {"text": "Can you check the symptoms for a pinched ulnar nerve?", "label": "MEDICAL_SUPPORT"},
    {"text": "I'm psyching myself out about this headache again.", "label": "MEDICAL_SUPPORT"},
    {"text": "What are the statistical odds of this being serious?", "label": "MEDICAL_SUPPORT"},
    {"text": "Dex, talk me down, I feel like my breathing is weird.", "label": "MEDICAL_SUPPORT"},
    {"text": "My arm is tingling and I'm panicking.", "label": "MEDICAL_SUPPORT"},
    {"text": "Is it normal for a resting heart rate to fluctuate this much?", "label": "MEDICAL_SUPPORT"},
    {"text": "Tell me why this stomach pain is probably just anxiety.", "label": "MEDICAL_SUPPORT"},
    {"text": "I read WebMD and now I'm freaking out about my symptoms.", "label": "MEDICAL_SUPPORT"},
    {"text": "Give me the clinical facts on muscle twitches.", "label": "MEDICAL_SUPPORT"},
    {"text": "I need medical logic to stop this panic loop.", "label": "MEDICAL_SUPPORT"},
    {"text": "What does a compressed nerve actually feel like?", "label": "MEDICAL_SUPPORT"},
    {"text": "Look up the medical literature on tension headaches.", "label": "MEDICAL_SUPPORT"},
    {"text": "Help me deconstruct this health fear I'm having right now.", "label": "MEDICAL_SUPPORT"},
    {"text": "Am I dying or is this just a panic attack?", "label": "MEDICAL_SUPPORT"},

    # 🦾 AIDER_SURGERY (Local 3060 File Edits & Code Generation)
    {"text": "Perform surgery on dex_telegram.py to fix the UI.", "label": "AIDER_SURGERY"},
    {"text": "Have aider write a new python script called test.py.", "label": "AIDER_SURGERY"},
    {"text": "Modify the CSS in my index.html file.", "label": "AIDER_SURGERY"},
    {"text": "Use the local metal to refactor this function.", "label": "AIDER_SURGERY"},
    {"text": "Open dex_gatekeeper.py and add a new endpoint.", "label": "AIDER_SURGERY"},
    {"text": "Code a new React component and save it as Button.jsx.", "label": "AIDER_SURGERY"},
    {"text": "Can you use aider to fix the syntax error in main.py?", "label": "AIDER_SURGERY"},
    {"text": "Write a python script that pings google and save it to ping.py.", "label": "AIDER_SURGERY"},
    {"text": "Edit the config.json file to change the port to 8080.", "label": "AIDER_SURGERY"},
    {"text": "Initiate local surgery on the HTML template.", "label": "AIDER_SURGERY"},
    {"text": "Wake up the 3060 to build a new data scraper script.", "label": "AIDER_SURGERY"},
    {"text": "Update the logic in dex_agents.py to include a timeout.", "label": "AIDER_SURGERY"},
    {"text": "Aider, write a bash script to backup my files.", "label": "AIDER_SURGERY"},
    {"text": "Refactor the memory archiver using the local metal.", "label": "AIDER_SURGERY"},

    # 🗺️ STRATEGIC_PLANNER (120b High Reasoning & Roadmapping)
    {"text": "How should we architect the next phase of the lab?", "label": "STRATEGIC_PLANNER"},
    {"text": "Let's plan out a new workflow for data ingestion.", "label": "STRATEGIC_PLANNER"},
    {"text": "Dex, give me a strategic roadmap for this project.", "label": "STRATEGIC_PLANNER"},
    {"text": "What is the best architecture for a decentralized app?", "label": "STRATEGIC_PLANNER"},
    {"text": "Help me design the system architecture for V3.", "label": "STRATEGIC_PLANNER"},
    {"text": "What are the pros and cons of moving to a microservices layout?", "label": "STRATEGIC_PLANNER"},
    {"text": "Outline a 3-month development plan for the lab.", "label": "STRATEGIC_PLANNER"},
    {"text": "Strategize a way to reduce API latency across the board.", "label": "STRATEGIC_PLANNER"},
    {"text": "Give me a high-level overview of how we should structure the database.", "label": "STRATEGIC_PLANNER"},
    {"text": "I need a strategic vision for integrating new models next year.", "label": "STRATEGIC_PLANNER"},
    {"text": "Plan a deployment pipeline for the new neural router.", "label": "STRATEGIC_PLANNER"},

    # 🔬 CODE_REVIEW (DeepSeek-V3 Auditor & Security)
    {"text": "Audit the dex_gatekeeper.py file for security leaks.", "label": "CODE_REVIEW"},
    {"text": "Review the code I just wrote for logical flaws.", "label": "CODE_REVIEW"},
    {"text": "Is this bash script safe to run on the Linode?", "label": "CODE_REVIEW"},
    {"text": "Check this python snippet for inefficiencies.", "label": "CODE_REVIEW"},
    {"text": "Do a deep dive code review on the memory middleware.", "label": "CODE_REVIEW"},
    {"text": "Analyze this HTML for cross-site scripting vulnerabilities.", "label": "CODE_REVIEW"},
    {"text": "Are there any memory leaks in this Node.js server?", "label": "CODE_REVIEW"},
    {"text": "Review the PR for the new telegram bot updates.", "label": "CODE_REVIEW"},
    {"text": "Look at my API authentication logic and tell me if it's secure.", "label": "CODE_REVIEW"},
    {"text": "Audit the swarm broker loop for potential infinite loops.", "label": "CODE_REVIEW"},
    {"text": "Check my regex for edge cases.", "label": "CODE_REVIEW"},

    # 🖼️ IMAGE_GEN (Flux Visuals & UI Mockups)
    {"text": "Generate a picture of a cyberpunk laboratory.", "label": "IMAGE_GEN"},
    {"text": "Draw me a logo for the Sovereign Lab.", "label": "IMAGE_GEN"},
    {"text": "Create an image of an astronaut riding a horse.", "label": "IMAGE_GEN"},
    {"text": "Vibe out a UI mockup for a new dashboard.", "label": "IMAGE_GEN"},
    {"text": "Generate a visual representation of a neural network.", "label": "IMAGE_GEN"},
    {"text": "I need a concept art image of a futuristic server rack.", "label": "IMAGE_GEN"},
    {"text": "Render an image of a neon sign that says DEX.", "label": "IMAGE_GEN"},
    {"text": "Make a picture of a robot performing surgery.", "label": "IMAGE_GEN"},
    {"text": "Generate a high-res wallpaper for my phone.", "label": "IMAGE_GEN"},
    {"text": "Create a favicon for the new web app.", "label": "IMAGE_GEN"},

    # 💻 LOCAL_CMD (Strict Bash Execution on Linode)
    {"text": "execute: ls -la", "label": "LOCAL_CMD"},
    {"text": "execute: df -h", "label": "LOCAL_CMD"},
    {"text": "execute: tail -n 50 ~/dex-local/logs/gatekeeper.log", "label": "LOCAL_CMD"},
    {"text": "execute: pwd", "label": "LOCAL_CMD"},
    {"text": "execute: htop", "label": "LOCAL_CMD"},
    {"text": "execute: cat /var/log/syslog", "label": "LOCAL_CMD"},
    {"text": "execute: ping -c 4 google.com", "label": "LOCAL_CMD"},
    {"text": "execute: free -m", "label": "LOCAL_CMD"},
    {"text": "execute: systemctl status nginx", "label": "LOCAL_CMD"},
    {"text": "execute: find . -name '*.py'", "label": "LOCAL_CMD"},
    {"text": "execute: du -sh ~/dex-local", "label": "LOCAL_CMD"},

    # 🐝 SWARM_BROKER (The OpenRouter Free Delegation / General Knowledge)
    {"text": "Write a sci-fi story about a rogue AI.", "label": "SWARM_BROKER"},
    {"text": "Translate this paragraph into Japanese.", "label": "SWARM_BROKER"},
    {"text": "Summarize this long article for me.", "label": "SWARM_BROKER"},
    {"text": "What is the capital of Australia?", "label": "SWARM_BROKER"},
    {"text": "Solve this complex algebra equation.", "label": "SWARM_BROKER"},
    {"text": "Give me a recipe for chocolate chip cookies.", "label": "SWARM_BROKER"},
    {"text": "Explain quantum physics to a five year old.", "label": "SWARM_BROKER"},
    {"text": "Write a polite email declining a job offer.", "label": "SWARM_BROKER"},
    {"text": "What are the rules of chess?", "label": "SWARM_BROKER"},
    {"text": "Tell me a joke.", "label": "SWARM_BROKER"},
    {"text": "Write a poem about a server farm.", "label": "SWARM_BROKER"},
    {"text": "Who won the World Series in 2004?", "label": "SWARM_BROKER"},
    {"text": "Convert 100 kilometers to miles.", "label": "SWARM_BROKER"}
]

def seed_vault():
    print("[*] Initiating Expanded Genesis Protocol...")
    if os.path.exists(CSV_PATH):
        print("[-] Wiping old poisoned vault...")
        os.remove(CSV_PATH)
    
    df = pd.DataFrame(genesis_data)
    
    # Optional: Duplicate and shuffle to create a thicker dataset for the zero-GPU trainer
    # This prevents batch-size crashing if the trainer expects a larger epoch volume
    df_extended = pd.concat([df, df]).sample(frac=1).reset_index(drop=True)
    
    df_extended.to_csv(CSV_PATH, index=False)
    print(f"[+] Genesis Vault seeded with {len(df_extended)} pristine samples (Extended Mode).")
    print("[!] Ready to export to your Zero-GPU Training Environment.")

if __name__ == "__main__":
    seed_vault()


