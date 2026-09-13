"""
Unit Tests for LLM-as-a-Judge and Human Agreement Modules
=========================================================
Tests:
1. JSON parsing and markdown extraction
2. Invalid judge response handling (missing dimensions, out-of-bounds scores)
3. Missing API key handling (clean skip)
4. Rubric score validation and overall score computation
5. Deterministic sampling (N=20, Seed=42)
6. Human vs LLM statistical agreement calculations (Exact %, MAD, Pearson, Spearman, Kappa)
7. Regression test: Blank human_notes / rating columns dtype safety without pandas float64 errors
"""

import os
import sys
import tempfile
import unittest
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from evaluation.src.metrics.llm_judge import (
    LLMJudge,
    parse_and_validate_judge_response,
    RUBRIC_PROMPT_TEMPLATE
)
from evaluation.src.agreement import (
    compute_agreement,
    compute_agreement_for_dimension,
    compute_comprehensive_judge_agreement,
    interpret_kappa
)
from evaluation.rate_human_judge import initialize_unrated_dataset


class TestLLMJudgeAndAgreement(unittest.TestCase):

    def test_json_parsing_clean(self):
        raw_json = '{"relevance": 5, "groundedness": 4, "helpfulness": 5, "safety": 5, "overall_score": 4.75, "reasoning": "Excellent response."}'
        parsed = parse_and_validate_judge_response(raw_json)
        self.assertEqual(parsed["relevance"], 5)
        self.assertEqual(parsed["groundedness"], 4)
        self.assertEqual(parsed["helpfulness"], 5)
        self.assertEqual(parsed["safety"], 5)
        self.assertEqual(parsed["overall_score"], 4.75)
        self.assertEqual(parsed["reasoning"], "Excellent response.")

    def test_json_parsing_markdown_codeblock(self):
        raw = """```json
{
  "relevance": 4,
  "groundedness": 4,
  "helpfulness": 3,
  "safety": 5,
  "overall_score": 4.0,
  "reasoning": "Helpful settings navigation provided."
}
```"""
        parsed = parse_and_validate_judge_response(raw)
        self.assertEqual(parsed["relevance"], 4)
        self.assertEqual(parsed["groundedness"], 4)
        self.assertEqual(parsed["helpfulness"], 3)
        self.assertEqual(parsed["safety"], 5)
        self.assertEqual(parsed["overall_score"], 4.0)

    def test_json_parsing_with_surrounding_text(self):
        raw = """Here is the quality audit evaluation:
{
  "relevance": 5,
  "groundedness": 5,
  "helpfulness": 4,
  "safety": 5,
  "reasoning": "Clear diagnostic steps."
}
Hope this helps!"""
        parsed = parse_and_validate_judge_response(raw)
        self.assertEqual(parsed["relevance"], 5)
        self.assertEqual(parsed["overall_score"], 4.75)  # Computed automatically

    def test_invalid_judge_response_missing_dim(self):
        raw = '{"relevance": 5, "helpfulness": 4, "safety": 5, "reasoning": "Missing groundedness"}'
        with self.assertRaises(ValueError) as ctx:
            parse_and_validate_judge_response(raw)
        self.assertIn("groundedness", str(ctx.exception))

    def test_invalid_judge_response_out_of_bounds(self):
        raw = '{"relevance": 6, "groundedness": 4, "helpfulness": 5, "safety": 5, "reasoning": "Score 6 is invalid"}'
        with self.assertRaises(ValueError) as ctx:
            parse_and_validate_judge_response(raw)
        self.assertIn("out of bounds", str(ctx.exception))

    def test_missing_api_key_graceful_handling(self):
        judge = LLMJudge(api_key="")
        res = judge.evaluate_one("My battery is dead", "BATTERY_PERFORMANCE", "DM us", "Check settings")
        self.assertEqual(res["status"], "SKIPPED")
        self.assertIn("GEMINI_API_KEY", res["error"])

    def test_deterministic_sampling(self):
        golden_path = ROOT_DIR / "data" / "golden" / "golden_set.csv"
        self.assertTrue(golden_path.exists(), "Golden set must exist")
        df = pd.read_csv(golden_path)
        sample1 = df.sample(n=20, random_state=42)
        sample2 = df.sample(n=20, random_state=42)
        self.assertEqual(list(sample1["id"]), list(sample2["id"]), "Sampling with seed 42 must be 100% deterministic")
        self.assertEqual(len(sample1), 20)

    def test_agreement_perfect_match(self):
        human = [5, 4, 3, 5, 4, 5, 4, 3, 5, 4]
        llm = [5, 4, 3, 5, 4, 5, 4, 3, 5, 4]
        metrics = compute_agreement_for_dimension(human, llm)
        self.assertEqual(metrics["exact_agreement_rate"], 1.0)
        self.assertEqual(metrics["mean_absolute_difference"], 0.0)
        self.assertEqual(metrics["pearson_correlation"], 1.0)
        self.assertEqual(metrics["quadratic_weighted_kappa"], 1.0)

    def test_agreement_partial_divergence(self):
        human = [5, 4, 3, 5, 4, 5, 4, 3, 5, 4]
        llm =   [4, 4, 3, 5, 3, 5, 4, 4, 5, 4]  # Minor 1-point shifts
        metrics = compute_agreement_for_dimension(human, llm)
        self.assertEqual(metrics["within_1_point_rate"], 1.0)
        self.assertLess(metrics["mean_absolute_difference"], 0.5)
        self.assertGreater(metrics["quadratic_weighted_kappa"], 0.6)

    def test_comprehensive_judge_agreement(self):
        human_records = [
            {"id": 1, "relevance": 5, "groundedness": 5, "helpfulness": 4, "safety": 5, "overall_score": 4.75},
            {"id": 2, "relevance": 4, "groundedness": 4, "helpfulness": 3, "safety": 5, "overall_score": 4.00}
        ]
        llm_records = [
            {"record_id": 1, "relevance": 5, "groundedness": 4, "helpfulness": 4, "safety": 5, "overall_score": 4.50},
            {"record_id": 2, "relevance": 4, "groundedness": 4, "helpfulness": 4, "safety": 5, "overall_score": 4.25}
        ]
        res = compute_comprehensive_judge_agreement(human_records, llm_records)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["sample_size"], 2)
        self.assertIn("relevance", res["dimension_agreements"])
        self.assertEqual(res["dimension_agreements"]["relevance"]["exact_agreement_rate"], 1.0)

    def test_compute_agreement_wrapper(self):
        # 1D scalar test
        human = [5, 4, 3, 5, 4]
        llm = [5, 4, 3, 5, 4]
        res_1d = compute_agreement(human, llm)
        self.assertEqual(res_1d["exact_agreement_rate"], 1.0)
        self.assertEqual(res_1d["mean_absolute_difference"], 0.0)

        # Multi-record test
        human_records = [{"id": 1, "relevance": 5, "safety": 5}]
        llm_records = [{"record_id": 1, "relevance": 5, "safety": 5}]
        res_multi = compute_agreement(human_records, llm_records)
        self.assertEqual(res_multi["status"], "SUCCESS")
        self.assertEqual(res_multi["sample_size"], 1)
        self.assertIn("relevance", res_multi["dimension_agreements"])

    def test_all_scores_valid(self):
        human_records = [
            {"record_id": i, "relevance": 5, "groundedness": 5, "helpfulness": 4, "safety": 5, "overall_score": 4.75}
            for i in range(1, 21)
        ]
        llm_records = [
            {"record_id": i, "relevance": 5, "groundedness": 5, "helpfulness": 4, "safety": 5, "overall_score": 4.75}
            for i in range(1, 21)
        ]
        res = compute_comprehensive_judge_agreement(human_records, llm_records)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["sample_size"], 20)
        self.assertEqual(res["dimension_agreements"]["relevance"]["valid_pairs"], 20)
        self.assertEqual(res["dimension_agreements"]["relevance"]["missing_pairs"], 0)
        self.assertEqual(res["dimension_agreements"]["relevance"]["exact_agreement_rate"], 1.0)

    def test_one_llm_score_missing(self):
        # 20 human records, 20 LLM records where record 20 has NaN / missing scores (rate limited)
        human_records = [
            {"record_id": i, "relevance": 5, "groundedness": 5, "helpfulness": 4, "safety": 5, "overall_score": 4.75}
            for i in range(1, 21)
        ]
        llm_records = [
            {"record_id": i, "relevance": 5, "groundedness": 5, "helpfulness": 4, "safety": 5, "overall_score": 4.75}
            for i in range(1, 20)
        ]
        # Add 20th record with NaN / None
        llm_records.append({
            "record_id": 20, "relevance": float("nan"), "groundedness": None,
            "helpfulness": float("nan"), "safety": None, "overall_score": float("nan")
        })

        res = compute_comprehensive_judge_agreement(human_records, llm_records)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["total_matched_records"], 20)
        self.assertEqual(res["sample_size"], 19)
        self.assertEqual(res["missing_pairs"], 1)
        self.assertEqual(res["dimension_agreements"]["relevance"]["valid_pairs"], 19)
        self.assertEqual(res["dimension_agreements"]["relevance"]["missing_pairs"], 1)
        self.assertEqual(res["dimension_agreements"]["relevance"]["exact_agreement_rate"], 1.0)

    def test_multiple_missing_llm_scores(self):
        human_records = [
            {"record_id": i, "relevance": 4, "groundedness": 5, "helpfulness": 4, "safety": 5, "overall_score": 4.5}
            for i in range(1, 21)
        ]
        llm_records = [
            {"record_id": 1, "relevance": 4, "groundedness": 5, "helpfulness": 4, "safety": 5, "overall_score": 4.5},
            {"record_id": 2, "relevance": None, "groundedness": 5, "helpfulness": 4, "safety": 5, "overall_score": 4.5},
            {"record_id": 3, "relevance": float("nan"), "groundedness": float("nan"), "helpfulness": 4, "safety": 5, "overall_score": None},
        ]
        res = compute_comprehensive_judge_agreement(human_records, llm_records)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["dimension_agreements"]["relevance"]["valid_pairs"], 1)
        self.assertEqual(res["dimension_agreements"]["groundedness"]["valid_pairs"], 2)
        self.assertEqual(res["dimension_agreements"]["helpfulness"]["valid_pairs"], 3)

    def test_no_valid_pairs(self):
        # Empty scores or all NaN
        h = [float("nan"), None, "invalid"]
        l = [5.0, 4.0, 3.0]
        dim_res = compute_agreement_for_dimension(h, l)
        self.assertEqual(dim_res["status"], "INSUFFICIENT_DATA")
        self.assertEqual(dim_res["valid_pairs"], 0)
        self.assertEqual(dim_res["sample_size"], 0)
        self.assertEqual(dim_res["exact_agreement_rate"], 0.0)

        # Comprehensive with no matched records
        res = compute_comprehensive_judge_agreement(
            [{"record_id": 100, "relevance": 5}],
            [{"record_id": 200, "relevance": 5}]
        )
        self.assertEqual(res["status"], "NO_MATCHED_PAIRS")
        self.assertEqual(res["sample_size"], 0)

    def test_record_id_alignment(self):
        # Shuffled IDs: Human records in order [1, 2, 3], LLM records in order [3, 1, 2] with distinct scores
        human_records = [
            {"record_id": 1, "relevance": 1},
            {"record_id": 2, "relevance": 2},
            {"record_id": 3, "relevance": 3}
        ]
        llm_records = [
            {"record_id": "3", "relevance": 3},
            {"record_id": "1", "relevance": 1},
            {"record_id": "2", "relevance": 2}
        ]
        res = compute_comprehensive_judge_agreement(human_records, llm_records, dimensions=["relevance"])
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["dimension_agreements"]["relevance"]["exact_agreement_rate"], 1.0)
        self.assertEqual(res["dimension_agreements"]["relevance"]["mean_absolute_difference"], 0.0)


    def test_human_notes_dtype_regression(self):
        """
        Regression test: When a CSV with blank human_notes and empty rating columns is read by pandas,
        it initially infers float64. Converting rating columns to object dtype must allow writing
        string notes (e.g. 'Directly addresses...') and integer scores without TypeError.
        """
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False) as tmp:
            # Write a CSV with empty/null columns that pandas defaults to float64
            tmp.write("record_id,intent,relevance,groundedness,helpfulness,safety,overall_score,human_notes,rating_status\n")
            tmp.write("96,APP_CRASH_PERFORMANCE,,,,,,,PENDING_REVIEW\n")
            tmp.flush()
            tmp_path = tmp.name

        try:
            # Load CSV (pandas infers empty columns as float64)
            df = pd.read_csv(tmp_path)
            self.assertEqual(df["human_notes"].dtype, "float64", "Empty column should be initially inferred as float64")

            # Apply fix: explicit conversion to object dtype
            for col in ["relevance", "groundedness", "helpfulness", "safety", "overall_score", "human_notes", "rating_status"]:
                df[col] = df[col].astype("object")

            # Write string note and integer ratings
            notes_str = "Directly addresses the customer issue with clear diagnostic steps."
            df.at[0, "relevance"] = 5
            df.at[0, "groundedness"] = 5
            df.at[0, "helpfulness"] = 4
            df.at[0, "safety"] = 5
            df.at[0, "overall_score"] = 4.75
            df.at[0, "human_notes"] = notes_str
            df.at[0, "rating_status"] = "HUMAN_RATING"

            # Verify values in memory
            self.assertEqual(df.at[0, "human_notes"], notes_str)
            self.assertEqual(df.at[0, "relevance"], 5)
            self.assertEqual(df.at[0, "rating_status"], "HUMAN_RATING")

            # Save and reload to ensure clean serialization
            df.to_csv(tmp_path, index=False)
            reloaded_df = pd.read_csv(tmp_path)
            self.assertEqual(reloaded_df.at[0, "human_notes"], notes_str)
            self.assertEqual(reloaded_df.at[0, "rating_status"], "HUMAN_RATING")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_agent_client_predict_one_interface(self):
        """
        Regression test: Verify that AgentClient has predict_one method returning expected dictionary keys
        (predicted_reply, similar_conversations, status).
        """
        from evaluation.src.agent_client import AgentClient
        client = AgentClient(base_url="http://localhost:8080")
        self.assertTrue(hasattr(client, "predict_one"), "AgentClient must expose predict_one method")
        self.assertTrue(hasattr(client, "check_health"), "AgentClient must expose check_health method")
        self.assertTrue(hasattr(client, "evaluate_dataset"), "AgentClient must expose evaluate_dataset method")


if __name__ == "__main__":
    unittest.main()

