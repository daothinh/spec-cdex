from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


class SecurityPipelineContractTests(unittest.TestCase):
    def test_bootstrap_pipeline_requires_scope_and_severity_handoff(self) -> None:
        text = read(".codex/agents/security-bootstrap-pipeline.toml")
        self.assertIn("prep/severity-conditions.md", text)
        self.assertIn("scope summary with decisive in-scope and out-of-scope reminders", text)
        self.assertIn("Do not recommend a \"next best attack\" in bootstrap", text)
        self.assertIn("severity conditions for `medium`, `high`, and `critical`", text)
        self.assertNotIn("next best attack path for `security-hunting-pipeline`", text)

    def test_hunting_pipeline_requires_real_observed_effect(self) -> None:
        text = read(".codex/agents/security-hunting-pipeline.toml")
        self.assertIn("attacker-observable consequence", text)
        self.assertIn("dangerous function call", text)
        self.assertIn("value-realization", text)
        self.assertIn("negative control", text)
        self.assertIn("prep/domain-logic.md", text)
        self.assertIn("scope/target.json", text)
        self.assertIn("prep/severity-conditions.md", text)
        self.assertIn("scope-check.md", text)
        self.assertIn("end-to-end state impact", text)
        self.assertIn("auth-status", text)
        self.assertIn("create-automate-session", text)
        self.assertIn("export-evidence", text)
        self.assertIn("continue-hunting", text)
        self.assertIn("Only `TRUE POSITIVE` findings with final severity `medium`, `high`, or `critical` satisfy the completion bar", text)
        self.assertIn("Do not stop while all confirmed findings are below `medium`", text)

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
        self.assertIn("security-preverify-trigger", text)
        self.assertIn("preverify-gate.json", text)
        self.assertIn("standalone PoC code file", text)
        self.assertIn("decisive output logs", text)
        self.assertIn("validate_submission_bundle.py", text)
        self.assertIn("external_proof", text)
        self.assertIn("required proof reference", text)
        self.assertIn("secret gist link is mandatory", text)
        self.assertIn("primary report body includes that gist URL inline", text)
        self.assertIn("opening summary or intro includes that gist URL", text)
        self.assertIn("next non-empty line below the gist URL", text)

    def test_preverify_trigger_exists_and_blocks_ai_slop(self) -> None:
        text = read(".codex/agents/security-preverify-trigger.toml")
        self.assertIn("AI slop", text)
        self.assertIn("preverify.md", text)
        self.assertIn("preverify-gate.json", text)
        self.assertIn("standalone PoC", text)
        self.assertIn("/test", text)

    def test_caido_skill_is_ported_into_web_pipeline(self) -> None:
        skill = read("plugins/caido/skills/caido-mode/SKILL.md")
        web = read("plugins/bounty-hunting-programs/skills/bounty-program-web/SKILL.md")
        bootstrap = read(".codex/agents/security-bootstrap-pipeline.toml")
        for command in [
            "create-scope",
            "create-filter",
            "create-env",
            "create-session",
            "create-automate-session",
            "intercept-status",
            "export-evidence",
            "sync-finding",
        ]:
            self.assertIn(command, skill)
        self.assertIn("prep/caido-plan.md", web)
        self.assertIn("export-evidence --out <finding>/artifacts/caido", web)
        self.assertIn("target scope, HTTPQL filter, and environment-variable setup", bootstrap)

    def test_report_rules_do_not_allow_initiation_to_be_reported_as_impact(self) -> None:
        text = read(
            "plugins/bug-bounty-report-submitter/skills/bug-bounty-report-submitter/references/report-writing-rules.md"
        )
        self.assertIn("dangerous function call", text)
        self.assertIn("initiated HTLC", text)
        self.assertIn("claimability", text)
        self.assertIn("settlement", text)
        self.assertIn("preverify-gate.json", text)
        self.assertIn("standalone PoC", text)
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
        self.assertIn("Automatic Preverify Gate", text)
        self.assertIn("Recorded Replay", text)
        self.assertIn("why that asset or workflow is in scope", text)
        self.assertIn("The hunting pipeline should not conclude \"done\" while every confirmed issue is still below `medium`", text)

    def test_step_by_step_contract_matches_scope_and_medium_plus_rules(self) -> None:
        text = read("step-by-step.txt")
        self.assertIn("Prompt 1: Bootstrap Outcome", text)
        self.assertNotIn("Prompt 1: Bootstrap Outcome + Next Best Attack", text)
        self.assertIn("severity conditions for `medium`, `high`, and `critical`", text)
        self.assertIn("`continue-hunting`", text)
        self.assertIn("Compare every candidate against scope before confirming it or assigning severity", text)
        self.assertNotIn("give the next best attack path", text)


if __name__ == "__main__":
    unittest.main()
