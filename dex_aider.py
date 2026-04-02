import requests
import os
import re

# --- HARDWARE MAP ---
OLLAMA_URL = "http://100.65.179.80:11434/api/generate"
MODEL = "qwen3.5:9b"

def get_context():
    """Gathers all core files and logs into a single context stream."""
    context = ""
    files = ["dex_gatekeeper.py", "dex_agents.py", "dex_memory.py", "dex_telegram.py", "gatekeeper.log"]
    for f_name in files:
        path = os.path.expanduser(f"~/dex-local/{f_name}")
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()
                context += f"\n--- FILE: {f_name} ---\n{content}\n"
    return context

def apply_edits(response):
    """Parses the Agent's output and executes file overwrites."""
    # Look for @@@WRITE:filename@@@ ... @@@END@@@ blocks
    pattern = r"@@@WRITE:(.*?)@@@\n(.*?)@@@END@@@"
    matches = re.findall(pattern, response, re.DOTALL)
    
    if not matches:
        print("[!] No autonomous edits detected in response.")
        return False

    for filename, content in matches:
        path = os.path.expanduser(f"~/dex-local/{filename.strip()}")
        print(f"[*] AIDER: Overwriting {filename.strip()}...")
        with open(path, 'w') as f:
            f.write(content.strip())
    return True

def run_aider(task="Fix the system"):
    print(f"[*] DEX AIDER: Engaging 3060 node for autonomous repair...")
    
    system_prompt = (
        "You are the Dex Aider Agent. You have READ/WRITE access to the filesystem. "
        "Analyze the provided files and logs. If there is a crash, fix it. "
        "To write a file, use the format: @@@WRITE:filename@@@\n{content}\n@@@END@@@. "
        "Output ONLY the write blocks and a brief explanation."
    )

    full_prompt = f"SYSTEM CONTEXT:\n{get_context()}\n\nTASK: {task}"

    try:
        r = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": full_prompt,
            "system": system_prompt,
            "stream": False
        }, timeout=120)
        
        response = r.json().get("response", "")
        print("\n--- AGENT REASONING ---")
        print(response)
        
        if apply_edits(response):
            print("\n[+] Autonomous Repair Complete. Run 'dex-gram' to reboot.")
        
    except Exception as e:
        print(f"[-] Aider Error: {e}")

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "Fix the Gatekeeper crash."
    run_aider(query)

