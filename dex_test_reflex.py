import requests
import json
import dex_agents
from dex_memory import get_dex_context

def test_brain(prompt):
    print("🧠 Neural Synapse Active...")
    
    # Try strategic planner first (most capable)
    response = dex_agents.strategic_planner(prompt)
    
    if "Offline" in response or "[-]" in response:
        # Fallback to dynamic broker
        response = dex_agents.dynamic_broker(prompt)
    
    return response

def test_brain_social():
    print("💬 Neural Synapse Active...")
    prompt = "Tell me a joke about coding"
    response = dex_agents.social_chat(prompt)
    return response

def test_brain_image():
    print("🎨 Neural Synapse Active...")
    prompt = "A futuristic robot in a cyberpunk city"
    image_url = dex_agents.generate_image(prompt)
    if image_url:
        print(f"✅ Image generated: {image_url}")
    else:
        print("❌ Image generation failed")
    return image_url

def test_brain_cmd():
    print("💻 Neural Synapse Active...")
    prompt = "execute:ls -la"
    response = dex_agents.local_cmd(prompt)
    return response

def test_brain_surgery():
    print("🔧 Neural Synapse Active...")
    prompt = "minor: fix any typos in the code files"
    for chunk in dex_agents.aider_surgery(prompt):
        print(chunk, end="")
    return True

def test_brain_review():
    print("📋 Neural Synapse Active...")
    prompt = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    response = dex_agents.code_review(prompt)
    return response

def test_brain_memory():
    print("🧠 Memory Module Online...")
    prompt = "What's the current context?"
    context = get_dex_context(prompt)
    return context

if __name__ == "__main__":
    print("=" * 50)
    print("DEX BRAIN REFLEX TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Strategic Planner", test_brain),
        ("Social Chat", test_brain_social),
        ("Image Gen", test_brain_image),
        ("Local CMD", test_brain_cmd),
        ("Aider Surgery", test_brain_surgery),
        ("Code Review", test_brain_review),
    ]
    
    for name, func in tests:
        print(f"\n--- {name} ---")
        try:
            result = func()
            print(f"✅ {name} completed successfully")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
    
    print("\n" + "=" * 50)
    print("TEST SUITE COMPLETE")
    print("=" * 50)
