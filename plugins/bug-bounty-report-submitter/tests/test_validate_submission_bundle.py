from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "bug-bounty-report-submitter"
    / "scripts"
    / "validate_submission_bundle.py"
)


class ValidateSubmissionBundleTests(unittest.TestCase):
    def test_blocks_missing_external_proof_mapping_for_form_submission(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = build_bundle(Path(temp_dir) / "bundle")
            (bundle_dir / "submission.json").write_text(json.dumps({"title": "Finding"}) + "\n", encoding="utf-8")
            (bundle_dir / "external-evidence.json").write_text(
                json.dumps(external_evidence_fixture())
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "report.md").write_text(
                primary_report_text(),
                encoding="utf-8",
            )

            result = run_validator(bundle_dir, "form")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing external_proof contract", result.stderr)

    def test_blocks_empty_url_when_payload_claims_required_external_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = build_bundle(Path(temp_dir) / "bundle")
            (bundle_dir / "submission.json").write_text(
                json.dumps(
                    {
                        "title": "Finding",
                        "details": "Replay links:\nPoC and logs: [https://gist.github.com/example/proof](https://gist.github.com/example/proof)\nPoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)",
                        "external_proof": {
                            "required": True,
                            "type": "secret-gist",
                            "url": "",
                            "source": "external-evidence.json",
                            "target_field": "Reference URL",
                            "inline_note_required": True,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "external-evidence.json").write_text(
                json.dumps(external_evidence_fixture())
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "report.md").write_text(
                primary_report_text(),
                encoding="utf-8",
            )

            result = run_validator(bundle_dir, "form")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("payload external_proof.url is required", result.stderr)

    def test_passes_when_email_payload_carries_required_external_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = build_bundle(Path(temp_dir) / "bundle")
            (bundle_dir / "mail-envelope.json").write_text(
                json.dumps(
                    {
                        "to": ["security@example.com"],
                        "subject": "Target issue",
                        "body": "Details, proof links, and replay:\nPoC and logs: [https://gist.github.com/example/proof](https://gist.github.com/example/proof)\nPoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)",
                        "external_proof": {
                            "required": True,
                            "type": "secret-gist",
                            "url": "https://gist.github.com/example/proof",
                            "source": "external-evidence.json",
                            "target_field": "Body inline note",
                            "inline_note_required": True,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "external-evidence.json").write_text(
                json.dumps(external_evidence_fixture())
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "email-draft.md").write_text(
                primary_report_text(),
                encoding="utf-8",
            )

            result = run_validator(bundle_dir, "email")

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])

    def test_blocks_when_primary_report_omits_gist_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = build_bundle(Path(temp_dir) / "bundle")
            (bundle_dir / "submission.json").write_text(
                json.dumps(
                    {
                        "title": "Finding",
                        "details": "Replay links:\nPoC and logs: [https://gist.github.com/example/proof](https://gist.github.com/example/proof)\nPoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)",
                        "external_proof": {
                            "required": True,
                            "type": "secret-gist",
                            "url": "https://gist.github.com/example/proof",
                            "source": "external-evidence.json",
                            "target_field": "Reference URL",
                            "inline_note_required": True,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "external-evidence.json").write_text(
                json.dumps(external_evidence_fixture())
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "report.md").write_text("Primary report without the required link.\n", encoding="utf-8")

            result = run_validator(bundle_dir, "form")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("primary report draft must include the gist URL", result.stderr)

    def test_blocks_when_opening_summary_omits_gist_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = build_bundle(Path(temp_dir) / "bundle")
            (bundle_dir / "submission.json").write_text(
                json.dumps(
                    {
                        "title": "Finding",
                        "details": "Replay links:\nPoC and logs: [https://gist.github.com/example/proof](https://gist.github.com/example/proof)\nPoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)",
                        "external_proof": {
                            "required": True,
                            "type": "secret-gist",
                            "url": "https://gist.github.com/example/proof",
                            "source": "external-evidence.json",
                            "target_field": "Reference URL",
                            "inline_note_required": True,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "external-evidence.json").write_text(
                json.dumps(external_evidence_fixture())
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "report.md").write_text(
                "# Heading\n\nOpening summary without link.\n\nEvidence later:\nPoC and logs: [https://gist.github.com/example/proof](https://gist.github.com/example/proof)\nPoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)\n",
                encoding="utf-8",
            )

            result = run_validator(bundle_dir, "form")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("opening summary/intro must include the gist URL", result.stderr)

    def test_blocks_when_gist_url_only_exists_in_external_proof_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = build_bundle(Path(temp_dir) / "bundle")
            (bundle_dir / "submission.json").write_text(
                json.dumps(
                    {
                        "title": "Finding",
                        "details": "No link in visible report field.",
                        "external_proof": {
                            "required": True,
                            "type": "secret-gist",
                            "url": "https://gist.github.com/example/proof",
                            "source": "external-evidence.json",
                            "target_field": "Reference URL",
                            "inline_note_required": True,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "external-evidence.json").write_text(
                json.dumps(external_evidence_fixture())
                + "\n",
                encoding="utf-8",
            )

            result = run_validator(bundle_dir, "form")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("submission payload must include the gist URL in a report field", result.stderr)

    def test_blocks_when_external_proof_source_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = build_bundle(Path(temp_dir) / "bundle")
            (bundle_dir / "submission.json").write_text(
                json.dumps(
                    {
                        "title": "Finding",
                        "details": "Replay links:\nPoC and logs: [https://gist.github.com/example/proof](https://gist.github.com/example/proof)\nPoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)",
                        "external_proof": {
                            "required": True,
                            "type": "secret-gist",
                            "url": "https://gist.github.com/example/proof",
                            "target_field": "Reference URL",
                            "inline_note_required": True,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "external-evidence.json").write_text(
                json.dumps(external_evidence_fixture())
                + "\n",
                encoding="utf-8",
            )

            result = run_validator(bundle_dir, "form")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("payload external_proof.source must be external-evidence.json", result.stderr)

    def test_blocks_when_gist_url_is_not_github_gist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = build_bundle(Path(temp_dir) / "bundle")
            (bundle_dir / "submission.json").write_text(
                json.dumps(
                    {
                        "title": "Finding",
                        "details": "Replay links:\nPoC and logs: [https://example.com/proof](https://example.com/proof)\nPoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)",
                        "external_proof": {
                            "required": True,
                            "type": "secret-gist",
                            "url": "https://example.com/proof",
                            "source": "external-evidence.json",
                            "target_field": "Reference URL",
                            "inline_note_required": True,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "report.md").write_text(
                "Opening summary with replay links.\nPoC and logs: [https://example.com/proof](https://example.com/proof)\nPoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)\n",
                encoding="utf-8",
            )
            (bundle_dir / "external-evidence.json").write_text(
                json.dumps(external_evidence_fixture(gist_url="https://example.com/proof"))
                + "\n",
                encoding="utf-8",
            )

            result = run_validator(bundle_dir, "form")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("gist.github.com URL", result.stderr)

    def test_blocks_when_output_log_is_absent_even_if_cast_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = build_bundle(Path(temp_dir) / "bundle")
            (bundle_dir / "report.md").write_text(
                "\n".join(
                    [
                        "Opening summary with replay links.",
                        "PoC and logs: [https://gist.github.com/example/proof](https://gist.github.com/example/proof)",
                        "PoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "evidence" / "logs" / "run.log").unlink()
            (bundle_dir / "evidence" / "poc-replay.cast").write_text(
                "\n".join(
                    [
                        '{"version": 2}',
                        '[sign-code] author: dxoth1nh',
                        '[PASS] replay completed',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "submission.json").write_text(
                json.dumps(
                    {
                        "title": "Finding",
                        "details": "Replay links:\nPoC and logs: [https://gist.github.com/example/proof](https://gist.github.com/example/proof)\nPoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)",
                        "external_proof": {
                            "required": True,
                            "type": "secret-gist",
                            "url": "https://gist.github.com/example/proof",
                            "source": "external-evidence.json",
                            "target_field": "Reference URL",
                            "inline_note_required": True,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "external-evidence.json").write_text(
                json.dumps(external_evidence_fixture())
                + "\n",
                encoding="utf-8",
            )

            result = run_validator(bundle_dir, "form")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing decisive output log file in evidence/", result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])

    def test_blocks_when_asciinema_url_is_not_below_gist_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = build_bundle(Path(temp_dir) / "bundle")
            (bundle_dir / "submission.json").write_text(
                json.dumps(
                    {
                        "title": "Finding",
                        "details": "Replay links:\nPoC and logs: [https://gist.github.com/example/proof](https://gist.github.com/example/proof)\nPoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)",
                        "external_proof": {
                            "required": True,
                            "type": "secret-gist",
                            "url": "https://gist.github.com/example/proof",
                            "source": "external-evidence.json",
                            "target_field": "Reference URL",
                            "inline_note_required": True,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "external-evidence.json").write_text(
                json.dumps(external_evidence_fixture())
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "report.md").write_text(
                "Opening summary with replay links.\nPoC and logs: [https://gist.github.com/example/proof](https://gist.github.com/example/proof)\nReplay video follows after this note.\nPoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)\n",
                encoding="utf-8",
            )

            result = run_validator(bundle_dir, "form")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("next non-empty line below the gist URL", result.stderr)


def build_bundle(bundle_dir: Path) -> Path:
    evidence_dir = bundle_dir / "evidence"
    evidence_dir.mkdir(parents=True)
    asciinema_dir = evidence_dir / "asciinema"
    asciinema_dir.mkdir()
    poc_dir = evidence_dir / "poc"
    poc_dir.mkdir()
    logs_dir = evidence_dir / "logs"
    logs_dir.mkdir()
    (bundle_dir / "artifacts.json").write_text(json.dumps({"artifacts": []}) + "\n", encoding="utf-8")
    (bundle_dir / "preverify.md").write_text("Automatic preverify passed.\n", encoding="utf-8")
    (bundle_dir / "preverify-gate.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "independent_verdict": "TRUE POSITIVE",
                "ai_slop_detected": False,
                "standalone_poc": {
                    "required": True,
                    "path": "artifacts/poc/exploit.py",
                    "test_harness_dependency": False,
                },
                "output_logs": {
                    "required": True,
                    "path": "artifacts/logs/run.log",
                    "success_signal": "[PASS] replay completed",
                },
                "blockers": [],
                "next_stage": "draft-report",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "reverify.md").write_text("TRUE POSITIVE\n", encoding="utf-8")
    (bundle_dir / "severity.md").write_text("High\n", encoding="utf-8")
    (bundle_dir / "report.md").write_text(
        primary_report_text(),
        encoding="utf-8",
    )
    (bundle_dir / "email-draft.md").write_text(
        primary_report_text(),
        encoding="utf-8",
    )
    (bundle_dir / "poc.md").write_text(
        "\n".join(
            [
                "## Proof of Concept",
                "",
                "```bash",
                "python evidence/poc/exploit.py",
                "```",
                "",
                "1. Run the replay command.",
                "2. Observe the returned secret.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (poc_dir / "exploit.py").write_text("print('exploit')\n", encoding="utf-8")
    (logs_dir / "run.log").write_text("[PASS] replay completed\n", encoding="utf-8")
    (asciinema_dir / "reverify-session.cast").write_text("{}\n", encoding="utf-8")
    (asciinema_dir / "asciinema-session.json").write_text(
        json.dumps(
            {
                "tool": "asciinema",
                "local_cast_path": "reverify-session.cast",
                "server_url": "https://asciinema.org/a/demo123",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return bundle_dir


def run_validator(bundle_dir: Path, channel: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--bundle-dir", str(bundle_dir), "--channel", channel],
        check=False,
        capture_output=True,
        text=True,
    )


def primary_report_text() -> str:
    return (
        "\n".join(
            [
                "Opening summary with replay links.",
                "PoC and logs: [https://gist.github.com/example/proof](https://gist.github.com/example/proof)",
                "PoC runtime: [https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)",
                "",
                "## Output from POC",
                "",
                "```text",
                "[PASS] replay completed",
                "```",
            ]
        )
        + "\n"
    )


def external_evidence_fixture(*, gist_url: str = "https://gist.github.com/example/proof") -> dict[str, object]:
    return {
        "type": "secret-gist",
        "submission_requirement": "include-secret-gist-reference",
        "recording_requirement": "include-asciinema-reference",
        "requires_url_field": True,
        "gist": {"published": True, "url": gist_url, "visibility": "secret"},
        "asciinema": {
            "required": True,
            "metadata_path": "evidence/asciinema/asciinema-session.json",
            "local_cast_path": "evidence/asciinema/reverify-session.cast",
            "server_url": "https://asciinema.org/a/demo123",
            "link_markdown": "[https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)",
        },
    }


if __name__ == "__main__":
    unittest.main()
