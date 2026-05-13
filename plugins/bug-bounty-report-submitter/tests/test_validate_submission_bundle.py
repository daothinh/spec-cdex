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
                json.dumps(
                    {
                        "type": "secret-gist",
                        "submission_requirement": "include-secret-gist-reference",
                        "requires_url_field": True,
                        "gist": {"published": True, "url": "https://gist.github.com/example/proof", "visibility": "secret"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "report.md").write_text(
                "Primary report with gist https://gist.github.com/example/proof\n",
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
                        "details": "See gist https://gist.github.com/example/proof",
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
                json.dumps(
                    {
                        "type": "secret-gist",
                        "submission_requirement": "include-secret-gist-reference",
                        "requires_url_field": True,
                        "gist": {"published": True, "url": "https://gist.github.com/example/proof", "visibility": "secret"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "report.md").write_text(
                "Primary report with gist https://gist.github.com/example/proof\n",
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
                        "body": "Details and gist https://gist.github.com/example/proof",
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
                json.dumps(
                    {
                        "type": "secret-gist",
                        "submission_requirement": "include-secret-gist-reference",
                        "requires_url_field": True,
                        "gist": {"published": True, "url": "https://gist.github.com/example/proof", "visibility": "secret"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "email-draft.md").write_text(
                "Email draft with gist https://gist.github.com/example/proof\n",
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
                        "details": "See gist https://gist.github.com/example/proof",
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
                json.dumps(
                    {
                        "type": "secret-gist",
                        "submission_requirement": "include-secret-gist-reference",
                        "requires_url_field": True,
                        "gist": {"published": True, "url": "https://gist.github.com/example/proof", "visibility": "secret"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "report.md").write_text("Primary report without the required link.\n", encoding="utf-8")

            result = run_validator(bundle_dir, "form")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("primary report draft must include the gist URL", result.stderr)

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
                json.dumps(
                    {
                        "type": "secret-gist",
                        "submission_requirement": "include-secret-gist-reference",
                        "requires_url_field": True,
                        "gist": {"published": True, "url": "https://gist.github.com/example/proof", "visibility": "secret"},
                    }
                )
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
                        "details": "Gist: https://gist.github.com/example/proof",
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
                json.dumps(
                    {
                        "type": "secret-gist",
                        "submission_requirement": "include-secret-gist-reference",
                        "requires_url_field": True,
                        "gist": {"published": True, "url": "https://gist.github.com/example/proof", "visibility": "secret"},
                    }
                )
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
                        "details": "Proof: https://example.com/proof",
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
            (bundle_dir / "report.md").write_text("Primary report with gist https://example.com/proof\n", encoding="utf-8")
            (bundle_dir / "external-evidence.json").write_text(
                json.dumps(
                    {
                        "type": "secret-gist",
                        "submission_requirement": "include-secret-gist-reference",
                        "requires_url_field": True,
                        "gist": {"published": True, "url": "https://example.com/proof", "visibility": "secret"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = run_validator(bundle_dir, "form")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("gist.github.com URL", result.stderr)


def build_bundle(bundle_dir: Path) -> Path:
    evidence_dir = bundle_dir / "evidence"
    evidence_dir.mkdir(parents=True)
    (bundle_dir / "artifacts.json").write_text(json.dumps({"artifacts": []}) + "\n", encoding="utf-8")
    (bundle_dir / "manual-review.md").write_text("Manual review passed.\n", encoding="utf-8")
    (bundle_dir / "reverify.md").write_text("TRUE POSITIVE\n", encoding="utf-8")
    (bundle_dir / "severity.md").write_text("High\n", encoding="utf-8")
    (bundle_dir / "report.md").write_text(
        "\n".join(
            [
                "Gist: https://gist.github.com/example/proof",
                "",
                "## Output from POC",
                "",
                "```text",
                "[PASS] replay completed",
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "email-draft.md").write_text(
        "Email draft with gist https://gist.github.com/example/proof\n",
        encoding="utf-8",
    )
    (bundle_dir / "poc.md").write_text(
        "\n".join(
            [
                "## Proof of Concept",
                "",
                "```bash",
                "python exploit.py",
                "```",
                "",
                "1. Run the replay command.",
                "2. Observe the returned secret.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "run.log").write_text("[PASS] replay completed\n", encoding="utf-8")
    return bundle_dir


def run_validator(bundle_dir: Path, channel: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--bundle-dir", str(bundle_dir), "--channel", channel],
        check=False,
        capture_output=True,
        text=True,
    )


if __name__ == "__main__":
    unittest.main()
