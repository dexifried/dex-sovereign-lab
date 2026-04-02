#!/usr/bin/env python3
"""DEX Evolution Outpost REST client"""
import requests, json, sys

BASE = "https://Dexifried-dex-evolution-outpost.hf.space"

def call_agent(agent="command", message=""):
    r = requests.post(f"{BASE}/api/agent", json={"agent": agent, "message": message}, timeout=180)
    r.raise_for_status()
    return r.json()

def health():
    r = requests.get(f"{BASE}/api/health", timeout=10)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: dex_outpost.py [health|command|code|research|image|web] [message]")
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "health":
        print(json.dumps(health(), indent=2))
    elif cmd in ("command","code","research","image","web"):
        msg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Hello!"
        result = call_agent(cmd, msg)
        print(result["response"])
    else:
        print(f"Unknown: {cmd}")
