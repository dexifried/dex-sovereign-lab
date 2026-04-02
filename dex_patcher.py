import os

GK_PATH = os.path.expanduser("~/dex-local/dex_gatekeeper.py")
TG_PATH = os.path.expanduser("~/dex-local/dex_telegram.py")

print("[*] Initiating Neural Patch Sequence...")

# -----------------------------------------
# PATCH 1: THE GATEKEEPER (Memory & Filter)
# -----------------------------------------
with open(GK_PATH, "r") as f:
    gk_code = f.read()

# Inject History into the API Model
gk_code = gk_code.replace(
    "class Query(BaseModel):\n    prompt: str", 
    "class Query(BaseModel):\n    prompt: str\n    history: str = \"\""
)

# Extract history from request
gk_code = gk_code.replace(
    "text = query.prompt\n    ", 
    "text = query.prompt\n    history = query.history\n    "
)

# Fuse Volatile Memory with Episodic DNA
gk_code = gk_code.replace(
    "context = dex_agents.pre_process_memory(text)",
    """context = dex_agents.pre_process_memory(text)
    if history:
        context = f"--- RECENT CONVERSATION BUFFER ---\\n{history}\\n\\n--- VAULT DNA ---\\n{context}\""""
)

# Rename old generator and wrap it with a Streaming Filter
gk_code = gk_code.replace("def response_generator():", "def _raw_generator():")

think_filter = """    def response_generator():
        in_think = False
        buf = ""
        for chunk in _raw_generator():
            buf += chunk
            while True:
                if not in_think:
                    if "<think>" in buf:
                        idx = buf.find("<think>")
                        yield buf[:idx]
                        buf = buf[idx+7:]
                        in_think = True
                    else:
                        # Yield safely behind a buffer to catch fragmented <think tags
                        if len(buf) > 10:
                            yield buf[:-10]
                            buf = buf[-10:]
                        break
                else:
                    if "</think>" in buf:
                        idx = buf.find("</think>")
                        buf = buf[idx+8:]
                        in_think = False
                    else:
                        buf = "" # Discard the deep thoughts entirely
                        break
        if buf and not in_think:
            yield buf

    return StreamingResponse(response_generator(), media_type="text/plain")"""

gk_code = gk_code.replace('return StreamingResponse(response_generator(), media_type="text/plain")', think_filter)

with open(GK_PATH, "w") as f:
    f.write(gk_code)
print("[+] Gatekeeper Patched: Volatile Memory & Thought-Stream Filter active.")

# -----------------------------------------
# PATCH 2: TELEGRAM (Passing the Buffer)
# -----------------------------------------
with open(TG_PATH, "r") as f:
    tg_code = f.read()

# Pass the last N messages to the Gatekeeper payload
tg_code = tg_code.replace(
    'json={"prompt": text}', 
    'json={"prompt": text, "history": "\\n".join(chat_buffer[uid][:-1])[-1500:]}'
)

with open(TG_PATH, "w") as f:
    f.write(tg_code)
print("[+] Telegram Bridge Patched: Contextual Uplink enabled.")
print("[*] Patch Sequence Complete.")
