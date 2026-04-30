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
                "focus_areas": ["Exchange", "Blockchain"],
                "scope_summary": "Authenticated whitebox repo review.",
                "in_scope": ["Staging API repo", "Internal CI helper repo"],
                "out_of_scope": ["Production customer data"],
                "repo_urls": [str(source_repo)],
                "artifacts": [{"url": apk_file.as_uri(), "kind": "apk"}],
                "web_urls": ["https://app.acme.local"],
                "api_urls": ["https://api.acme.local"],
                "rpc_urls": ["https://rpc.acme.local"],
                "docs_urls": ["https://docs.acme.local/security"],
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
            self.assertEqual(
                stdout["prioritized_bug_classes"][0],
                "authorization and IDOR boundary failures",
            )

            target_root = workspace / "audit-targets" / "acme-whitebox"
            self.assertTrue((target_root / "scope" / "target.json").exists())
            self.assertTrue((target_root / "scope" / "raw-scope-notes.md").exists())
            self.assertTrue((target_root / "scope" / "in-scope.md").exists())
            self.assertTrue((target_root / "scope" / "out-of-scope.md").exists())
            self.assertTrue((target_root / "scope" / "rules.md").exists())
            self.assertTrue((target_root / "scope" / "program-notes.md").exists())
            self.assertTrue((target_root / "scope" / "target-surface.md").exists())
            self.assertTrue((target_root / "scope" / "smart-contracts.md").exists())
            self.assertTrue((target_root / "scope" / "chain-inventory.json").exists())
            self.assertTrue((target_root / "scope" / "protocol-archetype.md").exists())
            self.assertTrue((target_root / "scope" / "proxy-topology.md").exists())
            self.assertTrue((target_root / "scope" / "dependency-boundaries.md").exists())
            self.assertTrue((target_root / "findings" / "README.md").exists())
            self.assertTrue((target_root / "prep" / "tried-and-ruled-out.md").exists())
            self.assertTrue((target_root / "prep" / "finding-pipeline.md").exists())
            self.assertTrue((target_root / "prep" / "bootstrap-summary.md").exists())
            self.assertTrue((target_root / "prep" / "kage-plan.md").exists())
            self.assertTrue((target_root / "prep" / "caido-plan.md").exists())
            self.assertTrue((target_root / "prep" / "attack-surface-map.md").exists())
            self.assertTrue((target_root / "prep" / "protocol-invariants.md").exists())
            self.assertTrue((target_root / "prep" / "web3-readiness.md").exists())
            self.assertTrue((target_root / "prep" / "context-pack" / "README.md").exists())
            self.assertTrue((target_root / "prep" / "context-pack" / "trust-boundaries.md").exists())
            self.assertTrue((target_root / "prep" / "context-pack" / "lane-decision.md").exists())
            self.assertTrue((target_root / "prep" / "context-pack" / "asset-pointers.md").exists())
            self.assertTrue((target_root / "prep" / "context-pack" / "web-handoff.md").exists())
            self.assertTrue((target_root / "prep" / "context-pack" / "protocol-archetype.md").exists())
            self.assertTrue((target_root / "prep" / "context-pack" / "dependency-boundaries.md").exists())
            self.assertTrue((target_root / "prep" / "context-pack" / "attack-surface-map.md").exists())
            self.assertTrue((target_root / "prep" / "context-pack" / "web3-readiness.md").exists())
            self.assertTrue((target_root / "source" / "repos" / "source-repo" / "package.json").exists())
            self.assertTrue((target_root / "source" / "artifacts" / "fixture.apk").exists())

            target_json = json.loads((target_root / "scope" / "target.json").read_text(encoding="utf-8"))
            self.assertEqual(target_json["focus_areas"], ["Exchange", "Blockchain"])
            self.assertEqual(target_json["in_scope"], ["Staging API repo", "Internal CI helper repo"])
            self.assertEqual(target_json["out_of_scope"], ["Production customer data"])
            self.assertEqual(target_json["rules"], ["Stay inside staging."])
            self.assertEqual(target_json["safe_harbor"], ["No social engineering."])
            self.assertEqual(target_json["submission_guidelines"], ["Include commit hash in report."])
            self.assertEqual(target_json["web_urls"], ["https://app.acme.local"])
            self.assertEqual(target_json["rpc_urls"], ["https://rpc.acme.local"])
            self.assertIn("web", target_json["surface_signals"])
            self.assertIn("exchange", target_json["surface_signals"])
            self.assertEqual(target_json["follow_on_lanes"], ["bounty-program-web"])
            self.assertEqual(target_json["protocol_archetype"]["name"], "Perps / Orderbook / Exchange")
            self.assertTrue(target_json["web3_readiness"]["is_web3_target"])
            self.assertTrue(stdout["kage_plan_file"].endswith("prep/kage-plan.md"))
            self.assertTrue(stdout["caido_plan_file"].endswith("prep/caido-plan.md"))

            self.assertIn("Production customer data", (target_root / "scope" / "out-of-scope.md").read_text(encoding="utf-8"))
            self.assertIn("No social engineering.", (target_root / "scope" / "program-notes.md").read_text(encoding="utf-8"))
            self.assertIn("https://docs.acme.local/security", (target_root / "scope" / "target-surface.md").read_text(encoding="utf-8"))
            self.assertIn("reverify-pending", (target_root / "prep" / "finding-pipeline.md").read_text(encoding="utf-8"))
            self.assertIn("reverify.md", (target_root / "findings" / "README.md").read_text(encoding="utf-8"))
            self.assertIn("facts-chain.md", (target_root / "findings" / "README.md").read_text(encoding="utf-8"))
            self.assertIn("impact-financials.md", (target_root / "findings" / "README.md").read_text(encoding="utf-8"))
            self.assertIn("environment.md", (target_root / "findings" / "README.md").read_text(encoding="utf-8"))
            self.assertIn("severity.md", (target_root / "findings" / "README.md").read_text(encoding="utf-8"))
            self.assertIn("artifacts/caido/", (target_root / "findings" / "README.md").read_text(encoding="utf-8"))
            self.assertIn("Primary Lane", (target_root / "prep" / "bootstrap-summary.md").read_text(encoding="utf-8"))
            self.assertIn("Next Best Attack Path", (target_root / "prep" / "bootstrap-summary.md").read_text(encoding="utf-8"))
            self.assertIn("Protocol Archetype", (target_root / "prep" / "bootstrap-summary.md").read_text(encoding="utf-8"))
            self.assertIn("Caido Plan", (target_root / "prep" / "caido-plan.md").read_text(encoding="utf-8"))
            self.assertIn("Preferred Mode", (target_root / "prep" / "kage-plan.md").read_text(encoding="utf-8"))
            self.assertIn("Use `caido`", (target_root / "prep" / "context-pack" / "web-handoff.md").read_text(encoding="utf-8"))
            self.assertIn("Execution Mode", (target_root / "prep" / "web3-readiness.md").read_text(encoding="utf-8"))

    def test_smart_contract_bootstrap_collects_contract_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            workspace = temp_root / "workspace"
            workspace.mkdir()

            source_repo = temp_root / "protocol-repo"
            source_repo.mkdir()
            (source_repo / "foundry.toml").write_text("[profile.default]\n", encoding="utf-8")
            subprocess.run(["git", "init"], cwd=source_repo, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "add", "foundry.toml"],
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

            abi_file = temp_root / "vault-abi.json"
            abi_file.write_text('{"abi":[]}\n', encoding="utf-8")
            audit_file = temp_root / "protocol-audit.pdf"
            audit_file.write_bytes(b"%PDF-1.4")

            input_payload = {
                "program_name": "Acme Protocol",
                "program_url": "https://program.local/acme-protocol",
                "target_type": "smart-contract",
                "focus_areas": ["Smart Contract", "Exchange"],
                "repo_urls": [str(source_repo)],
                "docs_urls": ["https://docs.acme.local/protocol"],
                "audit_report_urls": [audit_file.as_uri()],
                "smart_contracts": [
                    {
                        "name": "VaultProxy",
                        "kind": "proxy",
                        "chain": "Ethereum",
                        "chain_id": "1",
                        "network": "mainnet",
                        "vm": "EVM",
                        "address": "0x1234",
                        "proxy_address": "0x1234",
                        "implementation_address": "0xabcd",
                        "explorer_url": "https://etherscan.local/address/0x1234",
                        "abi_url": abi_file.as_uri(),
                        "source_url": "https://github.local/acme/protocol/blob/main/src/VaultProxy.sol",
                        "repo_url": str(source_repo),
                        "language": "Solidity",
                        "notes": "Primary production vault proxy.",
                    }
                ],
            }
            input_path = temp_root / "input.json"
            input_path.write_text(json.dumps(input_payload), encoding="utf-8")

            result = self.run_script(input_path, workspace)
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            stdout = json.loads(result.stdout)
            self.assertEqual(stdout["suggested_lane"], "bounty-program-smart-contracts")
            self.assertIn("privileged entry point and access-control failures", stdout["prioritized_bug_classes"])

            target_root = workspace / "audit-targets" / "acme-protocol"
            self.assertTrue((target_root / "scope" / "smart-contracts.md").exists())
            self.assertTrue((target_root / "scope" / "target-surface.md").exists())
            self.assertTrue((target_root / "scope" / "chain-inventory.json").exists())
            self.assertTrue((target_root / "scope" / "protocol-archetype.md").exists())
            self.assertTrue((target_root / "scope" / "proxy-topology.md").exists())
            self.assertTrue((target_root / "scope" / "dependency-boundaries.md").exists())
            self.assertTrue((target_root / "prep" / "bootstrap-summary.md").exists())
            self.assertTrue((target_root / "prep" / "attack-surface-map.md").exists())
            self.assertTrue((target_root / "prep" / "protocol-invariants.md").exists())
            self.assertTrue((target_root / "prep" / "web3-readiness.md").exists())
            self.assertTrue((target_root / "source" / "repos" / "protocol-repo" / "foundry.toml").exists())
            self.assertTrue((target_root / "source" / "artifacts" / "vault-abi.json").exists())
            self.assertTrue((target_root / "source" / "artifacts" / "protocol-audit.pdf").exists())

            target_json = json.loads((target_root / "scope" / "target.json").read_text(encoding="utf-8"))
            self.assertEqual(target_json["focus_areas"], ["Smart Contract", "Exchange"])
            self.assertEqual(target_json["smart_contracts"][0]["address"], "0x1234")
            self.assertEqual(target_json["repo_urls"], [str(source_repo)])
            self.assertIn("smart-contract", target_json["surface_signals"])
            self.assertIn("exchange", target_json["surface_signals"])
            self.assertEqual(target_json["protocol_archetype"]["name"], "Vault / Yield Strategy")
            self.assertIn("VaultProxy", (target_root / "scope" / "smart-contracts.md").read_text(encoding="utf-8"))
            self.assertIn("etherscan.local", (target_root / "scope" / "target-surface.md").read_text(encoding="utf-8"))
            self.assertIn("delegatecall", (target_root / "scope" / "proxy-topology.md").read_text(encoding="utf-8"))
            self.assertIn("privileged entry point", (target_root / "prep" / "bootstrap-summary.md").read_text(encoding="utf-8"))
            readiness_text = (target_root / "prep" / "web3-readiness.md").read_text(encoding="utf-8")
            self.assertIn("Execution Mode", readiness_text)
            self.assertIn("scripts/bootstrap-web3-tools.ps1", readiness_text)

    def test_wallet_mixed_surface_prefers_triage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            workspace = temp_root / "workspace"
            workspace.mkdir()

            apk_file = temp_root / "wallet.apk"
            apk_file.write_bytes(b"apk")

            input_payload = {
                "program_name": "Acme Wallet",
                "program_url": "https://program.local/acme-wallet",
                "target_type": "whitebox",
                "focus_areas": ["Wallet", "Blockchain"],
                "package_names": ["com.acme.wallet"],
                "api_urls": ["https://api.wallet.local"],
                "smart_contracts": [{"name": "WalletRegistry", "address": "0xbeef"}],
                "artifacts": [apk_file.as_uri()],
            }
            input_path = temp_root / "input.json"
            input_path.write_text(json.dumps(input_payload), encoding="utf-8")

            result = self.run_script(input_path, workspace)
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            stdout = json.loads(result.stdout)
            self.assertEqual(stdout["suggested_lane"], "bounty-program-triage")
            self.assertIn("bounty-program-web", stdout["follow_on_lanes"])
            self.assertIn("bounty-program-smart-contracts", stdout["follow_on_lanes"])

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
                "focus_areas": ["Wallet"],
                "package_names": ["com.acme.app"],
                "artifacts": [apk_file.as_uri()],
            }
            input_path = temp_root / "input.json"
            input_path.write_text(json.dumps(input_payload), encoding="utf-8")

            result = self.run_script(input_path, workspace)
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            stdout = json.loads(result.stdout)
            self.assertEqual(stdout["suggested_lane"], "bounty-program-mobile-android")
            self.assertEqual(stdout["follow_on_lanes"], ["bounty-program-mobile-android"])
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
