import chromadb
import os

def audit():
    vault_path = os.path.expanduser("~/dex-local/dex_vault")
    if not os.path.exists(vault_path):
        print("[-] Physical Vault directory not found.")
        return

    client = chromadb.PersistentClient(path=vault_path)
    
    print("\n" + "="*30)
    print("   DEX NEURAL AUDIT")
    print("="*30)
    
    collections = ["dex_omniscience", "dex_inspiration"]
    for coll_name in collections:
        try:
            coll = client.get_collection(name=coll_name)
            count = coll.count()
            print(f"Vault: {coll_name:18} | Chunks: {count}")
        except:
            print(f"Vault: {coll_name:18} | Status: EMPTY/MISSING")
    print("="*30 + "\n")

if __name__ == "__main__":
    audit()

