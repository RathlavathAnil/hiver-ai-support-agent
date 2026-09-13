"""
Small Real Gemini Embedding Test Script
=======================================
Verifies genuine semantic embedding generation via Google Gemini API:
- Model: gemini-embedding-001
- Task Type: RETRIEVAL_QUERY
- Dimension: 768
- Confirms vector is NOT deterministic hash fallback
- Safe logging (no API key printed)
"""

import os
import sys
import numpy as np
import requests
from seed_db import compute_fallback_embedding, EMBEDDING_DIM

def run_small_gemini_test():
    print("=" * 80)
    print(" SMALL REAL GEMINI EMBEDDING VERIFICATION TEST")
    print("=" * 80)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[ERROR] GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    model = "gemini-embedding-001"
    task_type = "RETRIEVAL_QUERY"
    query_text = "my iPhone battery is draining very quickly"

    print(f"[CONFIG] Target Provider:  Google Gemini REST Embedding API")
    print(f"[CONFIG] Model Resource:   {model}")
    print(f"[CONFIG] Task Type:        {task_type}")
    print(f"[CONFIG] Target Dimension: {EMBEDDING_DIM}")
    print(f"[CONFIG] Test Query:       '{query_text}'")
    print(f"[CONFIG] API Key Masked:   {'*' * (len(api_key)-6) + api_key[-6:] if len(api_key) > 6 else 'NOT_SET'}")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"
    payload = {
        "model": f"models/{model}",
        "content": {"parts": [{"text": query_text}]},
        "taskType": task_type,
        "outputDimensionality": EMBEDDING_DIM
    }
    headers = {"Content-Type": "application/json"}

    print("\n>>> Executing Live HTTP POST to Google Gemini Endpoint...")
    start_time = time.time() if "time" in dir() else 0
    import time
    t0 = time.time()
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    elapsed_ms = (time.time() - t0) * 1000

    print(f"[HTTP] Status Code: {resp.status_code}")
    print(f"[HTTP] Latency:     {elapsed_ms:.1f} ms")

    if resp.status_code != 200:
        print(f"[FATAL ERROR] API call failed with status {resp.status_code}: {resp.text[:300]}")
        sys.exit(1)

    data = resp.json()
    gemini_vec = data.get("embedding", {}).get("values", [])
    
    print(f"\n>>> Verifying Generated Vector...")
    print(f"[VERIFY] Output Dimension:      {len(gemini_vec)} (Expected: 768)")
    if len(gemini_vec) != 768:
        print(f"[FAIL] Dimension mismatch: expected 768, got {len(gemini_vec)}")
        sys.exit(1)

    # Compute deterministic hash fallback for comparison
    fallback_vec = compute_fallback_embedding(query_text, EMBEDDING_DIM)

    # Calculate L2 norms and difference
    gemini_np = np.array(gemini_vec, dtype=np.float32)
    fallback_np = np.array(fallback_vec, dtype=np.float32)

    gemini_norm = np.linalg.norm(gemini_np)
    cosine_diff = 1.0 - (np.dot(gemini_np, fallback_np) / (gemini_norm * np.linalg.norm(fallback_np)))

    print(f"[VERIFY] L2 Norm of Vector:     {gemini_norm:.6f}")
    print(f"[VERIFY] First 5 Float Values:  {gemini_vec[:5]}")
    print(f"[VERIFY] First 5 Fallback Hash: {fallback_vec[:5]}")
    print(f"[VERIFY] Vector Difference:     {cosine_diff:.4f} (Confirms not fallback hash)")

    if cosine_diff < 0.05:
        print("[FAIL] Generated vector is identical to fallback hash vector!")
        sys.exit(1)

    print("\n" + "=" * 80)
    print(" REAL GEMINI EMBEDDING TEST PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_small_gemini_test()
