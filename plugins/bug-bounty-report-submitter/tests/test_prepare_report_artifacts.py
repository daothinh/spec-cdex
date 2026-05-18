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
    / "prepare_report_artifacts.py"
)


class PrepareReportArtifactsTests(unittest.TestCase):
    def test_generates_artifacts_manifest_and_copies_caido_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            finding_dir = root / "finding"
            caido_dir = finding_dir / "artifacts" / "caido"
            caido_dir.mkdir(parents=True)

            (caido_dir / "request-123.json").write_text(
                json.dumps(
                    {
                        "request": {
                            "id": "123",
                            "method": "GET",
                            "host": "api.example.local",
                            "path": "/v1/users/999",
                        },
                        "response": {"statusCode": 200},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (caido_dir / "request-123.curl.txt").write_text("curl -X GET 'https://api.example.local/v1/users/999'\n", encoding="utf-8")
            (caido_dir / "response-123.txt").write_text("HTTP/1.1 200 OK\n\n{}", encoding="utf-8")

            bundle_dir = root / "bundle"
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--finding-dir", str(finding_dir), "--bundle-dir", str(bundle_dir)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            manifest = json.loads((bundle_dir / "artifacts.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["count"], 3)
            self.assertTrue((bundle_dir / "evidence" / "caido" / "request-123.json").exists())
            self.assertTrue((bundle_dir / "evidence" / "caido" / "request-123.curl.txt").exists())
            self.assertTrue((bundle_dir / "evidence" / "caido" / "response-123.txt").exists())

            kinds = {item["kind"] for item in manifest["artifacts"]}
            self.assertIn("caido-request-metadata", kinds)
            self.assertIn("caido-curl", kinds)
            self.assertIn("caido-response", kinds)

            request_entry = next(item for item in manifest["artifacts"] if item["kind"] == "caido-request-metadata")
            self.assertEqual(request_entry["details"]["request_id"], "123")
            self.assertEqual(request_entry["details"]["method"], "GET")
            self.assertEqual(request_entry["details"]["host"], "api.example.local")
            self.assertEqual(request_entry["details"]["path"], "/v1/users/999")

    def test_classifies_asciinema_casts_as_terminal_recordings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            finding_dir = root / "finding"
            terminal_dir = finding_dir / "artifacts" / "terminal"
            terminal_dir.mkdir(parents=True)

            (terminal_dir / "poc-replay.cast").write_text(
                '{"version": 2, "stdout": ["echo \\"[sign-code] author: dxoth1nh\\""]}\n',
                encoding="utf-8",
            )

            bundle_dir = root / "bundle"
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--finding-dir", str(finding_dir), "--bundle-dir", str(bundle_dir)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            manifest = json.loads((bundle_dir / "artifacts.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["count"], 1)
            self.assertTrue((bundle_dir / "evidence" / "terminal" / "poc-replay.cast").exists())

            cast_entry = manifest["artifacts"][0]
            self.assertEqual(cast_entry["kind"], "asciinema-cast")
            self.assertEqual(cast_entry["relative_bundle_path"], "evidence/terminal/poc-replay.cast")


if __name__ == "__main__":
    unittest.main()
