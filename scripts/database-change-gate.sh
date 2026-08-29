#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "用法: $0 <基准提交> <目标提交> [--report-only]" >&2
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
  exit 64
fi

base_commit="$1"
target_commit="$2"
report_only="false"

if [[ ${3:-} == "--report-only" ]]; then
  report_only="true"
elif [[ $# -eq 3 ]]; then
  usage
  exit 64
fi

git cat-file -e "${base_commit}^{commit}" 2>/dev/null || {
  echo "找不到基准提交: ${base_commit}" >&2
  exit 65
}
git cat-file -e "${target_commit}^{commit}" 2>/dev/null || {
  echo "找不到目标提交: ${target_commit}" >&2
  exit 65
}

changed_lines_match() {
  local path="$1"
  local pattern="$2"

  git diff --unified=0 --no-ext-diff --no-color --no-renames \
    "${base_commit}..${target_commit}" -- "$path" \
    | sed -n '/^[+-]/p' \
    | sed '/^+++ /d; /^--- /d' \
    | grep -Eiq -- "$pattern"
}

config_database_pattern='(^|[^[:alnum:]_])(database_url|mysql_connect_timeout|mysql_fallback_sqlite|data_dir|db_path|sqlalchemy_url)([^[:alnum:]_]|$)'
compose_database_pattern='(^|[^[:alnum:]_])(database_url|mysql_[[:alnum:]_]*|data_dir|backend_data|db)([^[:alnum:]_]|$)|mysql(\+|:|/)|/var/lib/mysql'

database_paths=()
while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  case "$path" in
    backend/app/core/config.py)
      if changed_lines_match "$path" "$config_database_pattern"; then
        database_paths+=("$path")
      fi
      ;;
    docker-compose.prod.yml)
      if changed_lines_match "$path" "$compose_database_pattern"; then
        database_paths+=("$path")
      fi
      ;;
    *.sql|deploy/*|backend/app/models/*|backend/app/core/database.py|backend/app/main.py|backend/app/services/trial.py|backend/scripts/*|backend/data/*|docker-compose.yml|Dockerfile.prod)
      database_paths+=("$path")
      ;;
  esac
done < <(git diff --name-only --no-renames "${base_commit}..${target_commit}")

if [[ ${#database_paths[@]} -eq 0 ]]; then
  echo "DATABASE_CHANGE_DETECTED=false"
  echo "未检测到数据库相关代码变更"
  exit 0
fi

echo "DATABASE_CHANGE_DETECTED=true"
echo "检测到需要人工处理的数据库相关变更:"
printf '  - %s\n' "${database_paths[@]}"

if [[ "$report_only" == "true" ]]; then
  echo "仅报告数据库相关变更，不执行部署"
  exit 0
fi

echo "自动部署已停止。线上使用 SQLite，而上游数据库交付为 MySQL，需要转为完整人工处理" >&2
exit 42
