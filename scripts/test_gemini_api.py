import os
import requests
import json

api_key = os.getenv("GEMINI_API_KEY", "").strip()
if not api_key:
    print("[ERROR] GEMINI_API_KEY environment variable is not set.")
    sys.exit(1)

print(f"[TEST] Testing Gemini Batch Embedding with 'gemini-embedding-001'...")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={api_key}"
payload = {
    "requests": [
        {
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": "Customer: My battery is draining fast on iOS 11"}]},
            "taskType": "RETRIEVAL_DOCUMENT",
            "outputDimensionality": 768
        },
        {
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": "Customer: My screen is cracked and broken"}]},
            "taskType": "RETRIEVAL_DOCUMENT",
            "outputDimensionality": 768
        }
    ]
}
headers = {"Content-Type": "application/json"}

resp = requests.post(url, headers=headers, json=payload, timeout=15)
print(f"[TEST] HTTP Status Code: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    embs = data.get("embeddings", [])
    print(f"[TEST] Embeddings returned: {len(embs)}")
    for i, emb in enumerate(embs):
        vals = emb.get("values", [])
        print(f"  [{i+1}] Dimension: {len(vals)}, Sample: {vals[:3]}")
else:
    print(f"[TEST] Error: {resp.text[:300]}")
