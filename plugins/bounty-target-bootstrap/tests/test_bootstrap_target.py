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
    / "bounty-target-bootstrap"
    / "scripts"
    / "bootstrap_target.py"
)


class BootstrapTargetTests(unittest.TestCase):
    def test_whitebox_bootstrap_clones_repo_and_downloads_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            workspace = temp_root / "workspace"
            workspace.mkdir()

            source_repo = temp_root / "source-repo"
            source_repo.mkdir()
            (source_repo / "package.json").write_text('{"name":"demo-web"}\n', encoding="utf-8")
            subprocess.run(["git", "init"], cwd=source_repo, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "add", "package.json"],
                cwd=source_repo,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.com",
                    "commit",
                    "-m",
                    "init",
                ],
                cwd=source_repo,
                check=True,
                capture_output=True,
                text=True,
            )

            apk_file = temp_root / "fixture.apk"
            apk_file.write_bytes(b"apk")

            input_payload = {
                "program_name": "Acme Whitebox",
                "program_url": "https://program.local/acme",
                "target_type": "whitebox",
                "scope_summary": "Authenticated whitebox repo review.",
                "in_scope": ["Staging API repo", "Internal CI helper repo"],
                "out_of_scope": ["Production customer data"],
                "repo_urls": [str(source_repo)],
                "artifacts": [{"url": apk_file.as_uri(), "kind": "apk"}],
                "rules": ["Stay inside staging."],
                "safe_harbor": ["No social engineering."],
                "submission_guidelines": ["Include commit hash in report."],
                "raw_scope_notes": "Rendered scope copied from Playwright.",
            }
            input_path = temp_root / "input.json"
            input_path.write_text(json.dumps(input_payload), encoding="utf-8")

            result = self.run_script(input_path, workspace)
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            stdout = json.loads(result.stdout)
            self.assertEqual(stdout["suggested_lane"], "bounty-program-web")

            target_root = workspace / "audit-targets" / "acme-whitebox"
            self.assertTrue((target_root / "scope" / "target.json").exists())
            self.assertTrue((target_root / "scope" / "raw-scope-notes.md").exists())
            self.assertTrue((target_root / "scope" / "in-scope.md").exists())
            self.assertTrue((target_root / "scope" / "out-of-scope.md").exists())
            self.assertTrue((target_root / "scope" / "rules.md").exists())
            self.assertTrue((target_root / "scope" / "program-notes.md").exists())
            self.assertTrue((target_root / "source" / "repos" / "source-repo" / "package.json").exists())
            self.assertTrue((target_root / "source" / "artifacts" / "fixture.apk").exists())

            target_json = json.loads((target_root / "scope" / "target.json").read_text(encoding="utf-8"))
            self.assertEqual(target_json["in_scope"], ["Staging API repo", "Internal CI helper repo"])
            self.assertEqual(target_json["out_of_scope"], ["Production customer data"])
            self.assertEqual(target_json["rules"], ["Stay inside staging."])
            self.assertEqual(target_json["safe_harbor"], ["No social engineering."])
            self.assertEqual(target_json["submission_guidelines"], ["Include commit hash in report."])

            self.assertIn("Production customer data", (target_root / "scope" / "out-of-scope.md").read_text(encoding="utf-8"))
            self.assertIn("No social engineering.", (target_root / "scope" / "program-notes.md").read_text(encoding="utf-8"))

    def test_android_bootstrap_prefers_mobile_lane(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            workspace = temp_root / "workspace"
            workspace.mkdir()

            apk_file = temp_root / "android-app.apk"
            apk_file.write_bytes(b"apk")

            input_payload = {
                "program_name": "Acme Android",
                "program_url": "https://program.local/acme-android",
                "target_type": "android",
                "package_names": ["com.acme.app"],
                "artifacts": [apk_file.as_uri()],
            }
            input_path = temp_root / "input.json"
            input_path.write_text(json.dumps(input_payload), encoding="utf-8")

            result = self.run_script(input_path, workspace)
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            stdout = json.loads(result.stdout)
            self.assertEqual(stdout["suggested_lane"], "bounty-program-mobile-android")
            ready_file = workspace / stdout["ready_file"]
            self.assertIn(
                "bounty-program-mobile-android",
                ready_file.read_text(encoding="utf-8"),
            )

    def test_rejects_unsupported_target_type(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            workspace = temp_root / "workspace"
            workspace.mkdir()

            input_payload = {
                "program_name": "Wrong Type",
                "program_url": "https://program.local/wrong",
                "target_type": "web",
            }
            input_path = temp_root / "input.json"
            input_path.write_text(json.dumps(input_payload), encoding="utf-8")

            result = self.run_script(input_path, workspace)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("target_type must be one of", result.stderr)

    def run_script(self, input_path: Path, workspace: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--input", str(input_path), "--repo-root", str(workspace)],
            check=False,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
