import pandas as pd
import os
import random

# --- Configuration ---
CSV_PATH = os.path.expanduser("~/dex-local/intent_dataset.csv")
TARGET_LABEL = "IMAGE_GEN"
# We want to reach about 200 total for this class. 
# If you have ~40 now, we add 160.
BOOST_COUNT = 160 

# Diverse templates to cover every way you/your girlfriend might ask
templates = [
    "Can you make me a picture of {t}",
    "Generate an image of {t}",
    "Visualize {t} for me",
    "Show me what {t} looks like",
    "Draw {t}",
    "Dex, create a visual of {t}",
    "I want to see {t}",
    "Can you render {t}?",
    "Hey, make a cool photo of {t}",
    "Visualize this: {t}",
    "Can you do an image for {t}?",
    "Create a high-res image of {t}",
    "I need an illustration of {t}",
    "Paint a picture of {t}",
    "Render a scene with {t}",
    "Give me a visual for {t}"
]

subjects = [
    "a baby highland cow in a green field", "a cyberpunk hacker den with neon lights", 
    "a futuristic city floating in the clouds", "a dragon ball z style training room",
    "a gothic cathedral at midnight", "a space marine in heavy armor", 
    "a cozy log cabin in a snowstorm", "a surreal landscape with purple grass",
    "a hyper-realistic portrait of an android", "a fantasy map of a hidden island",
    "a 3d blueprint of a neural network", "a vintage polaroid of a busy street",
    "a cinematic shot of a samurai in the rain", "an abstract painting of pure energy",
    "a retro 80s arcade interior", "a deep sea exploration vessel",
    "a majestic eagle soaring over mountains", "a crystal cavern glowing with blue light"
]

def boost_signal():
    if not os.path.exists(CSV_PATH):
        print(f"[-] Error: {CSV_PATH} not found.")
        return

    # Load current DNA
    df = pd.read_csv(CSV_PATH)
    
    # Calculate how many we actually need to hit 200
    current_count = len(df[df['label'] == TARGET_LABEL])
    needed = max(0, 200 - current_count)
    
    print(f"[*] Current {TARGET_LABEL} count: {current_count}")
    print(f"[*] Injecting {needed} synthetic samples...")

    new_data = []
    for _ in range(needed):
        text = random.choice(templates).format(t=random.choice(subjects))
        new_data.append({"text": text, "label": TARGET_LABEL})
    
    boost_df = pd.DataFrame(new_data)
    final_df = pd.concat([df, boost_df], ignore_index=True)
    
    # Shuffle the brain so synthetic and real-world feedback are mixed
    final_df = final_df.sample(frac=1).reset_index(drop=True)
    
    # Save the reinforced DNA
    final_df.to_csv(CSV_PATH, index=False)

    print(f"[+] Total {TARGET_LABEL} count is now: {len(final_df[final_df['label'] == TARGET_LABEL])}")
    print(f"[+] Total Dataset Size: {len(final_df)}")
    print("==========================================================")
    print("🏁 DNA REINFORCED. READY FOR FINAL AUDIT.")
    print("==========================================================")

if __name__ == "__main__":
    boost_signal()

