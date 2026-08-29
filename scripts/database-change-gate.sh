#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "用法: $0 <基准提交> <目标提交> [--allow]" >&2
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
  exit 64
fi

base_commit="$1"
target_commit="$2"
allow_database_changes="false"

if [[ ${3:-} == "--allow" ]]; then
  allow_database_changes="true"
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

database_paths=()
while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  case "$path" in
    *.sql|deploy/*|backend/app/models/*|backend/app/core/database.py|backend/app/core/config.py|backend/app/main.py|backend/app/services/trial.py|backend/scripts/*|backend/data/*|docker-compose.yml|docker-compose.prod.yml|Dockerfile.prod)
      database_paths+=("$path")
      ;;
  esac
done < <(git diff --name-only "${base_commit}..${target_commit}")

if [[ ${#database_paths[@]} -eq 0 ]]; then
  echo "DATABASE_CHANGE_DETECTED=false"
  echo "未检测到数据库相关代码变更"
  exit 0
fi

echo "DATABASE_CHANGE_DETECTED=true"
echo "检测到需要人工处理的数据库相关变更:"
printf '  - %s\n' "${database_paths[@]}"

if [[ "$allow_database_changes" == "true" ]]; then
  echo "已收到人工放行，仅继续部署代码；脚本不会执行任何 SQL 或数据迁移"
  exit 0
fi

echo "自动部署已停止。请先人工完成数据库处理，再从 GitHub 手动运行流水线并勾选数据库已处理" >&2
exit 42
