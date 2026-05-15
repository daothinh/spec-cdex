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
        self.assertIn("record_asciinema_replay.py", text)
        self.assertIn("Prefer native PATH", text)
        self.assertIn("WSL is fallback only", text)

    def test_submission_pipeline_requires_honest_effect(self) -> None:
        text = read(".codex/agents/security-report-submission-pipeline.toml")
        self.assertIn("internal side effect", text)
        self.assertIn("recipient-controlled settlement", text)
        self.assertIn("queued payment", text)
        self.assertIn("manual-review.md", text)
        self.assertIn("20-minute checkpoint", text)
        self.assertIn("validate_submission_bundle.py", text)
        self.assertIn("external_proof", text)
        self.assertIn("required proof reference", text)
        self.assertIn("secret gist link is mandatory", text)
        self.assertIn("primary report body includes that gist URL inline", text)
        self.assertIn("opening summary or intro includes that gist URL", text)
        self.assertIn("next non-empty line below the gist URL", text)

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
        self.assertIn("Format both URLs as markdown links", text)

    def test_report_structure_requires_external_proof_contract(self) -> None:
        text = read(
            "plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/references/report-structure.md"
        )
        self.assertIn("external_proof", text)
        self.assertIn("target_field", text)
        self.assertIn("gist URL inline", text)
        self.assertIn("required` is always `true", text)
        self.assertIn("opening summary or intro paragraph must carry that gist URL", text)
        self.assertIn("asciinema", text)

    def test_verification_contract_doc_exists(self) -> None:
        text = read("docs/security-finding-verification-contract.md")
        self.assertIn("internal side effect", text)
        self.assertIn("dangerous function call", text)
        self.assertIn("value realization", text)
        self.assertIn("report-ready", text)
        self.assertIn("Domain Logic", text)
        self.assertIn("Manual 20-Minute Gate", text)
        self.assertIn("Recorded Replay", text)


if __name__ == "__main__":
    unittest.main()
