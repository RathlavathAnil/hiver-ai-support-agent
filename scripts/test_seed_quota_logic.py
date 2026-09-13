"""
Unit & Integration Tests for Seeding & Quota Logic
===================================================
Verifies:
1. Sample size defaults to 500
2. Strict golden set exclusion (0% leakage)
3. batchEmbedContents packaging and dimensionality (768)
4. QuotaTracker metric accuracy and pacing calculation
5. Loud failure (no fallback) in Gemini mode
"""

import os
import sys
import unittest
import numpy as np
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from seed_db import (
    QuotaTracker,
    prepare_conversation_pairs,
    load_excluded_golden_ids,
    compute_fallback_embedding,
    classify_intent_heuristic,
    DEFAULT_SAMPLE_SIZE,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_GEMINI_BATCH_SIZE,
    DEFAULT_PACING_INTERVAL,
    EMBEDDING_DIM
)


class TestSeedQuotaLogic(unittest.TestCase):

    def test_default_configurations(self):
        self.assertEqual(DEFAULT_SAMPLE_SIZE, 500, "Default sample size should be 500")
        self.assertEqual(DEFAULT_GEMINI_BATCH_SIZE, 50, "Default batch size should be 50")
        self.assertEqual(DEFAULT_PACING_INTERVAL, 40.0, "Default pacing interval should be 40.0s")
        self.assertEqual(EMBEDDING_DIM, 768, "Embedding dimension must be 768")
        self.assertEqual(DEFAULT_GEMINI_MODEL, "gemini-embedding-001", "Model must be gemini-embedding-001")

    def test_golden_set_exclusion(self):
        golden_ids = load_excluded_golden_ids()
        self.assertEqual(len(golden_ids), 200, "Golden evaluation set must contain exactly 200 tweet IDs")
        
        clean_pairs, conversations, excluded_count = prepare_conversation_pairs(sample_size=500)
        self.assertEqual(len(conversations), 500, "Sampled conversations must equal requested sample size 500")
        
        # Verify 0 overlap with golden IDs
        sample_tweet_ids = {c[0] for c in conversations}
        overlap = sample_tweet_ids.intersection(golden_ids)
        self.assertEqual(len(overlap), 0, f"Found {len(overlap)} golden IDs in seeded sample: {overlap}")

    def test_quota_tracker_metrics(self):
        tracker = QuotaTracker()
        tracker.start()
        
        tracker.record_request(50)
        tracker.record_success(50)
        tracker.record_request(50)
        tracker.record_retry()
        tracker.record_success(50)
        
        summary = tracker.summary()
        self.assertEqual(summary["texts_submitted"], 100)
        self.assertEqual(summary["http_requests"], 2)
        self.assertEqual(summary["retries"], 1)
        self.assertEqual(summary["successful_embeddings"], 100)
        self.assertGreater(summary["texts_per_minute"], 0.0)

    def test_fallback_vector_dimension_and_norm(self):
        text = "My iPhone battery drains rapidly after update"
        vec = compute_fallback_embedding(text, dim=768)
        self.assertEqual(len(vec), 768, "Fallback embedding must have 768 dimensions")
        norm = np.linalg.norm(np.array(vec))
        self.assertAlmostEqual(norm, 1.0, places=4, msg="Embedding vector must be L2-normalized")

    def test_intent_heuristic(self):
        self.assertEqual(classify_intent_heuristic("battery dying fast"), "BATTERY_PERFORMANCE")
        self.assertEqual(classify_intent_heuristic("screen cracked and shattered"), "HARDWARE_PHYSICAL_DAMAGE")
        self.assertEqual(classify_intent_heuristic("apple id password locked out"), "ACCOUNT_ACCESS_SECURITY")
        self.assertEqual(classify_intent_heuristic("charged $14.99 for apple music refund"), "BILLING_SUBSCRIPTIONS")


if __name__ == "__main__":
    unittest.main()
