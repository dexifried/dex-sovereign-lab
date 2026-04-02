import torch
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Pointing STRICTLY to the new 50GB Model Vault download
MODEL_PATH = os.path.expanduser("~/dex-local/dex_router_model")

def interrogate_brain():
    print("==========================================================")
    print("🧠 DIRECT CORTEX INTERROGATION (BYPASSING TELEGRAM)")
    print("==========================================================")
    
    if not os.path.exists(MODEL_PATH):
        print(f"[-] FATAL: Cannot find new brain at {MODEL_PATH}")
        return

    print(f"[*] Loading raw weights from: {MODEL_PATH}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    
    # The exact prompt that failed
    test_prompt = "Can you make me a picture of a baby highland cow"
    print(f"\n[?] Injecting Prompt: '{test_prompt}'")
    
    inputs = tokenizer(test_prompt, return_tensors="pt", truncation=True, max_length=128)
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        predicted_idx = logits.argmax(-1).item()
        confidence = torch.softmax(logits, dim=-1)[0][predicted_idx].item() * 100
        
        predicted_intent = model.config.id2label[predicted_idx]
        
    print(f"\n[+] NEURAL ROUTING RESULT: {predicted_intent}")
    print(f"[+] CONFIDENCE LEVEL:      {confidence:.2f}%")
    print("==========================================================")
    
    if predicted_intent == "IMAGE_GEN":
        print("\n✅ DIAGNOSIS: The Brain is perfect. Telegram is loading the WRONG FOLDER or stuck in RAM.")
    else:
        print("\n❌ DIAGNOSIS: The Bake itself failed to generalize. We have a fundamental data issue.")

if __name__ == "__main__":
    interrogate_brain()

