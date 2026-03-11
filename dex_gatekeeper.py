
import os
import uvicorn
import threading
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import dex_agents

from dex_neural_router import neural_router

app = FastAPI(title="Dex Sovereign Gatekeeper", version="2.1.1")

class Query(BaseModel):
    prompt: str
    history: str = "" # 🧠 Volatile Memory Ingestion

class ArchiveQuery(BaseModel):
    transcript: str

@app.post("/execute")
def execute_task(query: Query):
    text = query.prompt
    history = query.history
    
    # 1. INTENT CLASSIFICATION
    intent, confidence, entropy, dist = neural_router.predict_intent(text, temperature=0.8)
    
    print("\n" + "="*50)
    print(f"[*] INCOMING PROMPT: '{text[:50]}...'")
    print(f"[+] RAW BERT ROUTE:  {intent}")
    print(f"[*] VOLATILE MEMORY: {'ACTIVE' if history else 'EMPTY'}")
    print("="*50 + "\n")
    
    if entropy > 2.5 and confidence < 40.0:
        intent = "SWARM_BROKER"

    # 🛡️ DRIFT PROTECTION
    legacy_map = {
        "SOCIAL_CHAT": "MEDICAL_SUPPORT",
        "DYNAMIC_BROKER": "SWARM_BROKER",
        "ACCESS_MEMORY": "MEDICAL_SUPPORT",
        "UPDATE_MEMORY": "SWARM_BROKER"
    }
    if intent in legacy_map:
        intent = legacy_map[intent]

    # 2. EPISODIC & VOLATILE MEMORY FUSION
    context = dex_agents.pre_process_memory(text)
    if history:
        context = f"--- RECENT CONVERSATION BUFFER ---\n{history}\n\n--- VAULT DNA ---\n{context}"

    # 3. RAW SPECIALIST EXECUTION
    def _raw_generator():
        full_response_buffer = []
        yield f"AGENT:{intent}\n"
        
        try:
            if intent == "STRATEGIC_PLANNER":
                for chunk in dex_agents.strategic_planner(text, context):
                    full_response_buffer.append(chunk)
                    yield chunk
            elif intent == "AIDER_SURGERY": 
                for chunk in dex_agents.aider_surgery(text, context): 
                    full_response_buffer.append(chunk)
                    yield chunk
            elif intent == "CODE_REVIEW": 
                for chunk in dex_agents.code_review(text, context):
                    full_response_buffer.append(chunk)
                    yield chunk
            elif intent == "LOCAL_CMD": 
                out = dex_agents.local_cmd(text)
                full_response_buffer.append(out)
                yield out
            elif intent == "MEDICAL_SUPPORT": 
                for chunk in dex_agents.medical_support(text, context):
                    full_response_buffer.append(chunk)
                    yield chunk
            elif intent == "IMAGE_GEN":
                out = dex_agents.generate_image(text)
                full_response_buffer.append(out)
                yield out
            else: 
                for chunk in dex_agents.swarm_broker(text):
                    full_response_buffer.append(chunk)
                    yield chunk
        except Exception as e:
            err_msg = f"\n[-] Mesh Execution Error: {str(e)}"
            full_response_buffer.append(err_msg)
            yield err_msg
        finally:
            # POST-PROCESSOR REFLEX
            full_response_text = "".join(full_response_buffer)
            if full_response_text.strip():
                threading.Thread(
                    target=dex_agents.post_process_memory, 
                    args=(text, full_response_text)
                ).start()

    # 4. STREAMING CORTEX FILTER (<think> Cloaking Device)
    def filtered_generator():
        in_think_block = False
        buffer = ""
        
        for chunk in _raw_generator():
            # Pass the intent header through immediately
            if chunk.startswith("AGENT:"):
                yield chunk
                continue
                
            buffer += chunk
            
            if not in_think_block:
                if "<think>" in buffer:
                    parts = buffer.split("<think>", 1)
                    if parts[0]:
                        yield parts[0]
                    buffer = "<think>" + parts[1]
                    in_think_block = True
                else:
                    # Hold 7 characters back in case a tag is split across network chunks
                    if len(buffer) > 7:
                        yield buffer[:-7]
                        buffer = buffer[-7:]
            
            if in_think_block:
                if "</think>" in buffer:
                    parts = buffer.split("</think>", 1)
                    buffer = parts[1]
                    in_think_block = False

        if not in_think_block and buffer:
            yield buffer

    return StreamingResponse(filtered_generator(), media_type="text/plain")

@app.post("/archive")
def archive_task(query: ArchiveQuery, background_tasks: BackgroundTasks):
    background_tasks.add_task(dex_agents.archive_chat_history, query.transcript)
    return {"status": "Archiving task queued to background"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

