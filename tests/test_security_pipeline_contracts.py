from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


class SecurityPipelineContractTests(unittest.TestCase):
    def test_hunting_pipeline_requires_real_observed_effect(self) -> None:
        text = read(".codex/agents/security-hunting-pipeline.toml")
        self.assertIn("attacker-observable consequence", text)
        self.assertIn("dangerous function call", text)
        self.assertIn("value-realization", text)
        self.assertIn("negative control", text)
        self.assertIn("prep/domain-logic.md", text)
        self.assertIn("end-to-end state impact", text)

    def test_reverify_pipeline_blocks_internal_side_effect_claims(self) -> None:
        text = read(".codex/agents/security-finding-reverify.toml")
        self.assertIn("dangerous function call", text)
        self.assertIn("value realization", text)
        self.assertIn("initiated HTLC", text)
        self.assertIn("gate review", text)
        self.assertIn("Devil's Advocate", text)
        self.assertIn("signature, preimage, ZK proof", text)

    def test_submission_pipeline_requires_honest_effect(self) -> None:
        text = read(".codex/agents/security-report-submission-pipeline.toml")
        self.assertIn("internal side effect", text)
        self.assertIn("recipient-controlled settlement", text)
        self.assertIn("queued payment", text)
        self.assertIn("manual-review.md", text)
        self.assertIn("20-minute checkpoint", text)

    def test_report_rules_do_not_allow_initiation_to_be_reported_as_impact(self) -> None:
        text = read(
            "plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/references/report-writing-rules.md"
        )
        self.assertIn("dangerous function call", text)
        self.assertIn("initiated HTLC", text)
        self.assertIn("claimability", text)
        self.assertIn("settlement", text)
        self.assertIn("manual-review.md", text)
        self.assertIn("signature, proof, or preimage", text)

    def test_verification_contract_doc_exists(self) -> None:
        text = read("docs/security-finding-verification-contract.md")
        self.assertIn("internal side effect", text)
        self.assertIn("dangerous function call", text)
        self.assertIn("value realization", text)
        self.assertIn("report-ready", text)
        self.assertIn("Domain Logic", text)
        self.assertIn("Manual 20-Minute Gate", text)


if __name__ == "__main__":
    unittest.main()
