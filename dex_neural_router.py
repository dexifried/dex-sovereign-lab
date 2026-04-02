import os
import gc
import math
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Tuple, Dict, Any

# --- SOVEREIGN CONFIGURATION ---
MODEL_PATH = os.path.expanduser("~/dex-local/dex_router_model")

class DexSovereignRouter:
    """
    Advanced Neural Routing Engine implementing Dynamic Quantization, 
    Temperature-Scaled Softmax, and Shannon Entropy evaluation.
    """
    def __init__(self):
        self.device = torch.device("cpu")
        print(f"[*] Initializing Sovereign Neural Lobe on {self.device}...")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
            raw_model = AutoModelForSequenceClassification.from_pretrained(
                MODEL_PATH,
                low_cpu_mem_usage=True,
                torch_dtype=torch.float32
            )
            raw_model.eval()
            
            # 🔥 ADVANCED: Dynamic CPU Quantization
            # Converts internal Linear layers to INT8 for a massive speed/RAM boost on Linode VMs
            print("[*] Applying Dynamic INT8 Quantization for Linode optimization...")
            self.model = torch.ao.quantization.quantize_dynamic(
                raw_model, 
                {torch.nn.Linear}, 
                dtype=torch.qint8
            ).to(self.device)
            
            # Dynamic Label Extraction
            self.id2label = self.model.config.id2label
            self.label2id = self.model.config.label2id
            
            print(f"[+] Sovereign Router Online. Discovered {len(self.id2label)} Neural Pathways.")
            
        except Exception as e:
            print(f"[-] FATAL Neural Lobe Error: {e}")
            self.model = None
            self.tokenizer = None

    def calculate_shannon_entropy(self, probabilities: torch.Tensor) -> float:
        """
        Calculates the Shannon Entropy (H). High entropy = High Neural Noise.
        """
        epsilon = 1e-10
        entropy = -torch.sum(probabilities * torch.log2(probabilities + epsilon)).item()
        return round(entropy, 4)

    def predict_intent(self, text: str, temperature: float = 1.0) -> Tuple[str, float, float, Dict[str, float]]:
        if not self.model:
            return "SWARM_BROKER", 0.0, 0.0, {}
            
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            padding=True, 
            max_length=128
        ).to(self.device)
        
        with torch.no_grad():
            logits = self.model(**inputs).logits
            
        # Temperature Scaling to sharpen/flatten the distribution
        scaled_logits = logits / temperature
        probs = torch.nn.functional.softmax(scaled_logits, dim=-1)[0]
        
        pred_idx = torch.argmax(probs).item()
        confidence = round(float(probs[pred_idx]) * 100, 2)
        
        # 🔥 CRITICAL FIX: HF Configs serialize integers to string keys in JSON.
        # We must check both integer and string representations to avoid defaulting.
        intent = self.id2label.get(pred_idx, self.id2label.get(str(pred_idx), "SWARM_BROKER"))
        
        entropy = self.calculate_shannon_entropy(probs)
        distribution = {self.id2label.get(i, self.id2label.get(str(i), str(i))): round(float(probs[i]) * 100, 2) for i in range(len(probs))}
        
        # Aggressive memory cleanup
        del inputs, logits, scaled_logits, probs
        gc.collect()
        
        return intent, confidence, entropy, distribution

# Singleton instance
neural_router = DexSovereignRouter()


