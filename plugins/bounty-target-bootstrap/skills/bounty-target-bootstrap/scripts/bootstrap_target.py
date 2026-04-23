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

SUPPORTED_TARGET_TYPES = {"whitebox", "android", "smart-contract"}
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
FOCUS_AREA_ALIASES = {
    "wallet": "Wallet",
    "wallets": "Wallet",
    "wallet extension": "Wallet",
    "browser extension": "Wallet",
    "smart contract": "Smart Contract",
    "smart-contract": "Smart Contract",
    "smart contracts": "Smart Contract",
    "contracts": "Smart Contract",
    "blockchain": "Blockchain",
    "blockchains": "Blockchain",
    "web3": "Web3",
    "exchange": "Exchange",
    "exchanges": "Exchange",
    "dex": "Exchange",
    "cex": "Exchange",
}
LANE_SIGNAL_TO_LANE = {
    "android": "bounty-program-mobile-android",
    "native": "bounty-program-native",
    "smart-contract": "bounty-program-smart-contracts",
    "web": "bounty-program-web",
}
BUG_CLASS_PRIORITIES = {
    "bounty-program-web": [
        (
            "authorization and IDOR boundary failures",
            "web and API targets commonly break on server-side object ownership or role checks",
        ),
        (
            "server-trust bugs in internal fetch, SSRF, or admin workflow paths",
            "backend services and background jobs often trust user-controlled URLs, hosts, or async state too much",
        ),
        (
            "state-machine and privilege transition flaws",
            "multi-step web flows frequently expose escalation or replay edges between user, admin, and worker roles",
        ),
    ],
    "bounty-program-mobile-android": [
        (
            "mobile-client trust abuse against backend APIs",
            "developers cannot safely trust the APK or rooted device as an authority boundary",
        ),
        (
            "secret, token, or local storage exposure",
            "mobile bundles and local storage often leak material that enables deeper backend or account attacks",
        ),
        (
            "crypto, transport, or SSL-pinning bypass paths",
            "Android apps frequently fail around local trust stores, custom crypto wrappers, or transport assumptions",
        ),
    ],
    "bounty-program-smart-contracts": [
        (
            "privileged entry point and access-control failures",
            "smart contracts fail hard when privileged functions, upgrade hooks, or role checks are wrong",
        ),
        (
            "accounting and invariant violations",
            "value-bearing logic often breaks through conservation, rounding, or state-transition mistakes",
        ),
        (
            "integration and callback trust failures",
            "token hooks, oracle inputs, bridges, and cross-contract callbacks frequently violate assumed trust boundaries",
        ),
    ],
    "bounty-program-native": [
        (
            "memory corruption and parser confusion",
            "native targets often fail at length checks, ownership, and unsafe parsing edges",
        ),
        (
            "filesystem, path, or command trust violations",
            "CLI tools and daemons commonly trust paths, archives, or environment-derived execution context",
        ),
        (
            "crypto and side-channel implementation flaws",
            "native and protocol-heavy code can leak via timing, nonce misuse, or unsafe custom primitives",
        ),
    ],
    "bounty-program-triage": [
        (
            "cross-surface authorization mismatches",
            "hybrid targets often break where web, mobile, backend, and on-chain components disagree on authority",
        ),
        (
            "workflow and synchronization flaws across surfaces",
            "mixed deployments often leak exploitable state between clients, workers, and contracts",
        ),
        (
            "CI, supply-chain, or release-path trust abuse",
            "multi-surface programs frequently widen attack surface through build, dependency, or automation systems",
        ),
    ],
}


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

    smart_contracts = normalize_smart_contracts(raw)
    repo_urls = unique_text_list(
        flatten_values(
            raw.get("repo_urls"),
            raw.get("source_repos"),
            [contract.get("repo_url") for contract in smart_contracts],
        )
    )
    source_code_urls = unique_text_list(
        flatten_values(
            raw.get("source_code_urls"),
            raw.get("source_urls"),
            raw.get("source_links"),
            [contract.get("source_url") for contract in smart_contracts],
        )
    )
    explorer_urls = unique_text_list(
        flatten_values(
            raw.get("explorer_urls"),
            raw.get("block_explorer_urls"),
            [contract.get("explorer_url") for contract in smart_contracts],
        )
    )
    artifacts = normalize_artifacts(raw, smart_contracts=smart_contracts)

    return {
        "program_name": program_name,
        "program_url": program_url,
        "target_type": target_type,
        "focus_areas": normalize_focus_areas(raw.get("focus_areas"), target_type),
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
        "repo_urls": repo_urls,
        "source_code_urls": source_code_urls,
        "package_names": unique_text_list(raw.get("package_names")),
        "app_urls": unique_text_list(raw.get("app_urls") or raw.get("store_urls")),
        "web_urls": unique_text_list(raw.get("web_urls") or raw.get("web_app_urls") or raw.get("portal_urls")),
        "api_urls": unique_text_list(raw.get("api_urls") or raw.get("api_base_urls") or raw.get("base_urls")),
        "rpc_urls": unique_text_list(raw.get("rpc_urls")),
        "ws_urls": unique_text_list(raw.get("ws_urls") or raw.get("websocket_urls")),
        "docs_urls": unique_text_list(
            raw.get("docs_urls") or raw.get("documentation_urls") or raw.get("reference_urls")
        ),
        "api_spec_urls": unique_text_list(
            raw.get("api_spec_urls")
            or raw.get("openapi_urls")
            or raw.get("swagger_urls")
            or raw.get("postman_urls")
        ),
        "audit_report_urls": unique_text_list(raw.get("audit_report_urls") or raw.get("audit_urls")),
        "registry_urls": unique_text_list(
            raw.get("registry_urls") or raw.get("package_registry_urls") or raw.get("sdk_urls")
        ),
        "explorer_urls": explorer_urls,
        "smart_contracts": smart_contracts,
        "raw_scope_notes": clean_text(raw.get("raw_scope_notes")),
        "artifacts": artifacts,
    }


def normalize_artifacts(
    raw: dict[str, Any], *, smart_contracts: list[dict[str, str]] | None = None
) -> list[dict[str, str]]:
    combined: list[Any] = []
    for key in ("artifacts", "artifact_urls"):
        value = raw.get(key)
        if value is not None:
            combined.extend(value if isinstance(value, list) else [value])

    for key, kind in (
        ("apk_urls", "apk"),
        ("source_archive_urls", "source-archive"),
        ("abi_urls", "abi"),
        ("audit_report_urls", "audit-report"),
        ("api_spec_urls", "api-spec"),
    ):
        value = raw.get(key)
        for item in value if isinstance(value, list) else ([value] if value else []):
            combined.append({"url": item, "kind": kind})

    for contract in smart_contracts or []:
        abi_url = clean_text(contract.get("abi_url"))
        if abi_url:
            combined.append({"url": abi_url, "kind": "abi"})

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


def normalize_smart_contracts(raw: dict[str, Any]) -> list[dict[str, str]]:
    contracts = raw.get("smart_contracts") or raw.get("contracts") or raw.get("deployed_contracts")
    if contracts is None:
        return []

    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in contracts if isinstance(contracts, list) else [contracts]:
        if isinstance(item, str):
            text = clean_text(item)
            if not text:
                continue
            contract = {
                "name": "",
                "kind": "",
                "chain": "",
                "chain_id": "",
                "network": "",
                "vm": "",
                "address": "" if text.startswith(("http://", "https://")) else text,
                "proxy_address": "",
                "implementation_address": "",
                "explorer_url": text if text.startswith(("http://", "https://")) else "",
                "abi_url": "",
                "source_url": "",
                "repo_url": "",
                "language": "",
                "notes": "",
            }
        elif isinstance(item, dict):
            contract = {
                "name": clean_text(item.get("name")),
                "kind": clean_text(item.get("kind")),
                "chain": clean_text(item.get("chain")),
                "chain_id": clean_text(item.get("chain_id")),
                "network": clean_text(item.get("network")),
                "vm": clean_text(item.get("vm") or item.get("platform")),
                "address": clean_text(item.get("address") or item.get("contract_address")),
                "proxy_address": clean_text(item.get("proxy_address")),
                "implementation_address": clean_text(item.get("implementation_address")),
                "explorer_url": clean_text(item.get("explorer_url") or item.get("explorer")),
                "abi_url": clean_text(item.get("abi_url")),
                "source_url": clean_text(item.get("source_url") or item.get("source_code_url")),
                "repo_url": clean_text(item.get("repo_url")),
                "language": clean_text(item.get("language")),
                "notes": clean_text(item.get("notes")),
            }
        else:
            continue

        if not any(contract.values()):
            continue
        marker = json.dumps(contract, sort_keys=True)
        if marker in seen:
            continue
        seen.add(marker)
        normalized.append(contract)
    return normalized


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
    context_pack_dir = prep_dir / "context-pack"
    findings_dir = target_root / "findings"
    repos_dir = target_root / "source" / "repos"
    artifacts_dir = target_root / "source" / "artifacts"
    for directory in (scope_dir, prep_dir, context_pack_dir, findings_dir, repos_dir, artifacts_dir):
        directory.mkdir(parents=True, exist_ok=True)

    repo_results = clone_repositories(
        target["repo_urls"], repos_dir, repo_root=repo_root, skip_clone=skip_clone
    )
    artifact_results = download_artifacts(
        target["artifacts"], artifacts_dir, repo_root=repo_root, skip_downloads=skip_downloads
    )
    suggested_lane, lane_reason, surface_signals, follow_on_lanes = suggest_lane(
        target, repo_results, repo_root=repo_root
    )

    target_record = dict(target)
    target_record["repo_results"] = repo_results
    target_record["artifact_results"] = artifact_results
    target_record["suggested_lane"] = suggested_lane
    target_record["suggested_lane_reason"] = lane_reason
    target_record["surface_signals"] = surface_signals
    target_record["follow_on_lanes"] = follow_on_lanes
    trust_boundaries = describe_trust_boundaries(target_record, suggested_lane, surface_signals)
    prioritized_bug_classes = prioritize_bug_classes(suggested_lane)
    top_assets = collect_top_assets(target_record, repo_results, artifact_results)
    next_attack_path = recommend_next_attack_path(
        suggested_lane=suggested_lane,
        follow_on_lanes=follow_on_lanes,
        top_assets=top_assets,
    )
    target_record["trust_boundaries"] = trust_boundaries
    target_record["prioritized_bug_classes"] = prioritized_bug_classes
    target_record["next_attack_path"] = next_attack_path

    write_json(scope_dir / "input.json", raw_input)
    write_json(scope_dir / "target.json", target_record)
    write_text(scope_dir / "raw-scope-notes.md", render_raw_notes(target_record))
    write_text(scope_dir / "summary.md", render_scope_summary(target_record, repo_results, artifact_results))
    write_text(scope_dir / "in-scope.md", render_scope_bucket("In Scope", target["in_scope"]))
    write_text(scope_dir / "out-of-scope.md", render_scope_bucket("Out Of Scope", target["out_of_scope"]))
    write_text(scope_dir / "rules.md", render_scope_bucket("Rules", target["rules"]))
    write_text(scope_dir / "program-notes.md", render_program_notes(target_record))
    write_text(scope_dir / "target-surface.md", render_target_surface(target_record, repo_results, artifact_results))
    write_text(scope_dir / "smart-contracts.md", render_smart_contracts(target["smart_contracts"]))
    write_text(prep_dir / "asset-inventory.md", render_inventory(target_record, repo_results, artifact_results))
    write_text(prep_dir / "tried-and-ruled-out.md", render_tried_and_ruled_out())
    write_text(prep_dir / "finding-pipeline.md", render_finding_pipeline())
    write_text(
        prep_dir / "bootstrap-summary.md",
        render_bootstrap_summary(
            target_record,
            suggested_lane=suggested_lane,
            lane_reason=lane_reason,
            follow_on_lanes=follow_on_lanes,
            trust_boundaries=trust_boundaries,
            prioritized_bug_classes=prioritized_bug_classes,
            top_assets=top_assets,
            next_attack_path=next_attack_path,
        ),
    )
    write_context_pack(
        context_pack_dir,
        target_record,
        suggested_lane=suggested_lane,
        lane_reason=lane_reason,
        follow_on_lanes=follow_on_lanes,
        trust_boundaries=trust_boundaries,
        prioritized_bug_classes=prioritized_bug_classes,
        top_assets=top_assets,
        next_attack_path=next_attack_path,
    )
    write_text(findings_dir / "README.md", render_findings_readme())
    write_text(
        prep_dir / "ready-for-bounty.md",
        render_ready_for_bounty(target_record, suggested_lane, lane_reason, surface_signals, follow_on_lanes),
    )
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
        "bootstrap_summary_file": relative_path(prep_dir / "bootstrap-summary.md", repo_root),
        "context_pack_dir": relative_path(context_pack_dir, repo_root),
        "suggested_lane": suggested_lane,
        "surface_signals": surface_signals,
        "follow_on_lanes": follow_on_lanes,
        "prioritized_bug_classes": [item["name"] for item in prioritized_bug_classes],
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
    target: dict[str, Any], repo_results: list[dict[str, str]], *, repo_root: Path
) -> tuple[str, str, list[str], list[str]]:
    target_type = target["target_type"]
    if target_type == "android":
        return "bounty-program-mobile-android", "explicit android target type from scope page", ["android"], [
            "bounty-program-mobile-android"
        ]
    if target_type == "smart-contract":
        return "bounty-program-smart-contracts", "explicit smart-contract target type from scope page", [
            "smart-contract",
            *sorted(collect_context_signals(target)),
        ], ["bounty-program-smart-contracts"]

    available_paths = [
        Path(item["local_path"])
        for item in repo_results
        if item["status"] == "cloned" and item["local_path"]
    ]
    markers = collect_markers(available_paths, repo_root=repo_root)
    surface_signals = collect_surface_signals(target, markers)
    lane_signals = [signal for signal in surface_signals if signal in LANE_SIGNAL_TO_LANE]
    follow_on_lanes = unique_preserve_order([LANE_SIGNAL_TO_LANE[signal] for signal in lane_signals])

    if len(lane_signals) > 1:
        labels = ", ".join(lane_signals)
        return (
            "bounty-program-triage",
            f"target surface spans multiple executable lanes: {labels}",
            surface_signals,
            follow_on_lanes,
        )
    if "android" in surface_signals:
        return (
            "bounty-program-mobile-android",
            "android app signals detected from source or scope metadata",
            surface_signals,
            follow_on_lanes,
        )
    if "smart-contract" in surface_signals:
        return (
            "bounty-program-smart-contracts",
            "smart contract signals detected from source or scope metadata",
            surface_signals,
            follow_on_lanes,
        )
    if "web" in surface_signals:
        return ("bounty-program-web", "web or API signals detected from source or scope metadata", surface_signals, follow_on_lanes)
    if "native" in surface_signals:
        return ("bounty-program-native", "native build markers detected in cloned source", surface_signals, follow_on_lanes)
    if available_paths:
        return ("bounty-program-triage", "source cloned but stack fingerprint stayed inconclusive", surface_signals, follow_on_lanes)
    return (
        "bounty-program-triage",
        "scope capture produced metadata only; deeper fingerprinting still required",
        surface_signals,
        follow_on_lanes,
    )


def collect_surface_signals(target: dict[str, Any], repo_markers: set[str]) -> list[str]:
    signals = set(repo_markers)
    artifact_kinds = {artifact.get("kind", "") for artifact in target["artifacts"]}

    if target["package_names"]:
        signals.add("android")
    if target["smart_contracts"] or (
        "Smart Contract" in target["focus_areas"] and (target["explorer_urls"] or target["rpc_urls"] or artifact_kinds & {"abi"})
    ):
        signals.add("smart-contract")
    if target["web_urls"] or target["api_urls"] or target["ws_urls"]:
        signals.add("web")
    if target["rpc_urls"] or target["explorer_urls"] or "Blockchain" in target["focus_areas"] or "Web3" in target["focus_areas"]:
        signals.add("blockchain")
    signals.update(collect_context_signals(target))
    return sorted(signals)


def collect_context_signals(target: dict[str, Any]) -> set[str]:
    signals: set[str] = set()
    if "Wallet" in target["focus_areas"]:
        signals.add("wallet")
    if "Exchange" in target["focus_areas"]:
        signals.add("exchange")
    return signals


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


def describe_trust_boundaries(target: dict[str, Any], suggested_lane: str, surface_signals: list[str]) -> list[str]:
    boundaries = [
        "Host-provided scope and rules are trusted only as input constraints; runtime behavior must be verified before hunting conclusions.",
    ]
    if target["web_urls"] or target["api_urls"] or suggested_lane == "bounty-program-web":
        boundaries.append(
            "Browser or API clients are untrusted; authorization, object ownership, and server-side state changes must be enforced by the backend."
        )
    if target["package_names"] or suggested_lane == "bounty-program-mobile-android" or "android" in surface_signals:
        boundaries.append(
            "The mobile client, device storage, and APK logic are attacker-controlled; backend APIs must not trust app-side checks or embedded state."
        )
    if target["smart_contracts"] or suggested_lane == "bounty-program-smart-contracts" or "smart-contract" in surface_signals:
        boundaries.append(
            "On-chain contracts hold value or privilege; off-chain services, keepers, or users must cross explicit role and invariant checks."
        )
    if "native" in surface_signals or suggested_lane == "bounty-program-native":
        boundaries.append(
            "Native parsers, binaries, and protocol handlers trust external bytes only after length, ownership, and state validation."
        )
    if target["repo_urls"] or target["registry_urls"]:
        boundaries.append(
            "Dependency and release automation can cross the source-to-runtime boundary; CI, package, and agent workflows should stay in scope when present."
        )
    return boundaries


def prioritize_bug_classes(suggested_lane: str) -> list[dict[str, str]]:
    candidates = BUG_CLASS_PRIORITIES.get(suggested_lane, BUG_CLASS_PRIORITIES["bounty-program-triage"])
    return [{"name": name, "reason": reason} for name, reason in candidates[:3]]


def collect_top_assets(
    target: dict[str, Any], repo_results: list[dict[str, str]], artifact_results: list[dict[str, str]]
) -> list[str]:
    assets: list[str] = []
    for item in repo_results:
        if item.get("status") == "cloned":
            assets.append(item["local_path"])
    for item in artifact_results:
        if item.get("status") == "downloaded":
            assets.append(item["local_path"])
    assets.extend(target["api_urls"][:3])
    assets.extend(target["web_urls"][:3])
    assets.extend(target["package_names"][:3])
    assets.extend(
        contract["address"] or contract["name"] or contract["explorer_url"]
        for contract in target["smart_contracts"][:3]
        if contract["address"] or contract["name"] or contract["explorer_url"]
    )
    return unique_preserve_order([asset for asset in assets if asset])


def recommend_next_attack_path(
    *, suggested_lane: str, follow_on_lanes: list[str], top_assets: list[str]
) -> str:
    lane = suggested_lane
    if lane == "bounty-program-triage" and follow_on_lanes:
        lane = follow_on_lanes[0]

    asset_hint = top_assets[0] if top_assets else "the normalized target workspace"
    if lane == "bounty-program-web":
        return f"Start `bounty-program-web` from {asset_hint}; map auth middleware, routes, and object-authorization checks first."
    if lane == "bounty-program-mobile-android":
        return f"Start `bounty-program-mobile-android` from {asset_hint}; inspect manifest, network config, local storage, and backend API trust."
    if lane == "bounty-program-smart-contracts":
        return f"Start `bounty-program-smart-contracts` from {asset_hint}; enumerate privileged entry points and value-moving invariants first."
    if lane == "bounty-program-native":
        return f"Start `bounty-program-native` from {asset_hint}; identify parsers, external byte boundaries, and fuzzable harness targets first."
    return f"Start `bounty-program-triage` from {asset_hint}; resolve the first executable lane before exploit work."


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
        f"- Focus Areas: {', '.join(target['focus_areas']) if target['focus_areas'] else 'Not captured'}",
        f"- Scope Summary: {target['scope_summary'] or 'Not captured'}",
        "",
        "## Surface Signals",
    ]
    lines.extend(render_list(target.get("surface_signals", [])))
    lines.extend(["", "## Follow-On Lanes"])
    lines.extend(render_list(target.get("follow_on_lanes", [])))
    lines.extend([
        "",
        "## In Scope",
    ])
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
    lines.extend(["", "## Target Surface"])
    lines.extend(render_target_surface_items(target))
    lines.extend(["", "## Smart Contracts"])
    lines.extend(render_contract_list(target["smart_contracts"]))
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
        f"- Focus Areas: {', '.join(target['focus_areas']) if target['focus_areas'] else 'None recorded'}",
        "",
        "## Surface Signals",
    ]
    lines.extend(render_list(target.get("surface_signals", [])))
    lines.extend(["", "## Follow-On Lanes"])
    lines.extend(render_list(target.get("follow_on_lanes", [])))
    lines.extend([
        "",
        "## In Scope",
    ])
    lines.extend(render_list(target["in_scope"]))
    lines.extend(["", "## Out Of Scope"])
    lines.extend(render_list(target["out_of_scope"]))
    lines.extend(["", "## Rules"])
    lines.extend(render_list(target["rules"]))
    lines.extend(["", "## Repo URLs"])
    lines.extend(render_status_list(repo_results))
    lines.extend(["", "## Artifact URLs"])
    lines.extend(render_status_list(artifact_results, include_kind=True))
    lines.extend(["", "## Source Code URLs"])
    lines.extend(render_list(target["source_code_urls"]))
    lines.extend(["", "## Package Names"])
    lines.extend(render_list(target["package_names"]))
    lines.extend(["", "## App URLs"])
    lines.extend(render_list(target["app_urls"]))
    lines.extend(["", "## Web URLs"])
    lines.extend(render_list(target["web_urls"]))
    lines.extend(["", "## API URLs"])
    lines.extend(render_list(target["api_urls"]))
    lines.extend(["", "## RPC URLs"])
    lines.extend(render_list(target["rpc_urls"]))
    lines.extend(["", "## WebSocket URLs"])
    lines.extend(render_list(target["ws_urls"]))
    lines.extend(["", "## Documentation URLs"])
    lines.extend(render_list(target["docs_urls"]))
    lines.extend(["", "## API Specification URLs"])
    lines.extend(render_list(target["api_spec_urls"]))
    lines.extend(["", "## Explorer URLs"])
    lines.extend(render_list(target["explorer_urls"]))
    lines.extend(["", "## Audit Report URLs"])
    lines.extend(render_list(target["audit_report_urls"]))
    lines.extend(["", "## Registry URLs"])
    lines.extend(render_list(target["registry_urls"]))
    lines.extend(["", "## Smart Contracts"])
    lines.extend(render_contract_list(target["smart_contracts"]))
    lines.extend(["", "## Program Notes"])
    lines.extend(render_list(target["program_notes"]))
    lines.extend(["", "## Safe Harbor"])
    lines.extend(render_list(target["safe_harbor"]))
    lines.extend(["", "## Submission Guidelines"])
    lines.extend(render_list(target["submission_guidelines"]))
    return "\n".join(lines).rstrip() + "\n"


def render_bootstrap_summary(
    target: dict[str, Any],
    *,
    suggested_lane: str,
    lane_reason: str,
    follow_on_lanes: list[str],
    trust_boundaries: list[str],
    prioritized_bug_classes: list[dict[str, str]],
    top_assets: list[str],
    next_attack_path: str,
) -> str:
    lines = [
        "# Bootstrap Summary",
        "",
        f"- Program: {target['program_name']}",
        f"- Program URL: {target['program_url']}",
        f"- Primary Lane: `{suggested_lane}`",
        f"- Lane Reason: {lane_reason}",
        f"- Follow-On Lanes: {', '.join(follow_on_lanes) if follow_on_lanes else 'None recorded'}",
        "",
        "## Active Constraints",
    ]
    lines.extend(render_constraints_list(target))
    lines.extend(["", "## Trust Boundaries"])
    lines.extend(render_list(trust_boundaries))
    lines.extend(["", "## First 3 Prioritized Bug Classes"])
    lines.extend(render_bug_class_list(prioritized_bug_classes))
    lines.extend(["", "## Auth And Test State"])
    auth_state = target["auth_notes"] + target["environment_notes"]
    lines.extend(render_list(auth_state))
    lines.extend(["", "## Top Assets"])
    lines.extend(render_list(top_assets))
    lines.extend(["", "## Next Best Attack Path", f"- {next_attack_path}"])
    return "\n".join(lines).rstrip() + "\n"


def write_context_pack(
    context_pack_dir: Path,
    target: dict[str, Any],
    *,
    suggested_lane: str,
    lane_reason: str,
    follow_on_lanes: list[str],
    trust_boundaries: list[str],
    prioritized_bug_classes: list[dict[str, str]],
    top_assets: list[str],
    next_attack_path: str,
) -> None:
    write_text(context_pack_dir / "README.md", render_context_pack_readme())
    write_text(context_pack_dir / "trust-boundaries.md", render_context_trust_boundaries(trust_boundaries))
    write_text(
        context_pack_dir / "lane-decision.md",
        render_context_lane_decision(
            suggested_lane=suggested_lane,
            lane_reason=lane_reason,
            follow_on_lanes=follow_on_lanes,
            prioritized_bug_classes=prioritized_bug_classes,
            next_attack_path=next_attack_path,
        ),
    )
    write_text(context_pack_dir / "asset-pointers.md", render_context_asset_pointers(target, top_assets))


def render_context_pack_readme() -> str:
    return (
        "# Context Pack\n\n"
        "This directory holds bootstrap-only summaries so the hunting pipeline can resume without rebuilding triage context.\n\n"
        "- `trust-boundaries.md` - bootstrap trust-boundary summary\n"
        "- `lane-decision.md` - primary lane, follow-on lanes, bug-class priorities, and next attack path\n"
        "- `asset-pointers.md` - top asset references collected during bootstrap\n"
    )


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


def render_context_trust_boundaries(trust_boundaries: list[str]) -> str:
    lines = ["# Trust Boundaries", ""]
    lines.extend(render_list(trust_boundaries))
    return "\n".join(lines).rstrip() + "\n"


def render_context_lane_decision(
    *,
    suggested_lane: str,
    lane_reason: str,
    follow_on_lanes: list[str],
    prioritized_bug_classes: list[dict[str, str]],
    next_attack_path: str,
) -> str:
    lines = [
        "# Lane Decision",
        "",
        f"- Primary Lane: `{suggested_lane}`",
        f"- Reason: {lane_reason}",
        f"- Follow-On Lanes: {', '.join(follow_on_lanes) if follow_on_lanes else 'None recorded'}",
        "",
        "## Prioritized Bug Classes",
    ]
    lines.extend(render_bug_class_list(prioritized_bug_classes))
    lines.extend(["", "## Next Best Attack Path", f"- {next_attack_path}"])
    return "\n".join(lines).rstrip() + "\n"


def render_context_asset_pointers(target: dict[str, Any], top_assets: list[str]) -> str:
    lines = ["# Asset Pointers", "", "## Top Assets"]
    lines.extend(render_list(top_assets))
    lines.extend(["", "## Source Pointers"])
    lines.extend(render_target_surface_items(target))
    return "\n".join(lines).rstrip() + "\n"


def render_target_surface(
    target: dict[str, Any], repo_results: list[dict[str, str]], artifact_results: list[dict[str, str]]
) -> str:
    lines = [
        "# Target Surface",
        "",
        f"- Program: {target['program_name']}",
        f"- Target Type: {target['target_type']}",
        f"- Focus Areas: {', '.join(target['focus_areas']) if target['focus_areas'] else 'None recorded'}",
        "",
        "## Surface Signals",
    ]
    lines.extend(render_list(target.get("surface_signals", [])))
    lines.extend(["", "## Follow-On Lanes"])
    lines.extend(render_list(target.get("follow_on_lanes", [])))
    lines.extend([
        "",
        "## Host-Provided Assets",
    ])
    lines.extend(render_target_surface_items(target))
    lines.extend(["", "## Smart Contracts"])
    lines.extend(render_contract_list(target["smart_contracts"]))
    lines.extend(["", "## Local Clone Status"])
    lines.extend(render_status_list(repo_results))
    lines.extend(["", "## Local Artifact Status"])
    lines.extend(render_status_list(artifact_results, include_kind=True))
    return "\n".join(lines).rstrip() + "\n"


def render_target_surface_items(target: dict[str, Any]) -> list[str]:
    sections = [
        ("Repo URLs", target["repo_urls"]),
        ("Source Code URLs", target["source_code_urls"]),
        ("Package Names", target["package_names"]),
        ("App URLs", target["app_urls"]),
        ("Web URLs", target["web_urls"]),
        ("API URLs", target["api_urls"]),
        ("RPC URLs", target["rpc_urls"]),
        ("WebSocket URLs", target["ws_urls"]),
        ("Documentation URLs", target["docs_urls"]),
        ("API Specification URLs", target["api_spec_urls"]),
        ("Explorer URLs", target["explorer_urls"]),
        ("Audit Report URLs", target["audit_report_urls"]),
        ("Registry URLs", target["registry_urls"]),
    ]
    lines: list[str] = []
    for title, values in sections:
        lines.append(f"- {title}:")
        if values:
            lines.extend([f"  - {value}" for value in values])
        else:
            lines.append("  - None recorded")
    return lines


def render_smart_contracts(contracts: list[dict[str, str]]) -> str:
    lines = ["# Smart Contracts", ""]
    if not contracts:
        lines.append("- None recorded")
        return "\n".join(lines).rstrip() + "\n"

    for index, contract in enumerate(contracts, start=1):
        label = contract["name"] or contract["address"] or contract["explorer_url"] or f"Contract {index}"
        lines.extend(
            [
                f"## {label}",
                "",
                f"- Kind: {contract['kind'] or 'Not captured'}",
                f"- Chain: {contract['chain'] or 'Not captured'}",
                f"- Chain ID: {contract['chain_id'] or 'Not captured'}",
                f"- Network: {contract['network'] or 'Not captured'}",
                f"- VM: {contract['vm'] or 'Not captured'}",
                f"- Address: {contract['address'] or 'Not captured'}",
                f"- Proxy Address: {contract['proxy_address'] or 'Not captured'}",
                f"- Implementation Address: {contract['implementation_address'] or 'Not captured'}",
                f"- Explorer URL: {contract['explorer_url'] or 'Not captured'}",
                f"- ABI URL: {contract['abi_url'] or 'Not captured'}",
                f"- Source URL: {contract['source_url'] or 'Not captured'}",
                f"- Repo URL: {contract['repo_url'] or 'Not captured'}",
                f"- Language: {contract['language'] or 'Not captured'}",
                f"- Notes: {contract['notes'] or 'Not captured'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_contract_list(contracts: list[dict[str, str]]) -> list[str]:
    if not contracts:
        return ["- None recorded"]
    rendered = []
    for contract in contracts:
        parts = [
            contract["name"] or "Unnamed contract",
            f"chain={contract['chain']}" if contract["chain"] else "",
            f"network={contract['network']}" if contract["network"] else "",
            f"vm={contract['vm']}" if contract["vm"] else "",
            f"address={contract['address']}" if contract["address"] else "",
            f"explorer={contract['explorer_url']}" if contract["explorer_url"] else "",
        ]
        rendered.append("- " + " | ".join(part for part in parts if part))
    return rendered


def render_ready_for_bounty(
    target: dict[str, Any], suggested_lane: str, lane_reason: str, surface_signals: list[str], follow_on_lanes: list[str]
) -> str:
    lines = [
        "# Ready For Bounty",
        "",
        f"- Suggested Lane: `{suggested_lane}`",
        f"- Reason: {lane_reason}",
        f"- Surface Signals: {', '.join(surface_signals) if surface_signals else 'None recorded'}",
        f"- Follow-On Lanes: {', '.join(follow_on_lanes) if follow_on_lanes else 'None recorded'}",
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
    elif suggested_lane == "bounty-program-smart-contracts":
        lines.extend(
            [
                "- Activate `bounty-program-smart-contracts`.",
                "- Start from `scope/smart-contracts.md`, `scope/target-surface.md`, and any cloned repos or downloaded ABI files.",
            ]
        )
    elif suggested_lane == "bounty-program-triage":
        lines.extend(
            [
                "- Activate `bounty-program-triage` first because the host-provided target surface spans multiple lanes or remains incomplete.",
                "- Use `scope/target-surface.md` to decide whether the first deep pass belongs to web, mobile, smart contract, or native review.",
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
            "- `scope/target-surface.md` for host-provided target assets and references",
            "- `scope/smart-contracts.md` for deployed addresses and chain metadata",
            "- `prep/asset-inventory.md` for local paths and download or clone status",
            "- `prep/tried-and-ruled-out.md` to track attack paths that were tested and discarded",
            "- `prep/finding-pipeline.md` to track candidate, re-verify, and reporting status",
            "- `prep/bootstrap-summary.md` for trust boundaries, lane choice, bug-class priorities, and the next attack path",
            "- `prep/context-pack/` for the resumable hunting context pack",
            "- `findings/README.md` for the per-finding evidence bundle contract",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_target_readme(target: dict[str, Any], suggested_lane: str) -> str:
    lines = [
        f"# {target['program_name']}",
        "",
        f"- Target Type: {target['target_type']}",
        f"- Focus Areas: {', '.join(target['focus_areas']) if target['focus_areas'] else 'None recorded'}",
        f"- Program URL: {target['program_url']}",
        f"- Suggested Lane: `{suggested_lane}`",
        "",
        "See `scope/target.json` for the machine-readable contract, `scope/target-surface.md` for the host-provided asset map, `scope/smart-contracts.md` for deployed contract metadata, `scope/summary.md` for the full scope digest, `prep/bootstrap-summary.md` and `prep/context-pack/` for the hunting handoff, `prep/ready-for-bounty.md` for the suggested lane, and `findings/README.md` for the closed-loop finding bundle layout.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_tried_and_ruled_out() -> str:
    return (
        "# Tried And Ruled Out\n\n"
        "Track attack paths that were tested and ruled out so the engagement does not loop.\n\n"
        "## Entries\n\n"
        "- Path: \n"
        "  - Status: untested | ruled-out | revisit\n"
        "  - Why ruled out: \n"
        "  - Evidence: \n"
        "  - Revisit trigger: \n"
    )


def render_finding_pipeline() -> str:
    return (
        "# Finding Pipeline\n\n"
        "Use this file to track candidate findings from first hypothesis through independent re-verification and reporting.\n\n"
        "## Status Vocabulary\n\n"
        "- `untested` - hypothesis exists but no decisive path has been proved yet\n"
        "- `confirmed` - hunter reproduced the issue and has a runnable PoC\n"
        "- `reverify-pending` - packaged for independent re-verification but no verdict yet\n"
        "- `true-positive` - independent re-verification passed\n"
        "- `false-positive` - independent re-verification disproved the claim\n"
        "- `needs-more-evidence` - plausible claim but independent proof is incomplete\n"
        "- `report-ready` - true positive with `severity.md` and a complete evidence bundle ready for disclosure\n"
        "- `reported` - disclosure submitted or sent\n\n"
        "## Candidate Findings\n\n"
        "| ID | Surface | Hypothesis | Hunt Status | PoC Path | Evidence | Next Action |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"
        "| CAND-001 |  |  | untested |  |  |  |\n\n"
        "## Validated Findings\n\n"
        "| ID | Title | Severity | Bundle Path | Re-verify Verdict | Re-verify Evidence | Report Status |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"
    )


def render_findings_readme() -> str:
    return (
        "# Findings\n\n"
        "Create one directory per finding under this folder once a hypothesis becomes a real candidate for reporting.\n\n"
        "Recommended layout:\n\n"
        "- `findings/<finding-id>/claim.md` - one falsifiable security claim\n"
        "- `findings/<finding-id>/facts.md` - observed facts only\n"
        "- `findings/<finding-id>/poc.md` - replayable exploit or reproduction path\n"
        "- `findings/<finding-id>/impact.md` - observed impact and inferred blast radius kept separate\n"
        "- `findings/<finding-id>/reverify.md` - independent re-verification verdict and failed disproof attempts\n"
        "- `findings/<finding-id>/severity.md` - severity level, CWE, CVSS when applicable, affected asset, preconditions, impact reasoning, and downgrade notes\n"
        "- `findings/<finding-id>/artifacts/` - scripts, payloads, traces, screenshots, logs, or tx data\n\n"
        "Lifecycle:\n\n"
        "1. Move the finding from `untested` to `confirmed` only after a runnable PoC exists.\n"
        "2. Create the bundle and move the finding to `reverify-pending`.\n"
        "3. Run `security-finding-reverify` and record `true-positive`, `false-positive`, or `needs-more-evidence`.\n"
        "4. For each `true-positive`, write `severity.md` before the finding becomes `report-ready` and feeds the report submitter.\n"
    )


def render_list(items: list[str]) -> list[str]:
    if not items:
        return ["- None recorded"]
    return [f"- {item}" for item in items]


def render_constraints_list(target: dict[str, Any]) -> list[str]:
    constraints = (
        target["rules"]
        + target["safe_harbor"]
        + target["submission_guidelines"]
        + target["auth_notes"]
        + target["environment_notes"]
    )
    return render_list(unique_preserve_order(constraints))


def render_bug_class_list(items: list[dict[str, str]]) -> list[str]:
    if not items:
        return ["- None recorded"]
    return [f"- {item['name']}: {item['reason']}" for item in items]


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
    if kind == "abi":
        return ".json"
    if kind == "audit-report":
        return ".pdf"
    if kind == "api-spec":
        return ".json"
    return ".bin"


def infer_artifact_kind(url: str) -> str:
    lowered = url.lower()
    if lowered.endswith(APK_SUFFIXES):
        return "apk"
    if lowered.endswith(ARCHIVE_SUFFIXES):
        return "source-archive"
    if lowered.endswith(".abi") or lowered.endswith(".abi.json") or ("abi" in lowered and lowered.endswith(".json")):
        return "abi"
    if any(token in lowered for token in ("audit", "report")) and lowered.endswith((".pdf", ".md", ".html", ".txt")):
        return "audit-report"
    if any(token in lowered for token in ("openapi", "swagger", "postman")) and lowered.endswith(
        (".json", ".yaml", ".yml")
    ):
        return "api-spec"
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


def flatten_values(*values: Any) -> list[Any]:
    items: list[Any] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, list):
            items.extend(value)
        else:
            items.append(value)
    return items


def normalize_focus_areas(value: Any, target_type: str) -> list[str]:
    items = flatten_values(value)
    if target_type == "smart-contract":
        items.append("smart-contract")

    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        key = clean_text(item).lower()
        if not key:
            continue
        label = FOCUS_AREA_ALIASES.get(key, clean_text(item))
        if label in seen:
            continue
        seen.add(label)
        normalized.append(label)
    return normalized


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


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def relative_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
