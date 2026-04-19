#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s TARGET_REPO [-Force] [-NoEnablePlugins] [-CodexHome PATH]\n' "$(basename "$0")" >&2
}

die() {
  printf '%s\n' "$*" >&2
  exit 1
}

need_command() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

normalize_path() {
  local path="$1"
  if command -v realpath >/dev/null 2>&1; then
    realpath -m -- "$path"
    return
  fi

  python3 - "$path" <<'PY'
import os
import sys

print(os.path.realpath(sys.argv[1]))
PY
}

resolve_final_path() {
  local path="$1"
  if [[ -e "$path" || -L "$path" ]]; then
    if command -v realpath >/dev/null 2>&1; then
      realpath -- "$path"
      return
    fi
  fi

  python3 - "$path" <<'PY'
import os
import sys

print(os.path.realpath(sys.argv[1]))
PY
}

path_inside() {
  local child root
  child="$(normalize_path "$1")"
  root="$(normalize_path "$2")"

  [[ "$child" == "$root" || "$child" == "$root/"* ]]
}

timestamp() {
  date +"%Y%m%d-%H%M%S"
}

backup_conflict() {
  local path="$1"
  local backup="${path}.backup-$(timestamp)"
  mv -- "$path" "$backup"
  printf '%s\n' "$backup"
}

backup_file_copy() {
  local path="$1"
  local backup="${path}.backup-$(timestamp)"
  cp -a -- "$path" "$backup"
  printf '%s\n' "$backup"
}

get_link_target_path() {
  local path="$1"
  local raw_target

  [[ -L "$path" ]] || return 1
  raw_target="$(readlink -- "$path")" || return 1

  if [[ "$raw_target" != /* ]]; then
    raw_target="$(dirname "$path")/$raw_target"
  fi

  normalize_path "$raw_target"
}

get_link_state() {
  local name="$1"
  local link_path="$2"
  local target_path="$3"
  local accept_targets="${4-}"
  local state current_target="" current_resolved="" desired_resolved candidate

  if [[ ! -e "$link_path" && ! -L "$link_path" ]]; then
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$name" "$link_path" "$target_path" "missing" "" ""
    return
  fi

  if [[ -L "$link_path" ]]; then
    current_target="$(get_link_target_path "$link_path" || true)"
    if [[ -n "$current_target" ]]; then
      current_resolved="$(resolve_final_path "$current_target")"
    fi

    desired_resolved="$(resolve_final_path "$target_path")"
    state="wrong-target"

    if [[ "$current_target" == "$target_path" || "$current_resolved" == "$desired_resolved" ]]; then
      state="linked"
    else
      while IFS= read -r candidate; do
        [[ -n "$candidate" ]] || continue
        if [[ "$current_resolved" == "$(normalize_path "$candidate")" ]]; then
          state="linked"
          break
        fi
      done <<< "$accept_targets"
    fi
  else
    state="exists-not-link"
  fi

  printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$name" "$link_path" "$target_path" "$state" "$current_target" "$current_resolved"
}

ensure_link() {
  local name="$1"
  local link_path="$2"
  local target_path="$3"
  local accept_targets="${4-}"
  local state_record state backup

  state_record="$(get_link_state "$name" "$link_path" "$target_path" "$accept_targets")"
  IFS=$'\t' read -r _ _ _ state _ _ <<< "$state_record"

  if [[ "$state" == "linked" ]]; then
    printf '%s\n' "$state_record"
    return
  fi

  if [[ "$state" != "missing" ]]; then
    (( force == 1 )) || die "Refusing to replace '$link_path' because it is '$state'. Re-run with -Force to back it up and replace it."
    backup="$(backup_conflict "$link_path")"
    printf 'Backed up %s -> %s\n' "$link_path" "$backup" >&2
  fi

  mkdir -p -- "$(dirname "$link_path")"
  ln -s -- "$target_path" "$link_path"
  get_link_state "$name" "$link_path" "$target_path" "$accept_targets"
}

remove_managed_link() {
  local name="$1"
  local link_path="$2"
  local target_path="$3"

  if [[ ! -e "$link_path" && ! -L "$link_path" ]]; then
    printf '%s\t%s\t%s\t%s\n' "$name" "missing" "$link_path" "$target_path"
    return
  fi

  if [[ ! -L "$link_path" ]]; then
    printf '%s\t%s\t%s\t%s\n' "$name" "exists-not-link" "$link_path" "$target_path"
    return
  fi

  rm -f -- "$link_path"
  printf '%s\t%s\t%s\t%s\n' "$name" "removed" "$link_path" "$target_path"
}

ensure_agent_file() {
  local path="$1"
  local existing_state="updated"
  local backup

  if [[ -e "$path" || -L "$path" ]]; then
    if [[ -d "$path" && ! -f "$path" ]]; then
      (( force == 1 )) || die "Refusing to replace directory '$path' with AGENTS.md file. Re-run with -Force to back it up and replace it."
      backup="$(backup_conflict "$path")"
      printf 'Backed up %s -> %s\n' "$path" "$backup" >&2
      rm -rf -- "$path" 2>/dev/null || true
    fi
  fi

  existing_state="$(
    python3 - "$source_agents_path" "$path" "$source_repo" <<'PY'
import pathlib
import re
import sys

source_agents_path = pathlib.Path(sys.argv[1])
target_path = pathlib.Path(sys.argv[2])
source_repo = sys.argv[3]

source_agents = source_agents_path.read_text(encoding="utf-8")
match = re.search(r"^(.*?)(?=^## Repository Scope\s*$)", source_agents, re.MULTILINE | re.DOTALL)
source_prelude = (match.group(1) if match else source_agents).strip()

existing_content = ""
if target_path.exists() or target_path.is_symlink():
    existing_content = target_path.read_text(encoding="utf-8")

local_match = re.search(
    r"<!-- spec-codex-workspace-install:start-local -->\r?\n(.*?)\r?\n<!-- spec-codex-workspace-install:end-local -->",
    existing_content,
    re.DOTALL,
)
if local_match:
    local_content = local_match.group(1).strip()
else:
    local_content = existing_content.strip()

parts = [
    "<!-- spec-codex-workspace-install:generated -->",
    f"<!-- source-repo: {source_repo} -->",
    "",
    source_prelude,
    "",
    "<!-- spec-codex-workspace-install:start-local -->",
]
if local_content:
    parts.append(local_content)
parts.append("<!-- spec-codex-workspace-install:end-local -->")

rendered = "\n".join(parts).rstrip() + "\n"
if existing_content != rendered:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(rendered, encoding="utf-8", newline="\n")
    print("updated")
else:
    print("unchanged")
PY
  )"

  printf '%s\t%s\t%s\n' "workspace:AGENTS.md" "$existing_state" "$path"
}

ensure_plugin_config_enabled() {
  local config_path="$1"
  local plugin_keys_file="$2"
  local desired_file result backup

  desired_file="$(mktemp)"
  result="$(
    python3 - "$config_path" "$plugin_keys_file" "$marketplace_name" "$desired_file" <<'PY'
import pathlib
import re
import sys

config_path = pathlib.Path(sys.argv[1])
plugin_keys_path = pathlib.Path(sys.argv[2])
marketplace_name = sys.argv[3]
desired_path = pathlib.Path(sys.argv[4])

plugin_keys = [
    line.strip()
    for line in plugin_keys_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

original = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
updated = original

section_pattern = re.compile(
    r'(?ms)^\[plugins\."(?P<key>[^"]+)"\]\r?\n(?P<body>.*?)(?=^\[|\Z)'
)

matches = list(section_pattern.finditer(updated))
for match in reversed(matches):
    key = match.group("key")
    if key.endswith(f"@{marketplace_name}") and key not in plugin_keys:
        updated = updated[:match.start()] + updated[match.end():]

for plugin_key in plugin_keys:
    header = f'[plugins."{plugin_key}"]'
    plugin_pattern = re.compile(
        r'(?ms)^\[plugins\."' + re.escape(plugin_key) + r'"\]\r?\n(?P<body>.*?)(?=^\[|\Z)'
    )
    match = plugin_pattern.search(updated)

    if match:
        body = match.group("body")
        lines = body.splitlines()
        new_lines = []
        enabled_written = False

        for line in lines:
            if re.match(r"^\s*enabled\s*=", line):
                if not enabled_written:
                    new_lines.append("enabled = true")
                    enabled_written = True
                continue

            if line or new_lines:
                new_lines.append(line)

        if not enabled_written:
            new_lines.insert(0, "enabled = true")

        new_section = header + "\n" + "\n".join(new_lines).rstrip() + "\n\n"
        updated = updated[:match.start()] + new_section + updated[match.end():]
        continue

    if updated and not updated.endswith("\n"):
        updated += "\n"
    if updated.strip():
        updated += "\n"
    updated += header + "\n" + "enabled = true\n"

if updated:
    updated = updated.rstrip("\n") + "\n"

desired_path.write_text(updated, encoding="utf-8", newline="\n")
print("updated" if updated != original else "unchanged")
PY
  )"

  if [[ "$result" == "updated" ]]; then
    if [[ -f "$config_path" ]]; then
      backup="$(backup_file_copy "$config_path")"
      printf 'Backed up %s -> %s\n' "$config_path" "$backup" >&2
    fi
    mkdir -p -- "$(dirname "$config_path")"
    cp -- "$desired_file" "$config_path"
  fi

  rm -f -- "$desired_file"

  printf '%s\t%s\n' "$config_path" "$result"
}

format_link_results() {
  local header="$1"
  shift

  printf '\n%s\n' "$header"
  for entry in "$@"; do
    IFS=$'\t' read -r name link_path target_path state _ current_resolved <<< "$entry"
    if [[ -n "$current_resolved" ]]; then
      printf '- [%s] %s -> %s (resolved: %s)\n' "$state" "$link_path" "$target_path" "$current_resolved"
    else
      printf '- [%s] %s -> %s\n' "$state" "$link_path" "$target_path"
    fi
  done
}

format_simple_results() {
  local header="$1"
  shift

  printf '\n%s\n' "$header"
  for entry in "$@"; do
    IFS=$'\t' read -r name state path target_path <<< "$entry"
    if [[ -n "${target_path-}" ]]; then
      printf '- [%s] %s -> %s\n' "$state" "$path" "$target_path"
    else
      printf '- [%s] %s\n' "$state" "$path"
    fi
  done
}

need_command python3
need_command readlink
need_command ln

force=0
no_enable_plugins=0
target_repo=""
codex_home="${HOME}/.codex"

while (($# > 0)); do
  case "$1" in
    -Force)
      force=1
      ;;
    -NoEnablePlugins)
      no_enable_plugins=1
      ;;
    -CodexHome)
      shift
      (($# > 0)) || die "Missing value for -CodexHome"
      codex_home="$1"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      usage
      die "Unknown option: $1"
      ;;
    *)
      if [[ -n "$target_repo" ]]; then
        usage
        die "Unexpected argument: $1"
      fi
      target_repo="$1"
      ;;
  esac
  shift
done

[[ -n "$target_repo" ]] || {
  usage
  exit 1
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_repo="$(normalize_path "$script_dir/..")"
marketplace_path="$source_repo/.agents/plugins/marketplace.json"
source_agents_path="$source_repo/AGENTS.md"
target_repo="$(normalize_path "$target_repo")"
codex_home="$(normalize_path "$codex_home")"

[[ -d "$target_repo" ]] || die "Target repo does not exist or is not a directory: $target_repo"
[[ -f "$marketplace_path" ]] || die "Missing Codex marketplace manifest: $marketplace_path"

plugin_info_file="$(mktemp)"
plugin_keys_file="$(mktemp)"
trap 'rm -f -- "$plugin_info_file" "$plugin_keys_file"' EXIT

python3 - "$marketplace_path" "$plugin_info_file" "$plugin_keys_file" <<'PY'
import json
import pathlib
import sys

marketplace_path = pathlib.Path(sys.argv[1])
plugin_info_path = pathlib.Path(sys.argv[2])
plugin_keys_path = pathlib.Path(sys.argv[3])

marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))

info_lines = [marketplace["name"]]
key_lines = []
for plugin in marketplace["plugins"]:
    source_path = plugin["source"]["path"]
    info_lines.append(f'{plugin["name"]}\t{source_path}')
    key_lines.append(f'{plugin["name"]}@{marketplace["name"]}')

plugin_info_path.write_text("\n".join(info_lines) + "\n", encoding="utf-8")
plugin_keys_path.write_text("\n".join(key_lines) + ("\n" if key_lines else ""), encoding="utf-8")
PY

mapfile -t plugin_info_lines < "$plugin_info_file"
marketplace_name="${plugin_info_lines[0]}"
plugin_lines=("${plugin_info_lines[@]:1}")

workspace_results=()
workspace_results+=("$(ensure_link "workspace:.agents/plugins" "$(normalize_path "$target_repo/.agents/plugins")" "$(normalize_path "$source_repo/.agents/plugins")")")
workspace_results+=("$(ensure_link "workspace:plugins" "$(normalize_path "$target_repo/plugins")" "$(normalize_path "$source_repo/plugins")")")
workspace_results+=("$(ensure_link "workspace:skills" "$(normalize_path "$target_repo/skills")" "$(normalize_path "$source_repo/skills")")")

agent_result="$(ensure_agent_file "$(normalize_path "$target_repo/AGENTS.md")")"

plugin_results=()
stale_results=()
config_result=""

if (( no_enable_plugins == 0 )); then
  desired_plugin_names=()

  for line in "${plugin_lines[@]}"; do
    [[ -n "$line" ]] || continue
    IFS=$'\t' read -r plugin_name source_path <<< "$line"
    source_path="${source_path#./}"
    plugin_dir="$(basename "$source_path")"
    desired_plugin_names+=("$plugin_dir")

    plugin_link_path="$(normalize_path "$codex_home/plugins/$plugin_dir")"
    plugin_target_path="$(normalize_path "$target_repo/$source_path")"
    accept_target="$(normalize_path "$source_repo/$source_path")"
    plugin_results+=("$(ensure_link "codex-plugin:$plugin_name" "$plugin_link_path" "$plugin_target_path" "$accept_target")")
  done

  plugins_root="$(normalize_path "$codex_home/plugins")"
  managed_roots=(
    "$(normalize_path "$target_repo/plugins")"
    "$(normalize_path "$source_repo/plugins")"
  )

  if [[ -d "$plugins_root" ]]; then
    while IFS= read -r -d '' item; do
      plugin_name="$(basename "$item")"
      skip=0
      for desired_name in "${desired_plugin_names[@]}"; do
        if [[ "$desired_name" == "$plugin_name" ]]; then
          skip=1
          break
        fi
      done
      (( skip == 1 )) && continue
      [[ -L "$item" ]] || continue

      current_target="$(get_link_target_path "$item" || true)"
      [[ -n "$current_target" ]] || continue
      current_resolved="$(resolve_final_path "$current_target")"

      is_managed=0
      for managed_root in "${managed_roots[@]}"; do
        if path_inside "$current_resolved" "$managed_root"; then
          is_managed=1
          break
        fi
      done

      (( is_managed == 1 )) || continue
      stale_results+=("$(remove_managed_link "stale-codex-plugin:$plugin_name" "$item" "$current_target")")
    done < <(find "$plugins_root" -mindepth 1 -maxdepth 1 -print0 2>/dev/null)
  fi

  config_path="$(normalize_path "$codex_home/config.toml")"
  config_result="$(ensure_plugin_config_enabled "$config_path" "$plugin_keys_file")"
fi

format_link_results "Workspace links:" "${workspace_results[@]}"
format_simple_results "AGENTS merge:" "$agent_result"

if (( no_enable_plugins == 0 )); then
  format_link_results "Codex plugin links:" "${plugin_results[@]}"

  if ((${#stale_results[@]} > 0)); then
    format_simple_results "Removed stale managed plugin links:" "${stale_results[@]}"
  fi

  format_simple_results "Codex config:" "$config_result"
fi

printf '\nTarget workspace prepared at: %s\n' "$target_repo"
if (( no_enable_plugins == 0 )); then
  printf "Plugins enabled from marketplace '%s': %s\n" "$marketplace_name" "${#plugin_lines[@]}"
fi
printf 'Restart Codex before opening the target workspace.\n'
