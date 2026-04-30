#!/usr/bin/env bash
set -Eeuo pipefail

TSV_MODE=0

usage() {
  cat <<'EOF'
Usage:
  bash scripts/list-chrome-profiles.sh [--tsv]

Options:
  --tsv     Emit tab-separated rows: browser<TAB>user_data_dir<TAB>profile_dir<TAB>profile_name
  -h        Show this help text.
EOF
}

parse_args() {
  while (($# > 0)); do
    case "$1" in
      --tsv)
        TSV_MODE=1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        printf '[list-chrome-profiles] ERROR: Unknown argument: %s\n' "$1" >&2
        exit 1
        ;;
    esac
  done
}

main() {
  parse_args "$@"

  python3 - "$TSV_MODE" <<'PY'
import json
import sys
from pathlib import Path

tsv_mode = sys.argv[1] == "1"
home = Path.home()

candidates = [
    ("google-chrome", home / ".config" / "google-chrome"),
    ("chromium", home / ".config" / "chromium"),
]

rows = []

for browser, user_data_dir in candidates:
    if not user_data_dir.is_dir():
        continue

    local_state = user_data_dir / "Local State"
    seen = set()

    if local_state.is_file():
        try:
            data = json.loads(local_state.read_text(encoding="utf-8"))
            info_cache = ((data.get("profile") or {}).get("info_cache") or {})
            for profile_dir, info in sorted(info_cache.items(), key=lambda item: item[0]):
                name = info.get("name") or profile_dir
                rows.append((browser, str(user_data_dir), profile_dir, name))
                seen.add(profile_dir)
        except Exception:
            pass

    fallback_dirs = []
    default_dir = user_data_dir / "Default"
    if default_dir.is_dir():
        fallback_dirs.append(default_dir.name)
    fallback_dirs.extend(sorted(path.name for path in user_data_dir.glob("Profile *") if path.is_dir()))

    for profile_dir in fallback_dirs:
      if profile_dir not in seen:
          rows.append((browser, str(user_data_dir), profile_dir, profile_dir))
          seen.add(profile_dir)

if tsv_mode:
    for row in rows:
        print("\t".join(row))
    raise SystemExit

if not rows:
    print("No Chrome/Chromium profiles detected.")
    raise SystemExit

for idx, (browser, user_data_dir, profile_dir, profile_name) in enumerate(rows, start=1):
    print(f"{idx}. {profile_name} [{profile_dir}]")
    print(f"   browser: {browser}")
    print(f"   user-data-dir: {user_data_dir}")
PY
}

main "$@"
