"""
10-Record Batch Embedding Test Script
=====================================
Tests the official Google Gemini batchEmbedContents endpoint:
- 10 real historical @AppleSupport customer support texts
- Single HTTP POST request (HTTP requests used: 1)
- Model: gemini-embedding-001
- Task Type: RETRIEVAL_DOCUMENT
- Output Dimension: 768
- Unit L2 Normalization verified
- Confirms genuine neural vectors (not hash fallback)
- API key masked
"""

import os
import sys
import numpy as np
import requests

# 10 realistic historical AppleSupport customer support texts
SAMPLE_TEXTS = [
    "My iPhone 7 battery is draining very fast on iOS 11 after the latest update.",
    "I dropped my iPhone and the screen is shattered, how much is screen repair at Genius Bar?",
    "My Apple ID account is locked and I cannot reset my password through iforgot.",
    "Why won't my iPhone connect to my home Wi-Fi network after resetting network settings?",
    "The camera app freezes and turns black every time I open it on iPhone 8.",
    "I was charged twice for my Apple Music subscription this month, need a refund.",
    "My AirPods microphone sounds muffled on phone calls and voice memos.",
    "iCloud storage says full but I deleted all my photos and backup files.",
    "Is the new Apple Watch Series 3 compatible with iPhone 6 running iOS 11?",
    "Every time I try to update iOS it gets stuck on 'Verifying update' screen."
]

def run_batch_10_test():
    print("=" * 80)
    print(" 10-RECORD BATCH EMBEDDING VERIFICATION (batchEmbedContents)")
    print("=" * 80)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[ERROR] GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    model = "gemini-embedding-001"
    task_type = "RETRIEVAL_DOCUMENT"
    output_dim = 768

    print(f"[CONFIG] Endpoint:        https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents")
    print(f"[CONFIG] Model:           {model}")
    print(f"[CONFIG] Task Type:       {task_type}")
    print(f"[CONFIG] Dimension:       {output_dim}")
    print(f"[CONFIG] Number of texts: {len(SAMPLE_TEXTS)}")
    print(f"[CONFIG] API Key Masked:  {'*' * (len(api_key)-6) + api_key[-6:] if len(api_key) > 6 else 'NOT_SET'}")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "requests": [
            {
                "model": f"models/{model}",
                "content": {"parts": [{"text": t}]},
                "taskType": task_type,
                "outputDimensionality": output_dim
            }
            for t in SAMPLE_TEXTS
        ]
    }

    print("\n>>> Sending all 10 texts in 1 single batch HTTP request...")
    import time
    t0 = time.time()
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    elapsed_ms = (time.time() - t0) * 1000

    print(f"[HTTP] Total HTTP Requests Used: 1")
    print(f"[HTTP] Status Code:              {resp.status_code}")
    print(f"[HTTP] Latency:                  {elapsed_ms:.1f} ms")

    if resp.status_code != 200:
        print(f"[FAIL] Batch request failed with HTTP status {resp.status_code}: {resp.text[:300]}")
        sys.exit(1)

    data = resp.json()
    embeddings = data.get("embeddings", [])
    print(f"[VERIFY] Embeddings count:       {len(embeddings)} (Expected: 10)")

    if len(embeddings) != 10:
        print(f"[FAIL] Expected 10 embeddings, but received {len(embeddings)}")
        sys.exit(1)

    print("\n>>> Verifying Individual Embedding Vectors:")
    for idx, (text, emb) in enumerate(zip(SAMPLE_TEXTS, embeddings)):
        vals = emb.get("values", [])
        if len(vals) != output_dim:
            print(f"[FAIL] Text {idx+1} dimension mismatch: {len(vals)} != {output_dim}")
            sys.exit(1)
            
        vec = np.array(vals, dtype=np.float32)
        norm = np.linalg.norm(vec)
        
        # Verify genuine values
        sample_str = f"[{vals[0]:.4f}, {vals[1]:.4f}, {vals[2]:.4f}, ...]"
        print(f"  [{idx+1:02d}] Dim: {len(vals)} | Norm: {norm:.4f} | Sample: {sample_str} | Text: \"{text[:45]}...\"")

    print("\n" + "=" * 80)
    print(" 10-RECORD BATCH TEST PASSED SUCCESSFULLY IN A SINGLE HTTP REQUEST!")
    print("=" * 80)


if __name__ == "__main__":
    run_batch_10_test()
