import os
import pandas as pd
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    Trainer, 
    TrainingArguments,
    DataCollatorWithPadding
)
from datasets import Dataset
import gradio as gr

# --- 🛰️ Laboratory Configuration ---
MODEL_ID = "answerdotai/ModernBERT-base"
DATA_PATH = "intent_dataset.csv"
OUTPUT_DIR = "./dex_router_model"

def start_bake():
    if not os.path.exists(DATA_PATH):
        raise gr.Error(f"Critical Failure: {DATA_PATH} not found. Sync DNA first.")

    # 1. Dynamic DNA Audit
    df = pd.read_csv(DATA_PATH)
    unique_labels = sorted(df['label'].unique().tolist())
    num_labels = len(unique_labels)
    
    label2id = {label: i for i, label in enumerate(unique_labels)}
    id2label = {i: label for i, label in enumerate(unique_labels)}
    
    print(f"[*] Brain Expansion Detected: Mapping {num_labels} Neural Pathways...")
    print(f"[*] Pathways: {unique_labels}")

    # 2. Tokenization DNA
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    
    def tokenize_func(examples):
        return tokenizer(examples["text"], truncation=True, padding=True, max_length=128)

    # Convert strings to IDs for the model
    df['label'] = df['label'].map(label2id)
    dataset = Dataset.from_pandas(df)
    tokenized_dataset = dataset.map(tokenize_func, batched=True)

    # 3. Load Model with Dynamic Head Size
    # ignore_mismatched_sizes=True is the key to fixing the 8 vs 9 neuron error
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_ID, 
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True 
    )

    # 4. Training Hyperparameters (Lab Grade)
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        learning_rate=2e-5,
        per_device_train_batch_size=32,
        num_train_epochs=15, 
        weight_decay=0.01,
        evaluation_strategy="no",
        save_strategy="no",
        push_to_hub=False,
        report_to="none",
        fp16=True 
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
    )

    # 5. Execute Bake
    try:
        print("[*] Synaptic Bake Commencing...")
        trainer.train()
        
        # Save the expanded brain
        model.save_pretrained(OUTPUT_DIR)
        tokenizer.save_pretrained(OUTPUT_DIR)
        print("[+] Bake Complete. 9-Intent Matrix Stabilized.")
        return f"✅ Success: {num_labels}-Intent Brain Stabilized."
    except Exception as e:
        raise gr.Error(f"Training failed: {str(e)}")

# --- UI Interface ---
with gr.Blocks(title="Dex Neural Lab") as demo:
    gr.Markdown("# 🧠 Dex Sovereign: Synaptic Bake")
    gr.Markdown("Evolutionary training for the ModernBERT Routing Head.")
    
    with gr.Row():
        status = gr.Textbox(label="System Status", value="Idle")
        bake_btn = gr.Button("🔥 START BAKE", variant="primary")
    
    bake_btn.click(fn=start_bake, outputs=status)

if __name__ == "__main__":
    demo.launch()

