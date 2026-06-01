#!/usr/bin/env bash
set -euo pipefail

tool_name="__RADBUILD_TOOL__"
default_version="__RADBUILD_VERSION__"
radbuild_root="${RADBUILD_ROOT:-__RADBUILD_ROOT__}"

find_settings_from_args() {
  local prev=""
  for arg in "$@"; do
    if [[ "${prev}" == "--settings" ]]; then
      printf '%s\n' "${arg}"
      return 0
    fi
    case "${arg}" in
      --settings=*)
        printf '%s\n' "${arg#--settings=}"
        return 0
        ;;
    esac
    prev="${arg}"
  done
  return 1
}

find_settings_upward() {
  local dir="${PWD}"
  while [[ "${dir}" != "/" ]]; do
    if [[ -f "${dir}/settings.json" ]]; then
      printf '%s\n' "${dir}/settings.json"
      return 0
    fi
    dir="$(dirname "${dir}")"
  done
  return 1
}

read_radbuild_version() {
  local settings="$1"
  if [[ ! -f "${settings}" ]]; then
    return 1
  fi
  python3 - "$settings" <<'PY' 2>/dev/null || return 1
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
value = str(data.get("radbuild_version", "")).strip()
if value:
    print(value)
PY
}

normalize_version() {
  local version="$1"
  case "${version}" in
    "") printf '%s\n' "${default_version}" ;;
    v*) printf '%s\n' "${version}" ;;
    *) printf 'v%s\n' "${version}" ;;
  esac
}

settings_path="$(find_settings_from_args "$@" || true)"
if [[ -z "${settings_path}" ]]; then
  settings_path="$(find_settings_upward || true)"
fi

version="${default_version}"
if [[ -n "${settings_path}" ]]; then
  parsed_version="$(read_radbuild_version "${settings_path}" || true)"
  if [[ -n "${parsed_version}" ]]; then
    version="$(normalize_version "${parsed_version}")"
  fi
fi

target="${radbuild_root}/${version}/bin/${tool_name}"
if [[ ! -x "${target}" && "${version}" != "${default_version}" ]]; then
  fallback="${radbuild_root}/${default_version}/bin/${tool_name}"
  if [[ -x "${fallback}" ]]; then
    target="${fallback}"
  fi
fi

if [[ ! -x "${target}" ]]; then
  echo "RadBuild executable not found: ${target}" >&2
  echo "Install the requested RadBuild version under: ${radbuild_root}/<version>" >&2
  exit 127
fi

exec "${target}" "$@"
