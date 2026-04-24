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
    / "prepare_web3_report_bundle.py"
)


class PrepareWeb3ReportBundleTests(unittest.TestCase):
    def test_generates_web3_bundle_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            finding_dir = root / "finding"
            finding_dir.mkdir()

            (finding_dir / "facts-chain.md").write_text(
                "\n".join(
                    [
                        "- Chain: Ethereum",
                        "- Network: mainnet",
                        "- Chain ID: 1",
                        "- Affected Asset: Vault share supply",
                        "- Prerequisites: attacker can deposit and call withdraw",
                        "- Success Signal: attacker receives inflated shares",
                        "- Transaction Hash: 0x" + "a" * 64,
                        "- Block: 12345678",
                        "- Contract: 0x" + "b" * 40,
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (finding_dir / "impact-financials.md").write_text(
                "\n".join(
                    [
                        "- Observed Asset Delta: attacker withdraws 12.4 ETH more than deposited",
                        "- Attack Capital: 1 wei seed deposit plus one normal deposit",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (finding_dir / "environment.md").write_text(
                "\n".join(
                    [
                        "- Replay Mode: fork-capable",
                        "- Preconditions: mainnet fork at block 12345678",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (finding_dir / "poc.md").write_text(
                "1. Fork mainnet.\n2. Seed the vault.\n3. Trigger the inflated withdrawal.\n",
                encoding="utf-8",
            )
            (finding_dir / "impact.md").write_text("Observed vault drain path.\n", encoding="utf-8")
            (finding_dir / "reverify.md").write_text("TRUE POSITIVE\n", encoding="utf-8")
            (finding_dir / "severity.md").write_text("- Severity: High\n", encoding="utf-8")
            (finding_dir / "facts.md").write_text("Observed reproducible share inflation.\n", encoding="utf-8")
            (finding_dir / "claim.md").write_text("Vault share inflation lets attackers drain assets.\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--finding-dir", str(finding_dir)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            web3_facts = json.loads((finding_dir / "web3-facts.json").read_text(encoding="utf-8"))
            self.assertEqual(web3_facts["chain"], "Ethereum")
            self.assertEqual(web3_facts["network"], "mainnet")
            self.assertEqual(web3_facts["chain_id"], "1")
            self.assertEqual(web3_facts["block_numbers"], [12345678])
            self.assertEqual(len(web3_facts["contract_addresses"]), 1)
            self.assertEqual(len(web3_facts["transaction_hashes"]), 1)
            self.assertEqual(
                web3_facts["observed_asset_delta"],
                "attacker withdraws 12.4 ETH more than deposited",
            )
            self.assertEqual(web3_facts["replay_mode"], "fork-capable")

            asset_delta = (finding_dir / "asset-delta.md").read_text(encoding="utf-8")
            self.assertIn("Observed Asset Delta", asset_delta)
            self.assertIn("12.4 ETH", asset_delta)

            reproduction = (finding_dir / "reproduction-matrix.md").read_text(encoding="utf-8")
            self.assertIn("Replay Mode: fork-capable", reproduction)
            self.assertIn("Fork mainnet.", reproduction)
            self.assertIn("facts-chain.md", reproduction)


if __name__ == "__main__":
    unittest.main()
