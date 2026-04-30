#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

CAIDO_REQUEST_JSON_RE = re.compile(r"^request-(\d+)\.json$")
CAIDO_CURL_RE = re.compile(r"^request-(\d+)\.curl\.txt$")
CAIDO_RESPONSE_RE = re.compile(r"^response-(\d+)\.txt$")
CAIDO_REQUEST_RAW_RE = re.compile(r"^request-(\d+)\.txt$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Copy finding artifacts into a report bundle evidence directory and "
            "materialize artifacts.json, including Caido-specific evidence metadata."
        )
    )
    parser.add_argument("--finding-dir", required=True, help="Path to audit-targets/<slug>/findings/<finding-id>")
    parser.add_argument(
        "--bundle-dir",
        help="Optional bug-bounty-reports/<slug>/<finding-id> output path. Defaults to the finding directory.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite artifacts.json and existing copied evidence.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    finding_dir = Path(args.finding_dir).resolve()
    if not finding_dir.is_dir():
        print(f"error: finding directory does not exist: {finding_dir}", file=sys.stderr)
        return 1

    bundle_dir = Path(args.bundle_dir).resolve() if args.bundle_dir else finding_dir
    bundle_dir.mkdir(parents=True, exist_ok=True)
    source_artifacts_dir = finding_dir / "artifacts"
    output_manifest = bundle_dir / "artifacts.json"
    output_evidence_dir = bundle_dir / "evidence"

    if output_manifest.exists() and not args.force:
        print(f"error: {output_manifest} already exists. Re-run with --force to overwrite.", file=sys.stderr)
        return 1

    if output_evidence_dir.exists():
        if args.force:
            shutil.rmtree(output_evidence_dir)
        elif any(output_evidence_dir.iterdir()):
            print(f"error: {output_evidence_dir} already exists. Re-run with --force to overwrite.", file=sys.stderr)
            return 1

    output_evidence_dir.mkdir(parents=True, exist_ok=True)
    artifacts = build_artifact_manifest(source_artifacts_dir, output_evidence_dir)
    payload = {
        "source_artifacts_dir": relative_or_absolute(source_artifacts_dir, finding_dir),
        "bundle_evidence_dir": relative_or_absolute(output_evidence_dir, bundle_dir),
        "count": len(artifacts),
        "artifacts": artifacts,
    }
    output_manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "artifacts_json": output_manifest.as_posix(),
                "evidence_dir": output_evidence_dir.as_posix(),
                "count": len(artifacts),
            },
            indent=2,
        )
    )
    return 0


def build_artifact_manifest(source_dir: Path, output_dir: Path) -> list[dict[str, Any]]:
    if not source_dir.is_dir():
        return []

    entries: list[dict[str, Any]] = []
    files = sorted(path for path in source_dir.rglob("*") if path.is_file())
    for index, source_path in enumerate(files, start=1):
        rel_source = source_path.relative_to(source_dir)
        bundle_path = output_dir / rel_source
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, bundle_path)
        entries.append(build_entry(index=index, rel_source=rel_source, source_path=source_path, bundle_path=bundle_path))
    return entries


def build_entry(*, index: int, rel_source: Path, source_path: Path, bundle_path: Path) -> dict[str, Any]:
    rel_source_posix = rel_source.as_posix()
    kind = infer_kind(rel_source)
    description = default_description(kind, rel_source)
    details: dict[str, Any] = {}

    if kind == "caido-request-metadata":
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        request = payload.get("request", {})
        request_id = request.get("id") or payload.get("requestId")
        details = {
            "request_id": request_id,
            "method": request.get("method"),
            "host": request.get("host"),
            "path": request.get("path"),
            "status_code": (payload.get("response") or {}).get("statusCode"),
        }
        method = request.get("method") or "request"
        host = request.get("host") or "unknown-host"
        path = request.get("path") or "/"
        description = f"Caido request metadata for {method} {host}{path}"
    else:
        request_id = request_id_from_name(rel_source.name)
        if request_id:
            details["request_id"] = request_id

    entry = {
        "id": f"ART-{index:03d}",
        "filename": rel_source.name,
        "relative_source_path": Path("artifacts", rel_source).as_posix(),
        "relative_bundle_path": Path("evidence", rel_source).as_posix(),
        "kind": kind,
        "description": description,
    }
    if details:
        entry["details"] = {key: value for key, value in details.items() if value not in (None, "", [])}
    return entry


def infer_kind(rel_source: Path) -> str:
    parts = rel_source.parts
    if parts and parts[0] == "caido":
        if CAIDO_REQUEST_JSON_RE.match(rel_source.name):
            return "caido-request-metadata"
        if CAIDO_CURL_RE.match(rel_source.name):
            return "caido-curl"
        if CAIDO_RESPONSE_RE.match(rel_source.name):
            return "caido-response"
        if CAIDO_REQUEST_RAW_RE.match(rel_source.name):
            return "caido-request-raw"
        return "caido-artifact"

    suffix = rel_source.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return "image"
    if suffix in {".har"}:
        return "har"
    if suffix in {".json"}:
        return "json"
    if suffix in {".log", ".txt"}:
        return "text"
    if suffix in {".py", ".js", ".ts", ".sh", ".ps1"}:
        return "script"
    return "artifact"


def default_description(kind: str, rel_source: Path) -> str:
    if kind == "caido-curl":
        request_id = request_id_from_name(rel_source.name)
        return f"Exported Caido curl PoC for request {request_id}" if request_id else "Exported Caido curl PoC"
    if kind == "caido-response":
        request_id = request_id_from_name(rel_source.name)
        return f"Formatted Caido response snapshot for request {request_id}" if request_id else "Formatted Caido response snapshot"
    if kind == "caido-request-raw":
        request_id = request_id_from_name(rel_source.name)
        return f"Raw Caido request snapshot for request {request_id}" if request_id else "Raw Caido request snapshot"
    if kind == "caido-artifact":
        return f"Additional Caido artifact at {rel_source.as_posix()}"
    return f"Supporting evidence file at {rel_source.as_posix()}"


def request_id_from_name(name: str) -> str:
    for pattern in (CAIDO_REQUEST_JSON_RE, CAIDO_CURL_RE, CAIDO_RESPONSE_RE, CAIDO_REQUEST_RAW_RE):
        match = pattern.match(name)
        if match:
            return match.group(1)
    return ""


def relative_or_absolute(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
