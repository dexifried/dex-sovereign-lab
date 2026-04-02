
import os
import json
import re
import subprocess
import requests
import random
import collections
import time
import traceback
import base64
from datetime import datetime
from typing import Dict, List, Generator, Any, Optional
from dotenv import load_dotenv

import chromadb
# Assuming you have a basic embedding function wrapper in dex_memory. 
# For V2.1, we will bypass it for explicit DeepInfra API calls where needed.
from dex_memory import get_dex_context, DeepInfraEmbeddingFunction 

# ==========================================
# 📁 SYSTEM PATHS & CONFIGURATION DNA
# ==========================================
P_DIR: str = os.path.expanduser("~/dex-local")
P_CONFIG: str = os.path.join(P_DIR, "dex_config.json")
P_AID: str = os.path.join(P_DIR, "aider-dex.sh")
P_LEDGER: str = os.path.join(P_DIR, "surgical_ledger.md")
P_VAULT: str = os.path.join(P_DIR, "dex_vault")

# Load the hidden environment variables strictly from the Dex root folder
load_dotenv(os.path.join(P_DIR, ".env"))

def load_config() -> Dict[str, Any]:
    if os.path.exists(P_CONFIG):
        try:
            with open(P_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[-] FATAL: Corrupted config DNA. {e}")
    return {"models": {}, "parameters": {}}

CONFIG: Dict[str, Any] = load_config()
MODELS: Dict[str, str] = CONFIG.get("models", {})
PARAMS: Dict[str, Any] = CONFIG.get("parameters", {})

# ==========================================
# 🔑 CORE API KEYS & ENDPOINTS (.ENV SECURED)
# ==========================================
CEREBRAS_KEY: str = os.getenv("CEREBRAS_KEY", "")
DEEP_INFRA_KEY: str = os.getenv("DEEP_INFRA_KEY", "")
OPENROUTER_KEY: str = os.getenv("OPENROUTER_KEY", "")
GROQ_KEY: str = os.getenv("GROQ_KEY", "")
SAMBANOVA_KEY: str = os.getenv("SAMBANOVA_KEY", "")

# Startup Diagnostic Warning
if not any([DEEP_INFRA_KEY, OPENROUTER_KEY, SAMBANOVA_KEY, CEREBRAS_KEY]):
    print("[-] OPSEC WARNING: No API keys found in .env. Neural pathways will fail.")

U_CER: str = "https://api.cerebras.ai/v1/chat/completions"
U_GRQ: str = "https://api.groq.com/openai/v1/chat/completions"
U_DPI: str = "https://api.deepinfra.com/v1/openai/chat/completions"
U_SMB: str = "https://api.sambanova.ai/v1/chat/completions"
U_IMG: str = "https://api.deepinfra.com/v1/openai/images/generations"

TICK: str = chr(96) * 3 

# ==========================================
# 🐝 THE SWARM MATRIX (OPENROUTER FREE)
# ==========================================
SWARM_MODELS = [
    "arcee-ai/trinity-large-preview:free", "arcee-ai/trinity-mini:free",
    "nousresearch/hermes-3-405b:free", "venice/uncensored:free",
    "nvidia/llama-nemotron-embed-vl-1b-v2:free", "stepfun/step-3-5-flash:free",
    "liquid/lfm-2.5-1.2b-thinking:free", "liquid/lfm-2.5-1.2b-instruct:free",
    "nvidia/nemotron-3-30b-a3b:free", "nvidia/nemotron-nano-12b-2-vl:free",
    "qwen/qwen3-next-80b-a3b-instruct:free", "nvidia/nemotron-nano-9b-v2:free",
    "openai/gpt-oss-120b:free", "openai/gpt-oss-20b:free",
    "z-ai/glm-4-5-air:free", "qwen/qwen3-coder-480b-a35b:free",
    "google/gemma-3n-2b:free", "google/gemma-3n-4b:free",
    "qwen/qwen3-4b:free", "mistralai/mistral-small-3.1-24b:free",
    "google/gemma-3-4b:free", "google/gemma-3-12b:free", "google/gemma-3-27b:free"
]

# ==========================================
# 🗄️ COGNITIVE MIDDLEWARE (PRE/POST REFLEXES)
# ==========================================
def pre_process_memory(user_prompt: str) -> str:
    """Reflex 1: Fetches base context from Chroma, then uses Qwen3-Reranker to filter."""
    print("[*] Executing Pre-Processor Qwen3 Reranker...")
    try:
        raw_context = get_dex_context(user_prompt)
        if not raw_context or raw_context.strip() == "":
            return ""
            
        docs = [chunk for chunk in raw_context.split("\n\n") if len(chunk) > 20]
        if not docs: return raw_context
        
        rerank_url = 'https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-8B'
        payload = {"queries": [user_prompt], "documents": docs[:10]}
        
        r = requests.post(rerank_url, headers={"Authorization": f"bearer {DEEP_INFRA_KEY}"}, json=payload, timeout=5)
        if r.status_code == 200:
            results = r.json()
            if 'results' in results:
                top_docs = [res['document'] for res in sorted(results['results'], key=lambda x: x.get('score', 0), reverse=True)[:3]]
                return "\n\n".join(top_docs)
        return raw_context 
    except Exception as e:
        print(f"[-] Reranker Exception: {e}")
        return ""

def post_process_memory(user_prompt: str, output: str) -> None:
    """Reflex 2: Explicitly uses Qwen3-Embedding-8B to fuse interaction to Vault."""
    print("[*] Executing Post-Processor Qwen3 Embedder...")
    try:
        fact_str = f"User asked: {user_prompt}\nDex response: {output[:500]}..."
        
        embed_url = 'https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Embedding-8B'
        r = requests.post(embed_url, headers={"Authorization": f"bearer {DEEP_INFRA_KEY}"}, json={"inputs": [fact_str]}, timeout=10)
        
        if r.status_code == 200:
            embeddings = r.json().get('embeddings', [None])[0]
            if embeddings:
                client = chromadb.PersistentClient(path=P_VAULT)
                collection = client.get_or_create_collection(name="dex_omniscience", embedding_function=DeepInfraEmbeddingFunction())
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                chunk_id = f"reflex_{timestamp.replace(' ', '_').replace(':', '')}"
                
                collection.upsert(
                    documents=[fact_str], 
                    embeddings=[embeddings], 
                    metadatas=[{"source": "interleaved_reflex", "type": "episodic_memory", "timestamp": timestamp}], 
                    ids=[chunk_id]
                )
                print("[+] Memory Reflex Fused to Vault.")
    except Exception as e:
        print(f"[-] Embedder Exception: {e}")

def archive_chat_history(transcript: str) -> str:
    """Preserved background task for Telegram buffer flushing."""
    try:
        client = chromadb.PersistentClient(path=P_VAULT)
        collection = client.get_or_create_collection(name="dex_conversations", embedding_function=DeepInfraEmbeddingFunction())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chunk_id = f"chat_log_{timestamp.replace(' ', '_').replace(':', '')}"
        collection.upsert(documents=[f"EPISODIC LOG ({timestamp})\n{transcript}"], metadatas=[{"source": "telegram_buffer", "type": "episodic_memory", "timestamp": timestamp}], ids=[chunk_id])
        return "Success"
    except Exception as e: return str(e)

# ==========================================
# 🩺 MEDICAL SUPPORT (DeepSeek R1/V3)
# ==========================================
def medical_support(user_prompt: str, context: str) -> Generator[str, None, None]:
    """Replaces social_chat. Primary: SambaNova R1. Failover: DeepInfra V3.2."""
    print("[*] Waking DeepSeek Medical Specialists...")
    
    system_prompt = (
        "You are a specialized Medical Logic and Reassurance Agent. Your goal is to provide evidence-based "
        "medical facts while explicitly identifying and de-escalating health anxiety loops (catastrophizing). "
        "Acknowledge the fear, provide the most likely benign explanation first, and use clinical statistics "
        "to logically deconstruct improbable worst-case scenarios. Do NOT give generic 'Go to the ER' "
        "disclaimers unless it is an absolute undeniable emergency. Be empathetic, highly logical, and calming."
    )
    
    final_prompt = user_prompt
    if context and context.strip() != "":
        final_prompt = f"Historical Lab Context regarding this patient:\n{context}\n\nPatient Query:\n{user_prompt}"

    payload = {
        "model": "DeepSeek-R1-0528",
        "stream": True,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_prompt}
        ]
    }
    
    try:
        response = requests.post(
            U_SMB, 
            headers={"Authorization": f"Bearer {SAMBANOVA_KEY}", "Content-Type": "application/json"}, 
            json=payload, stream=True, timeout=(10, 60)
        )
        if response.status_code == 200:
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith('data: '):
                    data_str = line[6:].strip()
                    if data_str == '[DONE]': break
                    try:
                        content = json.loads(data_str).get('choices', [{}])[0].get('delta', {}).get('content', '')
                        if content: yield content
                    except Exception: continue
            return 
    except Exception as e:
        print(f"[-] SambaNova R1 Failed: {e}. Failing over to DeepInfra V3.2...")

    payload["model"] = "deepseek-ai/DeepSeek-V3.2"
    try:
        response = requests.post(
            U_DPI, 
            headers={"Authorization": f"Bearer {DEEP_INFRA_KEY}", "Content-Type": "application/json"}, 
            json=payload, stream=True, timeout=(10, 60)
        )
        if response.status_code == 200:
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith('data: '):
                    data_str = line[6:].strip()
                    if data_str == '[DONE]': break
                    try:
                        content = json.loads(data_str).get('choices', [{}])[0].get('delta', {}).get('content', '')
                        if content: yield content
                    except Exception: continue
        else:
            yield f"[-] Medical Subsystem Offline. Both R1 and V3.2 nodes failed. Status: {response.status_code}"
    except Exception as e:
        yield f"[-] Medical Failover Exception: {traceback.format_exc()}"

# ==========================================
# 🧠 CEREBRAS 120B: TRUE STREAMING ORACLE
# ==========================================
def strategic_planner(user_prompt: str, context: str) -> Generator[str, None, None]:
    print(f"[*] Waking Cerebras Oracle...")
    payload = {
        "model": "qwen-3-235b-a22b-instruct-2507",
        "stream": True,
        "max_tokens": PARAMS.get("cerebras_max_tokens", 32768),
        "temperature": 1.0,
        "messages": [
            {"role": "system", "content": f"You are the Dex Strategist. Use this Memory DNA:\n\n{context}"}, 
            {"role": "user", "content": user_prompt}
        ]
    }
    try:
        response = requests.post(U_CER, headers={"Authorization": f"Bearer {CEREBRAS_KEY}", "Content-Type": "application/json"}, json=payload, stream=True, timeout=(10, 300))
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                data_str = line[6:].strip()
                if data_str == '[DONE]': break
                try:
                    content = json.loads(data_str).get('choices', [{}])[0].get('delta', {}).get('content', '')
                    if content: yield content
                except Exception: continue
    except Exception as e: yield f"\n[-] Cerebras Exception: {traceback.format_exc()}"

# ==========================================
# 🔬 SAMBANOVA DEEPSEEK-V3: STREAMING AUDITOR
# ==========================================
def code_review(user_prompt: str, context: str) -> Generator[str, None, None]:
    print("[*] Waking SambaNova DeepSeek-V3 for Code Audit...")
    
    if context and len(context) > 4000:
        context = context[:4000] + "\n...[Context Truncated for SambaNova Stability]"

    system_prompt = (
        "You are an elite Staff Engineer and ruthless code auditor for 'Dex'. "
        "CRITICAL CONTEXT: Dex is a sovereign multi-agentic AI lab framework and personal AI architecture project. "
        "Focus strictly on Python, ML architecture, API integrations, logic flaws, security leaks, and code inefficiencies."
    )
    
    final_prompt = user_prompt
    if context and context.strip() != "":
        final_prompt = f"Lab Context:\n{context}\n\nTask:\n{user_prompt}"
        
    payload = {
        "model": "DeepSeek-V3-0324",
        "stream": True,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_prompt}
        ]
    }
    
    try:
        response = requests.post(
            U_SMB, 
            headers={"Authorization": f"Bearer {SAMBANOVA_KEY}", "Content-Type": "application/json"}, 
            json=payload, 
            stream=True, 
            timeout=(10, 300)
        )
        
        if response.status_code != 200:
            yield f"[-] SambaNova API Error {response.status_code}: {response.text}"
            return
            
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                data_str = line[6:].strip()
                if data_str == '[DONE]': break
                try:
                    data_json = json.loads(data_str)
                    content = data_json.get('choices', [{}])[0].get('delta', {}).get('content', '')
                    if content: yield content
                except Exception: continue
    except Exception as e: 
        yield f"\n[-] SambaNova Streaming Exception: {traceback.format_exc()}"

# ==========================================
# 🦾 3060 SURGERY: LOCAL AIDER HARDLINE
# ==========================================
def log_to_ledger(prompt: str, output: str) -> None:
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(P_LEDGER, "a", encoding='utf-8') as f: f.write(f"\n## Surgery: {timestamp}\n**Task:** {prompt}\n**Result:**\n{TICK}diff\n{output[-3000:]}\n{TICK}\n")

def aider_surgery(user_prompt: str, context: str) -> Generator[str, None, None]:
    print("[*] Surgery triggered: Routing to 3060 Hardline...")
    history_file: str = os.path.join(P_DIR, ".aider.chat.history.md")
    if os.path.exists(history_file): 
        try: os.remove(history_file)
        except Exception: pass
        
    sanitized: str = re.sub(r'[;`$]', '', user_prompt)
    potential_files = re.findall(r'[\w\-]+\.(?:py|json|csv|md|sh|txt|html|css|jsx|tsx)', sanitized)
    valid_files = [f for f in set(potential_files) if os.path.exists(os.path.join(P_DIR, f))]
    
    model_flag = MODELS.get("local_surgeon", "ollama_chat/qwen3.5:9b")
    cmd = ["bash", P_AID, "--model", model_flag, "--message", f"DIRECTIVE: Use this DNA context to guide the edit.\n\nDNA:\n{context}\n\nTask: {sanitized}"] + valid_files
    
    try:
        process = subprocess.Popen(cmd, cwd=P_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        window = collections.deque(maxlen=20)
        full_output_list = []
        for line in iter(process.stdout.readline, ''):
            full_output_list.append(line)
            window.append(line.replace('\n', ''))
            yield f"[CLEAR]Live 3060 Feed ({model_flag}):\n\n{TICK}text\n" + "\n".join(window) + f"\n{TICK}"
        process.wait()
        full_output = "".join(full_output_list)
        if process.returncode == 0:
            log_to_ledger(sanitized, full_output)
            yield f"[CLEAR]✅ <b>Surgery Complete & Vault Updated.</b>\n\n{TICK}text\n{full_output[-1500:]}\n{TICK}"
        else:
            yield f"[CLEAR]❌ <b>Surgery Failed (Exit {process.returncode}).</b>"
    except Exception as e: yield f"[CLEAR][-] Bridge Error: {traceback.format_exc()}"

# ==========================================
# 🛡️ THE SWARM FAILOVER & UTILITIES
# ==========================================
def swarm_broker(user_prompt: str) -> Generator[str, None, None]:
    """The 'Offline' Killer: Ripples through 20+ Free OpenRouter models until one answers."""
    random.shuffle(SWARM_MODELS) 
    
    yield "🐝 <b>[ SWARM DELEGATION INITIATED ]</b>\n<i>Scanning OpenRouter Free Tier...</i>\n\n"
    
    for model in SWARM_MODELS:
        try:
            print(f"[*] Swarm Attempt: {model}")
            payload = {
                "model": model, 
                "messages": [{"role": "user", "content": user_prompt}],
                "stream": True
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions", 
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}, 
                json=payload, stream=True, timeout=8 
            )
            
            if response.status_code == 200:
                yield f"✅ <b>Agent Secured:</b> <code>{model}</code>\n\n"
                
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith('data: '):
                        data_str = line[6:].strip()
                        if data_str == '[DONE]': break
                        try:
                            content = json.loads(data_str).get('choices', [{}])[0].get('delta', {}).get('content', '')
                            if content: yield content
                        except Exception: continue
                return 
        except Exception as e:
            print(f"[-] Node {model} offline. Rippling to next...")
            continue
            
    yield "❌ <b>Swarm Exhausted.</b> All 20+ free nodes are currently offline or rate-limited."

def generate_image(user_prompt: str) -> str:
    try:
        payload = {
            "prompt": user_prompt,
            "size": "1024x1024",
            "model": "black-forest-labs/FLUX-2-klein-9b",
            "n": 1
        }
        r = requests.post(U_IMG, headers={"Authorization": f"Bearer {DEEP_INFRA_KEY}", "Content-Type": "application/json"}, json=payload, timeout=45)
        if r.status_code != 200: return f"[-] Visual Cortex Error ({r.status_code})."
        
        b64_data = r.json().get("images", [None])[0]
        if not b64_data: return "[-] Image Gen payload empty."
        if b64_data.startswith("data:image"): b64_data = b64_data.split(",")[1]
        
        image_bytes = base64.b64decode(b64_data)
        files = {'reqtype': (None, 'fileupload'), 'fileToUpload': ('dex_flux_render.png', image_bytes, 'image/png')}
        upload_r = requests.post('https://catbox.moe/user/api.php', files=files, timeout=20)
        
        return f"🖼️ **Visual Cortex Generation Complete:**\n{upload_r.text.strip()}" if upload_r.status_code == 200 else "[-] Catbox Upload Failed."
    except Exception as e: return f"[-] Image API execution error: {str(e)}"

def local_cmd(user_prompt: str) -> str:
    try:
        cmd = user_prompt.split("execute:")[-1].strip()
        ALLOWED = ["ls", "pwd", "cat", "grep", "find", "echo", "head", "tail", "bash", "python3", "hf", "git", "aider", "rm", "mv", "cp"]
        if not cmd.split() or cmd.split()[0].lower() not in ALLOWED: return "[-] Unauthorized command."
        out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT, timeout=60)
        return f"{TICK}bash\n{out[:3000]}\n{TICK}"
    except Exception as e: return f"[-] CMD Error: {e}"
