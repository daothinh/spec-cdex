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
    / "prepare_external_proof_pack.py"
)


class PrepareExternalProofPackTests(unittest.TestCase):
    def test_builds_gist_backed_proof_pack_and_external_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_dir = root / "bundle"
            evidence_dir = bundle_dir / "evidence"
            evidence_dir.mkdir(parents=True)

            (bundle_dir / "poc.md").write_text(
                "\n".join(
                    [
                        "## Proof of Concept",
                        "",
                        "Command:",
                        "```bash",
                        "forge test --match-path test/poc/RemoveLiquidityReentrancyPoC.t.sol -vv",
                        "```",
                        "",
                        "1. Clone the repository.",
                        "2. Copy the PoC file.",
                        "3. Run the Forge command.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "report-appendix.md").write_text(
                "\n".join(
                    [
                        "## Output from POC",
                        "",
                        "```text",
                        "[PASS] test_removeLiquidityReentersSwapBeforeReservesAndSharesAreUpdated()",
                        "reentrant ETH taken 9999000000000000000000",
                        "```",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "artifacts.json").write_text(
                json.dumps(
                    {
                        "count": 2,
                        "artifacts": [
                            {
                                "id": "ART-001",
                                "relative_bundle_path": "evidence/RemoveLiquidityReentrancyPoC.t.sol",
                                "kind": "script",
                                "description": "Foundry PoC file",
                            },
                            {
                                "id": "ART-002",
                                "relative_bundle_path": "evidence/test-output.log",
                                "kind": "text",
                                "description": "Captured Forge output",
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (evidence_dir / "RemoveLiquidityReentrancyPoC.t.sol").write_text("contract PoC {}\n", encoding="utf-8")
            (evidence_dir / "test-output.log").write_text("[PASS] replay\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--bundle-dir",
                    str(bundle_dir),
                    "--gist-url",
                    "https://gist.github.com/example/proof-pack",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            proof_pack_dir = bundle_dir / "proof-pack"
            self.assertTrue((proof_pack_dir / "poc.md").exists())
            self.assertTrue((proof_pack_dir / "report-appendix.md").exists())
            self.assertTrue((proof_pack_dir / "evidence__RemoveLiquidityReentrancyPoC.t.sol").exists())
            self.assertTrue((proof_pack_dir / "evidence__test-output.log").exists())
            self.assertTrue((proof_pack_dir / "external-proof-pack.md").exists())
            self.assertTrue((proof_pack_dir / "external-proof-pack.json").exists())

            external_evidence = json.loads((bundle_dir / "external-evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(external_evidence["type"], "secret-gist")
            self.assertIn("forge test --match-path", external_evidence["run_commands"][0])
            self.assertIn("[PASS]", external_evidence["success_signals"][0])
            self.assertIn("Reference URL", external_evidence["recommended_field_labels"])
            self.assertTrue(external_evidence["requires_url_field"])
            self.assertEqual(external_evidence["submission_requirement"], "include-secret-gist-reference")
            self.assertIn("exact vulnerable location", external_evidence["suggested_inline_note"])
            self.assertEqual(external_evidence["gist"]["url"], "https://gist.github.com/example/proof-pack")

            manifest = json.loads((proof_pack_dir / "external-proof-pack.json").read_text(encoding="utf-8"))
            filenames = {item["pack_filename"] for item in manifest["files"]}
            self.assertIn("evidence__RemoveLiquidityReentrancyPoC.t.sol", filenames)
            self.assertIn("evidence__test-output.log", filenames)
            self.assertEqual(manifest["gist"]["url"], "https://gist.github.com/example/proof-pack")

    def test_fails_without_gist_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir()
            (bundle_dir / "poc.md").write_text(
                "\n".join(
                    [
                        "## Proof of Concept",
                        "",
                        "```bash",
                        "python exploit.py",
                        "```",
                        "",
                        "1. Run the exploit.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_dir / "report.md").write_text(
                "\n".join(
                    [
                        "## Output from POC",
                        "",
                        "```text",
                        "[PASS] replay worked",
                        "```",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--bundle-dir", str(bundle_dir)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("gist link is required", result.stderr)

    def test_fails_without_replay_details(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir()
            (bundle_dir / "poc.md").write_text("See attached PoC file.\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--bundle-dir",
                    str(bundle_dir),
                    "--gist-url",
                    "https://gist.github.com/example/proof-pack",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no runnable replay material found", result.stderr)


if __name__ == "__main__":
    unittest.main()
