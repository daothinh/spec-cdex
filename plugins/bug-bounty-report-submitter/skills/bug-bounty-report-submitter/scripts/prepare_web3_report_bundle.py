#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


KEY_PATTERNS = {
    "chain": re.compile(r"^\s*[-*]?\s*chain\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "network": re.compile(r"^\s*[-*]?\s*network\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "chain_id": re.compile(r"^\s*[-*]?\s*chain(?:\s+id|_id)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "affected_asset": re.compile(r"^\s*[-*]?\s*(?:affected\s+asset|asset|market|pool|vault)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "attack_capital": re.compile(r"^\s*[-*]?\s*(?:attack\s+capital|required\s+capital|capital)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "asset_delta": re.compile(r"^\s*[-*]?\s*(?:observed\s+asset\s+delta|asset\s+delta|balance\s+delta)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "prerequisites": re.compile(r"^\s*[-*]?\s*(?:prerequisites|preconditions|required\s+role)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "replay_mode": re.compile(r"^\s*[-*]?\s*(?:replay\s+mode|execution\s+mode|environment)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "success_signal": re.compile(r"^\s*[-*]?\s*(?:success\s+signal|observed\s+result|poc\s+output)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
}
ADDRESS_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
TX_RE = re.compile(r"\b0x[a-fA-F0-9]{64}\b")
BLOCK_RE = re.compile(r"\bblock(?:\s+number)?\s*[:#]?\s*(\d+)\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare web3-specific report artifacts from a verified finding bundle. "
            "Writes web3-facts.json, asset-delta.md, and reproduction-matrix.md."
        )
    )
    parser.add_argument("--finding-dir", required=True, help="Path to audit-targets/<slug>/findings/<finding-id>")
    parser.add_argument(
        "--bundle-dir",
        help="Optional bug-bounty-reports/<slug>/<finding-id> output path. Defaults to the finding directory.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated artifacts.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    finding_dir = Path(args.finding_dir).resolve()
    if not finding_dir.is_dir():
        print(f"error: finding directory does not exist: {finding_dir}", file=sys.stderr)
        return 1

    output_dir = Path(args.bundle_dir).resolve() if args.bundle_dir else finding_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.force:
        for filename in ("web3-facts.json", "asset-delta.md", "reproduction-matrix.md"):
            if (output_dir / filename).exists():
                print(f"error: {output_dir / filename} already exists. Re-run with --force to overwrite.", file=sys.stderr)
                return 1

    files = load_bundle_files(finding_dir)
    web3_facts = build_web3_facts(files)
    write_json(output_dir / "web3-facts.json", web3_facts)
    write_text(output_dir / "asset-delta.md", render_asset_delta(web3_facts, files))
    write_text(output_dir / "reproduction-matrix.md", render_reproduction_matrix(web3_facts, files))

    print(
        json.dumps(
            {
                "output_dir": output_dir.as_posix(),
                "generated": [
                    (output_dir / "web3-facts.json").as_posix(),
                    (output_dir / "asset-delta.md").as_posix(),
                    (output_dir / "reproduction-matrix.md").as_posix(),
                ],
            },
            indent=2,
        )
    )
    return 0


def load_bundle_files(finding_dir: Path) -> dict[str, str]:
    names = [
        "claim.md",
        "facts.md",
        "facts-chain.md",
        "poc.md",
        "impact.md",
        "impact-financials.md",
        "environment.md",
        "reverify.md",
        "severity.md",
    ]
    output: dict[str, str] = {}
    for name in names:
        path = finding_dir / name
        if path.exists():
            output[name] = path.read_text(encoding="utf-8")
        else:
            output[name] = ""
    return output


def build_web3_facts(files: dict[str, str]) -> dict[str, Any]:
    primary_text = "\n\n".join(
        part for part in (
            files["facts-chain.md"],
            files["impact-financials.md"],
            files["environment.md"],
            files["severity.md"],
            files["facts.md"],
            files["impact.md"],
            files["poc.md"],
            files["reverify.md"],
        )
        if part
    )
    contracts = sorted(set(ADDRESS_RE.findall(primary_text)))
    tx_hashes = sorted(set(TX_RE.findall(primary_text)))
    block_numbers = sorted(set(int(match) for match in BLOCK_RE.findall(primary_text)))

    return {
        "chain": first_match(KEY_PATTERNS["chain"], primary_text),
        "network": first_match(KEY_PATTERNS["network"], primary_text),
        "chain_id": first_match(KEY_PATTERNS["chain_id"], primary_text),
        "contract_addresses": contracts,
        "transaction_hashes": tx_hashes,
        "block_numbers": block_numbers,
        "affected_asset_or_market": first_match(KEY_PATTERNS["affected_asset"], primary_text),
        "observed_asset_delta": first_match(KEY_PATTERNS["asset_delta"], primary_text),
        "attack_capital_estimate": first_match(KEY_PATTERNS["attack_capital"], primary_text),
        "prerequisites": extract_multivalue(KEY_PATTERNS["prerequisites"], primary_text),
        "replay_mode": first_match(KEY_PATTERNS["replay_mode"], primary_text),
        "success_signal": first_match(KEY_PATTERNS["success_signal"], primary_text),
        "sources": {
            "facts_chain": bool(files["facts-chain.md"]),
            "impact_financials": bool(files["impact-financials.md"]),
            "environment": bool(files["environment.md"]),
            "severity": bool(files["severity.md"]),
        },
    }


def render_asset_delta(web3_facts: dict[str, Any], files: dict[str, str]) -> str:
    lines = ["# Asset Delta", ""]
    lines.append(f"- Affected Asset Or Market: {web3_facts['affected_asset_or_market'] or 'Not captured'}")
    lines.append(f"- Observed Asset Delta: {web3_facts['observed_asset_delta'] or 'Not captured'}")
    lines.append(f"- Attack Capital Estimate: {web3_facts['attack_capital_estimate'] or 'Not captured'}")
    lines.append("")
    lines.append("## Supporting Evidence")
    if files["impact-financials.md"]:
        lines.append("")
        lines.append(files["impact-financials.md"].strip())
    elif files["impact.md"]:
        lines.append("")
        lines.append(files["impact.md"].strip())
    else:
        lines.append("- No impact file was present. Add direct asset movement or market-state observations here.")
    return "\n".join(lines).rstrip() + "\n"


def render_reproduction_matrix(web3_facts: dict[str, Any], files: dict[str, str]) -> str:
    lines = [
        "# Reproduction Matrix",
        "",
        f"- Replay Mode: {web3_facts['replay_mode'] or 'Not captured'}",
        f"- Chain: {web3_facts['chain'] or 'Not captured'}",
        f"- Network: {web3_facts['network'] or 'Not captured'}",
        "",
        "## Preconditions",
    ]
    prereqs = web3_facts["prerequisites"] or []
    if prereqs:
        lines.extend(f"- {item}" for item in prereqs)
    else:
        lines.append("- No structured prerequisites were extracted. Add them manually if replay depends on roles or timing.")

    lines.extend(["", "## Replay Path"])
    poc_steps = extract_steps(files["poc.md"])
    if poc_steps:
        lines.extend(f"{index}. {step}" for index, step in enumerate(poc_steps, start=1))
    elif files["poc.md"]:
        lines.append(files["poc.md"].strip())
    else:
        lines.append("- No `poc.md` content was present.")

    lines.extend(["", "## Success Signal"])
    lines.append(f"- {web3_facts['success_signal'] or 'Not captured'}")

    lines.extend(["", "## Evidence Mapping"])
    evidence_items = []
    if files["facts-chain.md"]:
        evidence_items.append("`facts-chain.md` -> chain, tx, block, and contract identifiers")
    if files["impact-financials.md"]:
        evidence_items.append("`impact-financials.md` -> asset delta and capital assumptions")
    if files["environment.md"]:
        evidence_items.append("`environment.md` -> replay environment and assumptions")
    if files["reverify.md"]:
        evidence_items.append("`reverify.md` -> independent replay and falsification outcome")
    if files["severity.md"]:
        evidence_items.append("`severity.md` -> affected asset, severity, and downgrade notes")
    if evidence_items:
        lines.extend(f"- {item}" for item in evidence_items)
    else:
        lines.append("- No structured evidence files were present.")
    return "\n".join(lines).rstrip() + "\n"


def first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def extract_multivalue(pattern: re.Pattern[str], text: str) -> list[str]:
    values = [match.strip() for match in pattern.findall(text)]
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def extract_steps(poc_text: str) -> list[str]:
    if not poc_text:
        return []
    steps = []
    for line in poc_text.splitlines():
        stripped = line.strip()
        if re.match(r"^\d+\.\s+", stripped):
            steps.append(re.sub(r"^\d+\.\s+", "", stripped))
        elif stripped.startswith("- "):
            steps.append(stripped[2:])
    return steps


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
