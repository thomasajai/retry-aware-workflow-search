"""Offline usability, verdict, fixture provenance, and request-leakage checks."""

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mathqa_verifier as verifier
from mathqa_response import validate_answer
from mathqa_verifier_trials import load_review


class UsabilityTests(unittest.TestCase):
    def test_readable_legacy_format_violations_are_usable(self):
        for calculation in ("Six groups of seven give 6*7=42.", "6*7=42; " + "a long explanation " * 20):
            answer = json.dumps({"calculation": calculation, "option": "b", "value": "42"})
            self.assertFalse(validate_answer(answer, "json-v1", "a) 40, b) 42")["valid"])
            self.assertTrue(verifier.extract_usable(answer, "json-v1")["usable"])

    def test_cosmetic_normalization_is_reported_and_missing_value_does_not_infer_option(self):
        result = verifier.extract_usable('```json\n{"calculation":"6*7=42","option":" B "}\n```', "json-v1")
        self.assertTrue(result["usable"])
        self.assertEqual(result["fields"]["option"], "b")
        self.assertIsNone(result["fields"]["value"])
        self.assertEqual(len(result["diagnostics"]["normalizations"]), 2)
        self.assertFalse(verifier.extract_usable('{"calculation":"6*7=42","value":"42"}', "json-v1")["usable"])

    def test_arithmetic_and_value_conflicts_are_for_verifier_not_local_rejection(self):
        result = verifier.extract_usable('{"calculation":"6*7=40","option":"b","value":"44"}', "json-v1")
        self.assertTrue(result["usable"])
        self.assertEqual(result["fields"]["calculation"], "6*7=40")
        self.assertEqual(result["fields"]["value"], "44")

    def test_ambiguity_missing_calculation_and_truncation_are_unusable(self):
        for answer in (None, "", "[]", '{"calculation":"x","option":"b","option":"a"}',
                       '{"option":"b"}', '{"calculation":"","option":"b"}',
                       '{"calculation":"6*7=42","option":["a","b"]}',
                       '{"calculation":"6*7=42","option":"b"} trailing'):
            with self.subTest(answer=answer):
                self.assertFalse(verifier.extract_usable(answer, "json-v1")["usable"])
        text = '{"calculation":"6*7=42","option":"b"}'
        for status, finish in (("failed", "stop"), ("completed", "length"), ("running", "stop")):
            self.assertFalse(verifier.extract_usable(text, "json-v1", status=status, finish_reason=finish)["usable"])

    def test_line_format_allows_prose_and_multistep_calculation_not_multiple_choices(self):
        result = verifier.extract_usable("six times seven; 6*7=42; B ) 42", "line-v1")
        self.assertTrue(result["usable"])
        for answer in ("6*7=42; a) 40; b) 42", "6*7=42; b) 42 or c) 44", "b) 42"):
            self.assertFalse(verifier.extract_usable(answer, "line-v1")["usable"])


class VerdictAndRequestTests(unittest.TestCase):
    def test_only_actual_booleans_and_unique_single_field_are_decisions(self):
        self.assertEqual(verifier.parse_verdict('{"accepted":true}')["status"], "accept")
        self.assertEqual(verifier.parse_verdict('{"accepted":false}')["status"], "reject")
        for answer in (None, "yes", '{"accepted":0}', '{"accepted":"false"}', '{"accepted":null}',
                       '{"accepted":true,"extra":1}', '{"accepted":true,"accepted":false}',
                       '```json\n{"accepted":true}\n```'):
            with self.subTest(answer=answer):
                result = verifier.parse_verdict(answer)
                self.assertEqual(result["status"], "invalid")
                self.assertIsNone(result["accepted"])
        for status, finish in (("failed", "stop"), ("completed", "length")):
            self.assertEqual(verifier.parse_verdict('{"accepted":false}', status=status, finish_reason=finish)["status"], "error")

    def test_request_allowlist_excludes_reference_labels_history_and_extra_fields(self):
        question = {"problem": "6 times 7?", "options": "a) 40, b) 42", "correct": "LEAK_KEY",
                    "Rationale": "LEAK_RATIONALE", "prior_answer": "LEAK_HISTORY"}
        fields = {"calculation": "6*7=42", "option": "b", "value": "42", "expected_accept": "LEAK_LABEL"}
        for alias in verifier.VERIFIER_PROFILES:
            request = verifier.build_request(alias, question, fields)
            text = json.dumps(request)
            self.assertNotIn("LEAK_", text)
            supplied = json.loads(request["messages"][1]["content"])
            self.assertEqual(set(supplied), {"question", "options", "solver_proposal"})
            self.assertEqual(set(supplied["solver_proposal"]), {"calculation", "option", "value"})

    def test_profiles_are_independent_proposed_snapshots(self):
        request = verifier.profile("deepseek")
        request["settings"]["provider"]["only"].append("another-provider")
        self.assertEqual(verifier.profile("deepseek")["settings"]["provider"]["only"], ["deepinfra/fp4"])
        self.assertIn("proposed", request["readiness"])

    def test_review_cases_have_independent_provenance_and_unknown_labels_stay_unknown(self):
        review = load_review()
        self.assertEqual(len(review["cases"]), 12)
        by_id = {c["id"]: c for c in review["cases"]}
        for case in review["cases"]:
            self.assertIn("not human", case["review"]["reviewer"])
            self.assertIn("no candidate verifier", case["review"]["method"].lower())
        lucky = by_id["lucky_option_bad_arithmetic"]["labels"]
        self.assertTrue(lucky["option_correct"])
        self.assertFalse(lucky["reasoning_valid"])
        self.assertFalse(lucky["expected_accept"])
        self.assertIsNone(by_id["uncertain_rounding"]["labels"]["reasoning_valid"])
        for case in review["cases"]:
            result = verifier.extract_usable(case["answer"], case["contract"], finish_reason=case.get("finish_reason", "stop"))
            if case["kind"].startswith("unusable"):
                self.assertFalse(result["usable"])
            elif case["labels"]["expected_accept"] is True:
                self.assertTrue(result["usable"])


if __name__ == "__main__":
    unittest.main()
