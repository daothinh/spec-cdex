#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


BASE_REQUIRED_FILES = [
    "artifacts.json",
    "manual-review.md",
    "poc.md",
    "reverify.md",
    "severity.md",
    "external-evidence.json",
]

PAYLOAD_FILE_BY_CHANNEL = {
    "form": "submission.json",
    "email": "mail-envelope.json",
}

PRIMARY_DRAFT_BY_CHANNEL = {
    "form": "report.md",
    "email": "email-draft.md",
}

URL_PATTERN = re.compile(r"^https?://\S+$", re.IGNORECASE)
GIST_URL_PATTERN = re.compile(r"^https?://gist\.github\.com/\S+$", re.IGNORECASE)
COMMAND_PREFIXES = (
    "$ ",
    "forge ",
    "cargo ",
    "python ",
    "python3 ",
    "pytest ",
    "npm ",
    "pnpm ",
    "bun ",
    "node ",
    "curl ",
    "cast ",
    "anvil ",
    "go test ",
    "git clone ",
)
OUTPUT_MARKERS = ("[PASS]", "Logs:", "Suite result:", "status code", "balance", "delta", "reserve", "returned", "assert")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a bug-bounty submission bundle before final form or email submission."
    )
    parser.add_argument("--bundle-dir", required=True, help="Path to bug-bounty-reports/<slug>/<finding-id>")
    parser.add_argument("--channel", required=True, choices=("form", "email"), help="Submission channel")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle_dir = Path(args.bundle_dir).resolve()
    if not bundle_dir.is_dir():
        return emit_and_exit(
            ok=False,
            errors=[f"bundle directory does not exist: {bundle_dir}"],
            channel=args.channel,
            bundle_dir=bundle_dir,
        )

    payload_path = bundle_dir / PAYLOAD_FILE_BY_CHANNEL[args.channel]
    payload = load_json(payload_path)
    errors: list[str] = []
    warnings: list[str] = []

    for filename in BASE_REQUIRED_FILES + [PAYLOAD_FILE_BY_CHANNEL[args.channel], PRIMARY_DRAFT_BY_CHANNEL[args.channel]]:
        if not (bundle_dir / filename).exists():
            errors.append(f"missing required file: {filename}")

    poc_text = read_text_if_exists(bundle_dir / "poc.md")
    run_commands = infer_commands(
        [
            poc_text,
            read_text_if_exists(bundle_dir / "report.md"),
            read_text_if_exists(bundle_dir / "report-appendix.md"),
        ]
    )
    replay_steps = extract_steps(poc_text)
    success_signals = infer_success_signals(
        [
            read_text_if_exists(bundle_dir / "report-appendix.md"),
            read_text_if_exists(bundle_dir / "report.md"),
            poc_text,
            read_first_text_artifact(bundle_dir / "evidence"),
        ]
    )
    validate_replay_material(
        poc_text=poc_text,
        run_commands=run_commands,
        replay_steps=replay_steps,
        success_signals=success_signals,
        errors=errors,
    )

    primary_draft_path = bundle_dir / PRIMARY_DRAFT_BY_CHANNEL[args.channel]
    primary_draft_text = read_text_if_exists(primary_draft_path)

    if payload is None:
        errors.append(f"invalid JSON payload: {payload_path.name}")
    else:
        external_evidence_path = bundle_dir / "external-evidence.json"
        external_evidence = load_json(external_evidence_path)
        if external_evidence is None:
            errors.append("invalid JSON payload: external-evidence.json")
        else:
            validate_external_proof(
                payload=payload,
                external_evidence=external_evidence,
                primary_draft_text=primary_draft_text,
                errors=errors,
                warnings=warnings,
            )

    return emit_and_exit(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        channel=args.channel,
        bundle_dir=bundle_dir,
        payload_path=payload_path,
    )


def validate_external_proof(
    *,
    payload: dict[str, Any],
    external_evidence: dict[str, Any],
    primary_draft_text: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    external_proof = payload.get("external_proof")
    gist = external_evidence.get("gist") or {}
    proof_type = str(external_evidence.get("type") or "").strip()
    submission_requirement = str(external_evidence.get("submission_requirement") or "").strip()
    gist_url = str(gist.get("url") or "").strip()
    gist_published = bool(gist.get("published"))

    if not external_proof:
        errors.append("external-evidence.json exists but payload is missing external_proof contract")
        return
    if not isinstance(external_proof, dict):
        errors.append("payload external_proof must be a JSON object")
        return

    required = external_proof.get("required")
    if not isinstance(required, bool):
        errors.append("payload external_proof.required must be true or false")

    target_field = str(external_proof.get("target_field") or "").strip()
    inline_note_required = external_proof.get("inline_note_required")
    source = str(external_proof.get("source") or "").strip()

    if source != "external-evidence.json":
        errors.append("payload external_proof.source must be external-evidence.json")
    if not target_field:
        errors.append("payload external_proof.target_field is required")
    if inline_note_required is not True:
        errors.append("payload external_proof.inline_note_required must be true")

    payload_type = str(external_proof.get("type") or "").strip()
    if proof_type and payload_type and payload_type != proof_type:
        errors.append(
            f"payload external_proof.type ({payload_type}) does not match external-evidence.json type ({proof_type})"
        )

    payload_url = str(external_proof.get("url") or "").strip()
    if proof_type != "secret-gist":
        errors.append("external-evidence.json must use type secret-gist")
    if not gist_published:
        errors.append("external-evidence.json must contain a published secret gist")
    if not gist_url:
        errors.append("external-evidence.json gist.url is required")
    elif not GIST_URL_PATTERN.match(gist_url):
        errors.append("external-evidence.json gist.url must be a gist.github.com URL")
    if not payload_url:
        errors.append("payload external_proof.url is required")
    elif not GIST_URL_PATTERN.match(payload_url):
        errors.append("payload external_proof.url must be a gist.github.com URL")
    elif gist_url and payload_url != gist_url:
        errors.append("payload external_proof.url does not match external-evidence.json gist.url")

    if required is not True:
        errors.append("payload external_proof.required must be true")
    if submission_requirement != "include-secret-gist-reference":
        errors.append("external-evidence.json submission_requirement must be include-secret-gist-reference")
    if not external_evidence.get("requires_url_field"):
        errors.append("external-evidence.json requires_url_field must be true")

    if gist_url:
        if gist_url not in primary_draft_text:
            errors.append("primary report draft must include the gist URL")
        opening_paragraph = extract_opening_paragraph(primary_draft_text)
        if opening_paragraph and gist_url not in opening_paragraph:
            errors.append("opening summary/intro must include the gist URL")
        if not payload_contains_text_outside_external_proof(payload, gist_url):
            errors.append("submission payload must include the gist URL in a report field")


def emit_and_exit(
    *,
    ok: bool,
    errors: list[str],
    warnings: list[str] | None = None,
    channel: str,
    bundle_dir: Path,
    payload_path: Path | None = None,
) -> int:
    warnings = warnings or []
    result = {
        "ok": ok,
        "channel": channel,
        "bundle_dir": bundle_dir.as_posix(),
        "payload_path": payload_path.as_posix() if payload_path else None,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, indent=2))
    if ok:
        print("validation: PASS", file=sys.stderr)
        return 0
    print(f"validation: BLOCKED - {errors[0]}", file=sys.stderr)
    return 1


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def validate_replay_material(
    *,
    poc_text: str,
    run_commands: list[str],
    replay_steps: list[str],
    success_signals: list[str],
    errors: list[str],
) -> None:
    if not poc_text:
        errors.append("bundle is missing poc.md content")
    if not run_commands and not replay_steps:
        errors.append("no runnable replay material found in poc.md")
    if not success_signals:
        errors.append("no decisive success signal found in report.md/report-appendix.md/evidence")


def infer_commands(texts: list[str]) -> list[str]:
    commands: list[str] = []
    for text in texts:
        if not text:
            continue
        in_block = False
        block_language = ""
        block_lines: list[str] = []
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("```"):
                if in_block:
                    if block_language in {"", "bash", "sh", "shell", "console", "zsh", "powershell", "pwsh"}:
                        for block_line in block_lines:
                            candidate = normalize_command(block_line)
                            if candidate:
                                commands.append(candidate)
                    in_block = False
                    block_language = ""
                    block_lines = []
                else:
                    in_block = True
                    block_language = stripped[3:].strip().lower()
                continue
            if in_block:
                block_lines.append(raw_line.rstrip())
                continue
            candidate = normalize_command(stripped)
            if candidate:
                commands.append(candidate)
    return unique(commands)


def normalize_command(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    if stripped.startswith("$ "):
        stripped = stripped[2:].strip()
    if stripped.startswith("#"):
        return ""
    return stripped if any(stripped.startswith(prefix.strip()) for prefix in COMMAND_PREFIXES) else ""


def extract_opening_paragraph(text: str) -> str:
    if not text:
        return ""
    paragraph_lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            if paragraph_lines:
                break
            continue
        if not paragraph_lines and (stripped.startswith("#") or stripped.startswith(">")):
            continue
        paragraph_lines.append(stripped)
    return " ".join(paragraph_lines).strip()


def infer_success_signals(texts: list[str]) -> list[str]:
    signals: list[str] = []
    for text in texts:
        if not text:
            continue
        for block in extract_output_blocks(text):
            if block:
                signals.append(block)
        if signals:
            continue
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if stripped and any(marker.lower() in stripped.lower() for marker in OUTPUT_MARKERS):
                signals.append(stripped)
        if signals:
            continue
    return unique(signals)


def extract_output_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        stripped = lines[index].strip().lower()
        if "output from poc" in stripped or "observed output" in stripped or "success signal" in stripped:
            index += 1
            while index < len(lines) and not lines[index].strip():
                index += 1
            if index < len(lines) and lines[index].strip().startswith("```"):
                index += 1
                captured: list[str] = []
                while index < len(lines) and not lines[index].strip().startswith("```"):
                    if lines[index].strip():
                        captured.append(lines[index].rstrip())
                    index += 1
                if captured:
                    blocks.append("\n".join(captured))
            elif index < len(lines) and lines[index].strip():
                blocks.append(lines[index].strip())
        index += 1
    return blocks


def extract_steps(text: str) -> list[str]:
    if not text:
        return []
    steps: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^\d+\.\s+", stripped):
            steps.append(re.sub(r"^\d+\.\s+", "", stripped))
        elif stripped.startswith("- "):
            steps.append(stripped[2:])
    return unique(steps)


def read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_first_text_artifact(evidence_dir: Path) -> str:
    if not evidence_dir.is_dir():
        return ""
    for candidate in sorted(path for path in evidence_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".log", ".txt"}):
        return candidate.read_text(encoding="utf-8", errors="ignore")
    return ""


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)
    return output


def payload_contains_text(payload: dict[str, Any], needle: str) -> bool:
    for value in payload.values():
        if isinstance(value, str) and needle in value:
            return True
        if isinstance(value, dict) and payload_contains_text(value, needle):
            return True
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and needle in item:
                    return True
                if isinstance(item, dict) and payload_contains_text(item, needle):
                    return True
    return False


def payload_contains_text_outside_external_proof(payload: dict[str, Any], needle: str) -> bool:
    for key, value in payload.items():
        if key == "external_proof":
            continue
        if isinstance(value, str) and needle in value:
            return True
        if isinstance(value, dict) and payload_contains_text(value, needle):
            return True
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and needle in item:
                    return True
                if isinstance(item, dict) and payload_contains_text(item, needle):
                    return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
