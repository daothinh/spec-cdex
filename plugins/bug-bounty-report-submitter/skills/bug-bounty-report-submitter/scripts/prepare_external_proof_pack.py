#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CORE_FILES = [
    ("report.md", "report-draft", "Final local report draft"),
    ("report-appendix.md", "report-appendix", "Field-limit appendix with the full runnable proof"),
    ("poc.md", "poc-markdown", "Replayable PoC instructions"),
    ("artifacts.json", "artifacts-manifest", "Evidence inventory"),
    ("reproduction-matrix.md", "reproduction-matrix", "Replay prerequisites and matrix"),
    ("asset-delta.md", "asset-delta", "Observed asset or balance delta summary"),
    ("web3-facts.json", "web3-facts", "Structured web3 replay facts"),
    ("environment.md", "environment", "Replay environment and assumptions"),
    ("facts-chain.md", "facts-chain", "Chain or market identifiers"),
    ("severity.md", "severity", "Severity and downgrade notes"),
]

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
ASCIINEMA_URL_PATTERN = re.compile(r"^https?://asciinema\.org/a/\S+$", re.IGNORECASE)
CODE_EXTENSIONS = {".py", ".js", ".ts", ".sh", ".ps1", ".sol", ".rs", ".go", ".c", ".cc", ".cpp", ".java"}
TEST_PATH_PARTS = {"test", "tests", "__tests__"}
GIST_REFERENCE_LABEL = "PoC and logs"
ASCIINEMA_REFERENCE_LABEL = "PoC runtime"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a gist-ready proof pack from a local bug bounty report bundle. "
            "Copies core proof files, flattens evidence/ entries, writes a manifest, "
            "and can optionally publish a secret GitHub gist."
        )
    )
    parser.add_argument("--bundle-dir", required=True, help="Path to bug-bounty-reports/<slug>/<finding-id>")
    parser.add_argument("--output-dir", help="Optional proof-pack directory. Defaults to <bundle-dir>/proof-pack")
    parser.add_argument("--title", help="Optional proof-pack title")
    parser.add_argument(
        "--summary",
        default="Runnable PoC, logs, and helper artifacts for a field-limited bug bounty submission.",
        help="One-line proof-pack summary",
    )
    parser.add_argument("--run-command", action="append", default=[], help="Exact replay command. Repeatable.")
    parser.add_argument("--success-signal", action="append", default=[], help="Decisive expected output. Repeatable.")
    parser.add_argument("--publish-gist", action="store_true", help="Publish the proof pack with `gh gist create`.")
    parser.add_argument("--gist-url", help="Use an existing secret gist URL instead of publishing one.")
    parser.add_argument("--gist-desc", help="Optional gist description. Defaults to the proof-pack title.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing proof-pack directory and metadata.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle_dir = Path(args.bundle_dir).resolve()
    if not bundle_dir.is_dir():
        print(f"error: bundle directory does not exist: {bundle_dir}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir).resolve() if args.output_dir else bundle_dir / "proof-pack"
    if output_dir.exists():
        if not args.force:
            print(f"error: proof-pack directory already exists: {output_dir}", file=sys.stderr)
            return 1
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    title = args.title or f"{bundle_dir.parent.name}/{bundle_dir.name} runnable proof pack"
    artifact_map = load_artifact_map(bundle_dir / "artifacts.json")
    pack_files = copy_bundle_files(bundle_dir, output_dir, artifact_map)
    gist_candidate_files = select_gist_files(output_dir=output_dir, pack_files=pack_files)
    asciinema_session = load_asciinema_session(bundle_dir)

    poc_text = read_text_if_exists(bundle_dir / "poc.md")
    run_commands = unique(args.run_command + infer_commands([poc_text, read_text_if_exists(bundle_dir / "report-appendix.md"), read_text_if_exists(bundle_dir / "report.md")]))
    success_signals = unique(
        args.success_signal
        + infer_success_signals(
            [
                read_text_if_exists(bundle_dir / "report-appendix.md"),
                read_text_if_exists(bundle_dir / "report.md"),
                poc_text,
                read_first_text_artifact(bundle_dir / "evidence"),
            ]
        )
    )
    replay_steps = extract_steps(poc_text)
    validate_replay_material(poc_text=poc_text, run_commands=run_commands, replay_steps=replay_steps, success_signals=success_signals)

    manifest = {
        "title": title,
        "summary": args.summary,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bundle_dir": bundle_dir.as_posix(),
        "proof_pack_dir": output_dir.as_posix(),
        "run_commands": run_commands,
        "replay_steps": replay_steps,
        "success_signals": success_signals,
        "asciinema": {
            "metadata_path": relative_or_absolute(asciinema_session["metadata_path"], bundle_dir),
            "local_cast_path": relative_or_absolute(asciinema_session["cast_path"], bundle_dir),
            "server_url": asciinema_session["server_url"],
            "link_markdown": markdown_link(asciinema_session["server_url"]),
        },
        "gist": {"published": False, "url": None, "visibility": None},
        "gist_candidate_files": [Path(path).name for path in gist_candidate_files],
        "files": pack_files,
    }
    index_path = output_dir / "external-proof-pack.md"
    index_path.write_text(
        render_index(
            title=title,
            summary=args.summary,
            gist_url="",
            asciinema_url=asciinema_session["server_url"],
            run_commands=run_commands,
            replay_steps=replay_steps,
            success_signals=success_signals,
            files=pack_files,
        ),
        encoding="utf-8",
    )
    manifest_path = output_dir / "external-proof-pack.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    gist_url = (args.gist_url or "").strip()
    if args.publish_gist and gist_url:
        raise SystemExit("error: provide either --publish-gist or --gist-url, not both")
    if args.publish_gist:
        gist_desc = args.gist_desc or title
        gist_url = publish_gist(output_dir=output_dir, description=gist_desc, gist_candidate_files=gist_candidate_files)
    if not gist_url:
        raise SystemExit("error: gist link is required. Use --publish-gist or provide --gist-url.")
    manifest["gist"] = {"published": True, "url": gist_url, "visibility": "secret"}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    index_path.write_text(
        render_index(
            title=title,
            summary=args.summary,
            gist_url=gist_url,
            asciinema_url=asciinema_session["server_url"],
            run_commands=run_commands,
            replay_steps=replay_steps,
            success_signals=success_signals,
            files=pack_files,
        ),
        encoding="utf-8",
    )

    external_evidence = {
        "type": "secret-gist",
        "title": title,
        "summary": args.summary,
        "proof_pack_dir": relative_or_absolute(output_dir, bundle_dir),
        "index_markdown": relative_or_absolute(index_path, bundle_dir),
        "manifest_json": relative_or_absolute(manifest_path, bundle_dir),
        "run_commands": run_commands,
        "replay_steps": replay_steps,
        "success_signals": success_signals,
        "suggested_reference_text": (
            "Full runnable PoC, raw logs, and helper files are preserved in the linked secret gist. "
            "The recorded terminal replay is preserved in the linked asciinema session. "
            "The inline body still contains the vulnerable location, replay command or sequence, and decisive output."
        ),
        "recommended_field_labels": [
            "Reference URL",
            "Evidence URL",
            "Supporting Links",
            "Additional References",
        ],
        "suggested_inline_note": (
            "Full runnable PoC, raw logs, and helper files are preserved in the linked secret gist. "
            "The recorded terminal replay is preserved in the linked asciinema session. "
            "This report body still contains the exact vulnerable location, replay command or sequence, and decisive output."
        ),
        "requires_url_field": True,
        "submission_requirement": "include-secret-gist-reference",
        "recording_requirement": "include-asciinema-reference",
        "asciinema": {
            "required": True,
            "metadata_path": relative_or_absolute(asciinema_session["metadata_path"], bundle_dir),
            "local_cast_path": relative_or_absolute(asciinema_session["cast_path"], bundle_dir),
            "server_url": asciinema_session["server_url"],
            "link_markdown": markdown_link(asciinema_session["server_url"]),
        },
        "suggested_reference_block": "\n".join(
            [
                labeled_markdown_link(GIST_REFERENCE_LABEL, gist_url),
                labeled_markdown_link(ASCIINEMA_REFERENCE_LABEL, asciinema_session["server_url"]),
            ]
        ),
        "gist": {
            "published": True,
            "url": gist_url,
            "visibility": "secret",
        },
        "mandatory_reviewer_files": [Path(path).name for path in gist_candidate_files],
    }
    external_evidence_path = bundle_dir / "external-evidence.json"
    external_evidence_path.write_text(json.dumps(external_evidence, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "proof_pack_dir": output_dir.as_posix(),
                "manifest_json": manifest_path.as_posix(),
                "index_markdown": index_path.as_posix(),
                "external_evidence_json": external_evidence_path.as_posix(),
                "gist_url": gist_url,
                "asciinema_url": asciinema_session["server_url"],
                "count": len(pack_files),
            },
            indent=2,
        )
    )
    return 0


def load_artifact_map(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    mapping: dict[str, dict[str, Any]] = {}
    for item in payload.get("artifacts", []):
        relative_bundle_path = item.get("relative_bundle_path")
        if relative_bundle_path:
            mapping[relative_bundle_path] = item
    return mapping


def load_asciinema_session(bundle_dir: Path) -> dict[str, Any]:
    evidence_dir = bundle_dir / "evidence"
    if not evidence_dir.is_dir():
        raise SystemExit("error: missing evidence/ directory; run prepare_report_artifacts.py before preparing the proof pack")

    candidates = sorted(evidence_dir.rglob("asciinema-session.json"))
    if not candidates:
        raise SystemExit(
            "error: missing asciinema replay metadata in evidence/. Run record_asciinema_replay.py during final reverify first."
        )

    for metadata_path in candidates:
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict) or payload.get("tool") != "asciinema":
            continue

        relative_cast = str(payload.get("local_cast_path") or payload.get("cast_filename") or "").strip()
        if not relative_cast:
            raise SystemExit("error: asciinema-session.json is missing local_cast_path")
        cast_path = (metadata_path.parent / relative_cast).resolve()
        if not cast_path.is_file():
            raise SystemExit(f"error: asciinema cast file referenced by {metadata_path.name} does not exist: {cast_path}")

        server_url = str(payload.get("server_url") or "").strip()
        if not server_url:
            raise SystemExit("error: asciinema-session.json is missing server_url")
        if not ASCIINEMA_URL_PATTERN.match(server_url):
            raise SystemExit("error: asciinema-session.json server_url must be an asciinema.org URL")

        return {
            "metadata_path": metadata_path.resolve(),
            "cast_path": cast_path,
            "server_url": server_url,
            "payload": payload,
        }

    raise SystemExit("error: unable to load a valid asciinema-session.json from evidence/")


def copy_bundle_files(bundle_dir: Path, output_dir: Path, artifact_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    for index, (name, category, description) in enumerate(CORE_FILES, start=1):
        source = bundle_dir / name
        if not source.exists():
            continue
        destination = output_dir / name
        shutil.copyfile(source, destination)
        copied.append(
            {
                "id": f"DOC-{index:03d}",
                "pack_filename": destination.name,
                "source_relative_path": source.relative_to(bundle_dir).as_posix(),
                "category": category,
                "description": description,
            }
        )

    evidence_dir = bundle_dir / "evidence"
    if not evidence_dir.is_dir():
        return copied

    file_index = 1
    for source in sorted(path for path in evidence_dir.rglob("*") if path.is_file()):
        rel = source.relative_to(bundle_dir)
        destination = output_dir / flatten_name(rel)
        shutil.copyfile(source, destination)
        artifact = artifact_map.get(rel.as_posix(), {})
        copied.append(
            {
                "id": artifact.get("id") or f"EV-{file_index:03d}",
                "pack_filename": destination.name,
                "source_relative_path": rel.as_posix(),
                "category": artifact.get("kind") or infer_category(source.suffix.lower()),
                "description": artifact.get("description") or f"Supporting evidence copied from {rel.as_posix()}",
            }
        )
        file_index += 1
    return copied


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


def validate_replay_material(*, poc_text: str, run_commands: list[str], replay_steps: list[str], success_signals: list[str]) -> None:
    if not poc_text:
        raise SystemExit("error: bundle is missing poc.md content")
    if not run_commands and not replay_steps:
        raise SystemExit("error: no runnable replay material found in poc.md. Add --run-command or numbered replay steps.")
    if not success_signals:
        raise SystemExit("error: no decisive success signal found. Add --success-signal or include observed output in report.md/report-appendix.md.")


def publish_gist(*, output_dir: Path, description: str, gist_candidate_files: list[str]) -> str:
    files = gist_candidate_files
    if not files:
        raise SystemExit("error: proof-pack directory is empty; nothing to publish")
    result = subprocess.run(
        ["gh", "gist", "create", *files, "-d", description],
        check=False,
        capture_output=True,
        text=True,
        cwd=output_dir,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "unknown gh gist create failure"
        raise SystemExit(f"error: failed to publish secret gist: {stderr}")
    stdout = result.stdout.strip()
    if not stdout:
        raise SystemExit("error: gh gist create succeeded without returning a gist URL")
    return stdout.splitlines()[-1].strip()


def select_gist_files(*, output_dir: Path, pack_files: list[dict[str, Any]]) -> list[str]:
    evidence_items = [item for item in pack_files if str(item.get("source_relative_path") or "").startswith("evidence/")]
    reference_text = "\n".join(
        part
        for part in (
            read_text_if_exists(output_dir / "poc.md"),
            read_text_if_exists(output_dir / "report.md"),
            read_text_if_exists(output_dir / "report-appendix.md"),
        )
        if part
    )

    replay_files: list[str] = []
    report_files: list[str] = []
    log_files: list[str] = []
    replay_seen: set[str] = set()
    log_seen: set[str] = set()

    referenced_items = referenced_evidence_items(reference_text=reference_text, evidence_items=evidence_items)
    if referenced_items:
        for item in referenced_items:
            filename = str(item.get("pack_filename") or "").strip()
            source_relative_path = str(item.get("source_relative_path") or "").strip()
            category = str(item.get("category") or "").strip().lower()
            path = output_dir / filename
            if not path.is_file():
                continue
            if is_output_log_file(filename=filename, source_relative_path=source_relative_path, category=category):
                log_files.append(str(path))
                log_seen.add(filename)
            else:
                replay_files.append(str(path))
                replay_seen.add(filename)

    for item in pack_files:
        filename = str(item.get("pack_filename") or "").strip()
        if not filename:
            continue
        source_relative_path = str(item.get("source_relative_path") or "").strip()
        category = str(item.get("category") or "").strip().lower()
        path = output_dir / filename
        if not path.is_file():
            continue

        if filename in replay_seen or filename in log_seen:
            continue
        if not replay_files and is_default_replay_file(source_relative_path=source_relative_path, category=category):
            replay_files.append(str(path))
            replay_seen.add(filename)
            continue
        if filename == "report.md" or (filename == "report-appendix.md" and not report_files):
            report_files.append(str(path))
            continue
        if is_output_log_file(filename=filename, source_relative_path=source_relative_path, category=category):
            log_files.append(str(path))
            log_seen.add(filename)

    ordered = unique_paths(replay_files) + unique_paths(report_files) + unique_paths(log_files)
    standalone_poc_candidates = [
        path
        for path in ordered
        if is_standalone_poc_item(next((item for item in evidence_items if str(output_dir / str(item.get("pack_filename") or "").strip()) == path), None))
    ]
    output_log_candidates = [
        path
        for path in ordered
        if is_output_log_item(next((item for item in evidence_items if str(output_dir / str(item.get("pack_filename") or "").strip()) == path), None))
    ]
    if not standalone_poc_candidates:
        raise SystemExit("error: proof-pack must include a standalone PoC code file and it must not depend on /test")
    if not output_log_candidates:
        raise SystemExit("error: proof-pack must include a decisive output log file")
    return ordered


def is_default_replay_file(*, source_relative_path: str, category: str) -> bool:
    if not source_relative_path.startswith("evidence/"):
        return False
    if is_test_harness_path(source_relative_path):
        return False
    return category in {"code", "script"} or Path(source_relative_path).suffix.lower() in CODE_EXTENSIONS


def referenced_evidence_items(*, reference_text: str, evidence_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not reference_text.strip():
        return []

    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(evidence_items):
        filename = str(item.get("pack_filename") or "").strip()
        source_relative_path = str(item.get("source_relative_path") or "").strip()
        basename = Path(source_relative_path).name if source_relative_path else ""
        candidates = unique(
            [
                source_relative_path,
                filename,
                basename,
                f"`{source_relative_path}`" if source_relative_path else "",
                f"`{basename}`" if basename else "",
            ]
        )
        position = first_match_position(reference_text, candidates)
        if position is None:
            continue
        ranked.append((position, index, item))

    ranked.sort(key=lambda row: (row[0], row[1]))
    return [item for _, _, item in ranked]


def first_match_position(text: str, candidates: list[str]) -> int | None:
    best: int | None = None
    haystack = text
    for candidate in candidates:
        if not candidate:
            continue
        position = haystack.find(candidate)
        if position == -1:
            continue
        if best is None or position < best:
            best = position
    return best


def is_output_log_file(*, filename: str, source_relative_path: str, category: str) -> bool:
    if filename.endswith(".log"):
        return True
    if category == "text" and source_relative_path.startswith("evidence/"):
        lower_name = Path(filename).name.lower()
        lower_source = source_relative_path.lower()
        return "log" in lower_name or "output" in lower_name or "trace" in lower_name or "log" in lower_source
    return False


def is_standalone_poc_item(item: dict[str, Any] | None) -> bool:
    if not item:
        return False
    source_relative_path = str(item.get("source_relative_path") or "").strip()
    if not source_relative_path.startswith("evidence/"):
        return False
    if is_test_harness_path(source_relative_path):
        return False
    category = str(item.get("category") or "").strip().lower()
    suffix = Path(source_relative_path).suffix.lower()
    return category in {"code", "script"} or suffix in CODE_EXTENSIONS


def is_output_log_item(item: dict[str, Any] | None) -> bool:
    if not item:
        return False
    filename = str(item.get("pack_filename") or "").strip()
    source_relative_path = str(item.get("source_relative_path") or "").strip()
    category = str(item.get("category") or "").strip().lower()
    return is_output_log_file(filename=filename, source_relative_path=source_relative_path, category=category)


def is_test_harness_path(relative_path: str) -> bool:
    return any(part.lower() in TEST_PATH_PARTS for part in Path(relative_path).parts)


def unique_paths(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def render_index(
    *,
    title: str,
    summary: str,
    gist_url: str,
    asciinema_url: str,
    run_commands: list[str],
    replay_steps: list[str],
    success_signals: list[str],
    files: list[dict[str, Any]],
) -> str:
    lines = [f"# {title}", "", summary, ""]
    lines.extend(["## Reference Links", ""])
    if gist_url:
        lines.append(labeled_markdown_link(GIST_REFERENCE_LABEL, gist_url))
    lines.append(labeled_markdown_link(ASCIINEMA_REFERENCE_LABEL, asciinema_url))
    lines.append("")
    if run_commands:
        lines.extend(["## Replay Commands", ""])
        lines.extend(f"- `{command}`" for command in run_commands)
        lines.append("")
    if replay_steps:
        lines.extend(["## Replay Steps", ""])
        lines.extend(f"{index}. {step}" for index, step in enumerate(replay_steps, start=1))
        lines.append("")
    lines.extend(["## Success Signals", ""])
    lines.extend(f"- {signal}" for signal in success_signals)
    lines.extend(["", "## Included Files", ""])
    lines.extend(f"- `{item['pack_filename']}` -> {item['description']}" for item in files)
    lines.extend(
        [
            "",
            "## Suggested Reference Text",
            "",
            "Full runnable PoC, raw logs, and helper files are preserved in the linked secret gist.",
            "The gist must include the standalone PoC code file and the decisive output-log file.",
        ]
    )
    if gist_url:
        lines.append(labeled_markdown_link(GIST_REFERENCE_LABEL, gist_url))
    lines.extend(
        [
            labeled_markdown_link(ASCIINEMA_REFERENCE_LABEL, asciinema_url),
            "The inline report still contains the vulnerable location, replay command or sequence, and decisive output.",
            "",
        ]
    )
    return "\n".join(lines)


def infer_category(suffix: str) -> str:
    if suffix in {".log", ".txt"}:
        return "text"
    if suffix in {".cast"}:
        return "terminal-cast"
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return "image"
    if suffix in {".mp4", ".mov", ".webm"}:
        return "video"
    if suffix in {".json"}:
        return "json"
    if suffix in {".md"}:
        return "markdown"
    if suffix in {".py", ".js", ".ts", ".sh", ".ps1", ".sol"}:
        return "code"
    return "artifact"


def flatten_name(path: Path) -> str:
    return "__".join(path.parts)


def markdown_link(url: str) -> str:
    return f"[{url}]({url})"


def labeled_markdown_link(label: str, url: str) -> str:
    return f"{label}: {markdown_link(url)}"


def read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_first_text_artifact(evidence_dir: Path) -> str:
    if not evidence_dir.is_dir():
        return ""
    for candidate in sorted(
        path
        for path in evidence_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".cast", ".log", ".txt"}
    ):
        return candidate.read_text(encoding="utf-8", errors="ignore")
    return ""


def relative_or_absolute(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


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


if __name__ == "__main__":
    raise SystemExit(main())
