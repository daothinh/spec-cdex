#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname, urlopen

SUPPORTED_TARGET_TYPES = {"whitebox", "android"}
APK_SUFFIXES = (".apk", ".xapk", ".apks")
ARCHIVE_SUFFIXES = (".zip", ".tgz", ".tar.gz", ".tar", ".tar.bz2", ".tar.xz")
ANDROID_MARKERS = {
    "androidmanifest.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "gradlew",
}
SMART_CONTRACT_MARKERS = {
    "foundry.toml",
    "hardhat.config.js",
    "hardhat.config.ts",
    "truffle-config.js",
    "brownie-config.yaml",
    "anchor.toml",
}
WEB_MARKERS = {
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "pyproject.toml",
    "composer.json",
    "pom.xml",
    "manage.py",
    "go.mod",
}
NATIVE_MARKERS = {"cargo.toml", "cmakelists.txt", "meson.build", "makefile"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create an audit-target workspace from structured scope data, clone "
            "repos, download artifacts, and emit a suggested bounty lane."
        )
    )
    parser.add_argument("--input", required=True, help="Path to the normalized target JSON.")
    parser.add_argument("--repo-root", default=".", help="Repository root where audit-targets/ is created.")
    parser.add_argument(
        "--targets-dir",
        default="audit-targets",
        help="Relative directory under repo-root where targets are stored.",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing target directory.")
    parser.add_argument("--skip-clone", action="store_true", help="Do not clone source repositories.")
    parser.add_argument("--skip-downloads", action="store_true", help="Do not download artifacts.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    input_path = Path(args.input).resolve()

    try:
        raw_input = json.loads(input_path.read_text(encoding="utf-8"))
        target = normalize_target(raw_input)
        summary = bootstrap_target(
            target=target,
            raw_input=raw_input,
            repo_root=repo_root,
            targets_dir=args.targets_dir,
            force=args.force,
            skip_clone=args.skip_clone,
            skip_downloads=args.skip_downloads,
        )
    except Exception as exc:  # pragma: no cover - exercised via subprocess tests
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=2))
    return 0


def normalize_target(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Input JSON must be an object.")

    program_name = clean_text(raw.get("program_name") or raw.get("name"))
    if not program_name:
        raise ValueError("Missing required field: program_name")

    program_url = clean_text(raw.get("program_url"))
    if not program_url:
        raise ValueError("Missing required field: program_url")

    target_type = clean_text(raw.get("target_type")).lower()
    if target_type not in SUPPORTED_TARGET_TYPES:
        supported = ", ".join(sorted(SUPPORTED_TARGET_TYPES))
        raise ValueError(f"target_type must be one of: {supported}")

    artifacts = normalize_artifacts(raw)

    return {
        "program_name": program_name,
        "program_url": program_url,
        "target_type": target_type,
        "slug": slugify(clean_text(raw.get("slug")) or program_name),
        "scope_summary": clean_text(raw.get("scope_summary")),
        "in_scope": unique_text_list(raw.get("in_scope") or raw.get("scope") or raw.get("allowed_assets")),
        "out_of_scope": unique_text_list(
            raw.get("out_of_scope") or raw.get("out_scope") or raw.get("ignored_assets")
        ),
        "rules": unique_text_list(raw.get("rules")),
        "safe_harbor": unique_text_list(raw.get("safe_harbor")),
        "submission_guidelines": unique_text_list(raw.get("submission_guidelines")),
        "program_notes": unique_text_list(raw.get("program_notes")),
        "auth_notes": unique_text_list(raw.get("auth_notes")),
        "environment_notes": unique_text_list(raw.get("environment_notes")),
        "repo_urls": unique_text_list(raw.get("repo_urls") or raw.get("source_repos")),
        "package_names": unique_text_list(raw.get("package_names")),
        "app_urls": unique_text_list(raw.get("app_urls") or raw.get("store_urls")),
        "raw_scope_notes": clean_text(raw.get("raw_scope_notes")),
        "artifacts": artifacts,
    }


def normalize_artifacts(raw: dict[str, Any]) -> list[dict[str, str]]:
    combined: list[Any] = []
    for key in ("artifacts", "artifact_urls"):
        value = raw.get(key)
        if value is not None:
            combined.extend(value if isinstance(value, list) else [value])

    for key, kind in (("apk_urls", "apk"), ("source_archive_urls", "source-archive")):
        value = raw.get(key)
        for item in value if isinstance(value, list) else ([value] if value else []):
            combined.append({"url": item, "kind": kind})

    artifacts: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for item in combined:
        if isinstance(item, str):
            url = clean_text(item)
            kind = infer_artifact_kind(url)
            filename = ""
        elif isinstance(item, dict):
            url = clean_text(item.get("url"))
            kind = clean_text(item.get("kind")) or infer_artifact_kind(url)
            filename = clean_text(item.get("filename"))
        else:
            continue

        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        artifacts.append({"url": url, "kind": kind or "other", "filename": filename})

    return artifacts


def bootstrap_target(
    *,
    target: dict[str, Any],
    raw_input: dict[str, Any],
    repo_root: Path,
    targets_dir: str,
    force: bool,
    skip_clone: bool,
    skip_downloads: bool,
) -> dict[str, Any]:
    target_root = repo_root / targets_dir / target["slug"]
    ensure_inside_root(repo_root, target_root)
    prepare_target_root(target_root, force=force)

    scope_dir = target_root / "scope"
    prep_dir = target_root / "prep"
    repos_dir = target_root / "source" / "repos"
    artifacts_dir = target_root / "source" / "artifacts"
    for directory in (scope_dir, prep_dir, repos_dir, artifacts_dir):
        directory.mkdir(parents=True, exist_ok=True)

    repo_results = clone_repositories(
        target["repo_urls"], repos_dir, repo_root=repo_root, skip_clone=skip_clone
    )
    artifact_results = download_artifacts(
        target["artifacts"], artifacts_dir, repo_root=repo_root, skip_downloads=skip_downloads
    )
    suggested_lane, lane_reason = suggest_lane(target["target_type"], repo_results, repo_root=repo_root)

    target_record = dict(target)
    target_record["repo_results"] = repo_results
    target_record["artifact_results"] = artifact_results
    target_record["suggested_lane"] = suggested_lane
    target_record["suggested_lane_reason"] = lane_reason

    write_json(scope_dir / "input.json", raw_input)
    write_json(scope_dir / "target.json", target_record)
    write_text(scope_dir / "raw-scope-notes.md", render_raw_notes(target))
    write_text(scope_dir / "summary.md", render_scope_summary(target, repo_results, artifact_results))
    write_text(scope_dir / "in-scope.md", render_scope_bucket("In Scope", target["in_scope"]))
    write_text(scope_dir / "out-of-scope.md", render_scope_bucket("Out Of Scope", target["out_of_scope"]))
    write_text(scope_dir / "rules.md", render_scope_bucket("Rules", target["rules"]))
    write_text(scope_dir / "program-notes.md", render_program_notes(target))
    write_text(prep_dir / "asset-inventory.md", render_inventory(target, repo_results, artifact_results))
    write_text(prep_dir / "ready-for-bounty.md", render_ready_for_bounty(target, suggested_lane, lane_reason))
    write_text(target_root / "README.md", render_target_readme(target, suggested_lane))

    failures = [
        item
        for item in [*repo_results, *artifact_results]
        if item["status"] == "error"
    ]
    if failures:
        print(
            f"warning: bootstrap completed with {len(failures)} failed network action(s)",
            file=sys.stderr,
        )

    return {
        "target_root": relative_path(target_root, repo_root),
        "scope_file": relative_path(scope_dir / "target.json", repo_root),
        "ready_file": relative_path(prep_dir / "ready-for-bounty.md", repo_root),
        "suggested_lane": suggested_lane,
        "repo_results": repo_results,
        "artifact_results": artifact_results,
    }


def clone_repositories(
    repo_urls: list[str], repos_dir: Path, *, repo_root: Path, skip_clone: bool
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for index, repo_url in enumerate(repo_urls, start=1):
        folder_name = destination_name(repo_url, index=index, fallback_prefix="repo")
        destination = ensure_unique_destination(repos_dir / folder_name)
        result = {
            "url": repo_url,
            "status": "skipped" if skip_clone else "pending",
            "local_path": relative_path(destination, repo_root),
            "note": "",
        }
        if skip_clone:
            result["note"] = "clone skipped by flag"
            results.append(result)
            continue

        clone_source = resolve_local_source(repo_url)
        command = ["git", "clone", str(clone_source) if clone_source else repo_url, str(destination)]
        if clone_source is None:
            command = ["git", "clone", "--depth", "1", repo_url, str(destination)]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            result["status"] = "cloned"
        except subprocess.CalledProcessError as exc:
            result["status"] = "error"
            result["note"] = exc.stderr.strip() or exc.stdout.strip() or "git clone failed"
        results.append(result)
    return results


def download_artifacts(
    artifacts: list[dict[str, str]], artifacts_dir: Path, *, repo_root: Path, skip_downloads: bool
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for index, artifact in enumerate(artifacts, start=1):
        base_name = artifact["filename"] or destination_name(
            artifact["url"], index=index, fallback_prefix=artifact["kind"] or "artifact"
        )
        destination = ensure_unique_destination(artifacts_dir / base_name)
        result = {
            "url": artifact["url"],
            "kind": artifact["kind"],
            "status": "skipped" if skip_downloads else "pending",
            "local_path": relative_path(destination, repo_root),
            "note": "",
        }
        if skip_downloads:
            result["note"] = "download skipped by flag"
            results.append(result)
            continue

        try:
            copy_url_to_path(artifact["url"], destination)
            result["status"] = "downloaded"
        except Exception as exc:  # pragma: no cover - exercised via subprocess tests
            result["status"] = "error"
            result["note"] = str(exc)
        results.append(result)
    return results


def suggest_lane(
    target_type: str, repo_results: list[dict[str, str]], *, repo_root: Path
) -> tuple[str, str]:
    if target_type == "android":
        return "bounty-program-mobile-android", "explicit android target type from scope page"

    available_paths = [
        Path(item["local_path"])
        for item in repo_results
        if item["status"] == "cloned" and item["local_path"]
    ]
    markers = collect_markers(available_paths, repo_root=repo_root)
    if "android" in markers:
        return "bounty-program-mobile-android", "android build markers detected in cloned source"
    if "smart-contract" in markers:
        return "bounty-program-smart-contracts", "smart contract build markers detected in cloned source"
    if "web" in markers:
        return "bounty-program-web", "web or API application markers detected in cloned source"
    if "native" in markers:
        return "bounty-program-native", "native build markers detected in cloned source"
    if available_paths:
        return "bounty-program-triage", "source cloned but stack fingerprint stayed inconclusive"
    return "bounty-program-triage", "whitebox scope provided no cloned source to fingerprint"


def collect_markers(repo_paths: list[Path], *, repo_root: Path) -> set[str]:
    markers: set[str] = set()
    for repo_path in repo_paths:
        root = repo_root / repo_path
        if not root.exists():
            continue
        for candidate in iter_relative_names(root):
            if candidate in ANDROID_MARKERS:
                markers.add("android")
            if candidate in SMART_CONTRACT_MARKERS:
                markers.add("smart-contract")
            if candidate in WEB_MARKERS:
                markers.add("web")
            if candidate in NATIVE_MARKERS:
                markers.add("native")
    return markers


def iter_relative_names(root: Path, *, max_depth: int = 4, limit: int = 4000) -> list[str]:
    names: list[str] = []
    stack: list[tuple[Path, int]] = [(root, 0)]
    while stack and len(names) < limit:
        current, depth = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            names.append(entry.name.lower())
            if entry.is_dir() and depth < max_depth:
                stack.append((entry, depth + 1))
            if len(names) >= limit:
                break
    return names


def render_raw_notes(target: dict[str, Any]) -> str:
    if target["raw_scope_notes"]:
        body = target["raw_scope_notes"]
    else:
        body = "No raw Playwright notes were provided. Re-run scope capture if fidelity matters."
    return f"# Raw Scope Notes\n\n{body}\n"


def render_scope_summary(
    target: dict[str, Any], repo_results: list[dict[str, str]], artifact_results: list[dict[str, str]]
) -> str:
    lines = [
        "# Scope Summary",
        "",
        f"- Program: {target['program_name']}",
        f"- URL: {target['program_url']}",
        f"- Target Type: {target['target_type']}",
        f"- Scope Summary: {target['scope_summary'] or 'Not captured'}",
        "",
        "## In Scope",
    ]
    lines.extend(render_list(target["in_scope"]))
    lines.extend(["", "## Out Of Scope"])
    lines.extend(render_list(target["out_of_scope"]))
    lines.extend(["", "## Rules"])
    lines.extend(render_list(target["rules"]))
    lines.extend(["", "## Safe Harbor"])
    lines.extend(render_list(target["safe_harbor"]))
    lines.extend(["", "## Submission Guidelines"])
    lines.extend(render_list(target["submission_guidelines"]))
    lines.extend(["", "## Program Notes"])
    lines.extend(render_list(target["program_notes"]))
    lines.extend(["", "## Auth Notes"])
    lines.extend(render_list(target["auth_notes"]))
    lines.extend(["", "## Environment Notes"])
    lines.extend(render_list(target["environment_notes"]))
    lines.extend(["", "## Source Repositories"])
    lines.extend(render_status_list(repo_results))
    lines.extend(["", "## Artifacts"])
    lines.extend(render_status_list(artifact_results, include_kind=True))
    return "\n".join(lines).rstrip() + "\n"


def render_inventory(
    target: dict[str, Any], repo_results: list[dict[str, str]], artifact_results: list[dict[str, str]]
) -> str:
    lines = [
        "# Asset Inventory",
        "",
        f"- Program: {target['program_name']}",
        f"- Target Type: {target['target_type']}",
        "",
        "## In Scope",
    ]
    lines.extend(render_list(target["in_scope"]))
    lines.extend(["", "## Out Of Scope"])
    lines.extend(render_list(target["out_of_scope"]))
    lines.extend(["", "## Rules"])
    lines.extend(render_list(target["rules"]))
    lines.extend(["", "## Repo URLs"])
    lines.extend(render_status_list(repo_results))
    lines.extend(["", "## Artifact URLs"])
    lines.extend(render_status_list(artifact_results, include_kind=True))
    lines.extend(["", "## Package Names"])
    lines.extend(render_list(target["package_names"]))
    lines.extend(["", "## App URLs"])
    lines.extend(render_list(target["app_urls"]))
    lines.extend(["", "## Program Notes"])
    lines.extend(render_list(target["program_notes"]))
    lines.extend(["", "## Safe Harbor"])
    lines.extend(render_list(target["safe_harbor"]))
    lines.extend(["", "## Submission Guidelines"])
    lines.extend(render_list(target["submission_guidelines"]))
    return "\n".join(lines).rstrip() + "\n"


def render_scope_bucket(title: str, items: list[str]) -> str:
    lines = [f"# {title}", ""]
    lines.extend(render_list(items))
    return "\n".join(lines).rstrip() + "\n"


def render_program_notes(target: dict[str, Any]) -> str:
    lines = [
        "# Program Notes",
        "",
        "## Safe Harbor",
    ]
    lines.extend(render_list(target["safe_harbor"]))
    lines.extend(["", "## Submission Guidelines"])
    lines.extend(render_list(target["submission_guidelines"]))
    lines.extend(["", "## Auth Notes"])
    lines.extend(render_list(target["auth_notes"]))
    lines.extend(["", "## Environment Notes"])
    lines.extend(render_list(target["environment_notes"]))
    lines.extend(["", "## Extra Program Notes"])
    lines.extend(render_list(target["program_notes"]))
    return "\n".join(lines).rstrip() + "\n"


def render_ready_for_bounty(target: dict[str, Any], suggested_lane: str, lane_reason: str) -> str:
    lines = [
        "# Ready For Bounty",
        "",
        f"- Suggested Lane: `{suggested_lane}`",
        f"- Reason: {lane_reason}",
        "",
        "## Next Step",
    ]
    if suggested_lane == "bounty-program-mobile-android":
        lines.extend(
            [
                "- Activate `bounty-program-mobile-android`.",
                "- Use the downloaded APKs and package names from `scope/target.json`.",
            ]
        )
    else:
        lines.extend(
            [
                f"- Activate `{suggested_lane}` if the fingerprint is already clear.",
                "- If confidence is low, start with `bounty-program-triage` on the cloned source tree.",
            ]
        )
    lines.extend(
        [
            "",
            "## Always Check",
            "- `scope/target.json` for the normalized contract",
            "- `scope/in-scope.md`, `scope/out-of-scope.md`, and `scope/rules.md` for persisted scope buckets",
            "- `scope/raw-scope-notes.md` for exact copied scope text",
            "- `prep/asset-inventory.md` for local paths and download or clone status",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_target_readme(target: dict[str, Any], suggested_lane: str) -> str:
    lines = [
        f"# {target['program_name']}",
        "",
        f"- Target Type: {target['target_type']}",
        f"- Program URL: {target['program_url']}",
        f"- Suggested Lane: `{suggested_lane}`",
        "",
        "See `scope/target.json` for the machine-readable contract, `scope/summary.md` for the full scope digest, and `prep/ready-for-bounty.md` for the handoff.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_list(items: list[str]) -> list[str]:
    if not items:
        return ["- None recorded"]
    return [f"- {item}" for item in items]


def render_status_list(items: list[dict[str, str]], *, include_kind: bool = False) -> list[str]:
    if not items:
        return ["- None recorded"]
    rendered = []
    for item in items:
        prefix = f"[{item['status']}] {item['url']}"
        if include_kind:
            prefix = f"[{item['status']}] ({item.get('kind', 'other')}) {item['url']}"
        details = f" -> {item['local_path']}"
        if item.get("note"):
            details += f" ({item['note']})"
        rendered.append(f"- {prefix}{details}")
    return rendered


def prepare_target_root(target_root: Path, *, force: bool) -> None:
    if target_root.exists():
        if not force:
            raise ValueError(f"Target already exists: {target_root}. Re-run with --force to replace it.")
        shutil.rmtree(target_root)
    target_root.mkdir(parents=True, exist_ok=True)


def ensure_inside_root(repo_root: Path, target_path: Path) -> None:
    resolved_root = repo_root.resolve()
    resolved_target = target_path.resolve()
    if not resolved_target.is_relative_to(resolved_root):
        raise ValueError(f"Refusing to write outside repo root: {target_path}")


def copy_url_to_path(url: str, destination: Path) -> None:
    local_source = resolve_local_source(url)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if local_source is not None:
        shutil.copyfile(local_source, destination)
        return
    with urlopen(url) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def resolve_local_source(url: str) -> Path | None:
    path_candidate = Path(url)
    if path_candidate.exists():
        return path_candidate.resolve()

    parsed = urlparse(url)
    if parsed.scheme != "file":
        return None
    path_text = url2pathname(unquote(parsed.path))
    if parsed.netloc and not path_text.startswith("\\\\"):
        path_text = f"//{parsed.netloc}{path_text}"
    local_path = Path(path_text)
    return local_path.resolve()


def ensure_unique_destination(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def destination_name(value: str, *, index: int, fallback_prefix: str) -> str:
    parsed = urlparse(value)
    candidate = ""
    if parsed.scheme and parsed.scheme != "file":
        candidate = Path(parsed.path).name
    else:
        local_path = resolve_local_source(value)
        if local_path is not None:
            candidate = local_path.name
        elif parsed.path:
            candidate = Path(parsed.path).name
    candidate = candidate or f"{fallback_prefix}-{index}"
    if candidate.endswith(".git"):
        candidate = candidate[:-4]
    if "." not in candidate and fallback_prefix != "repo":
        extension = suffix_for_kind(fallback_prefix)
        candidate = f"{candidate}{extension}"
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", candidate).strip("-")
    return cleaned or f"{fallback_prefix}-{index}"


def suffix_for_kind(kind: str) -> str:
    if kind == "apk":
        return ".apk"
    if kind == "source-archive":
        return ".zip"
    return ".bin"


def infer_artifact_kind(url: str) -> str:
    lowered = url.lower()
    if lowered.endswith(APK_SUFFIXES):
        return "apk"
    if lowered.endswith(ARCHIVE_SUFFIXES):
        return "source-archive"
    return "other"


def slugify(value: str) -> str:
    lowered = value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "target"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def unique_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        text = clean_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output


def relative_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
