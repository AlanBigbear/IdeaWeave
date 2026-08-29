#!/usr/bin/env bash
set -Eeuo pipefail

target_commit="${1:-}"
deploy_path="${DEPLOY_PATH:-/opt/ideaweave}"
project_name="${COMPOSE_PROJECT_NAME:-ideaweave}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gate_script="${script_dir}/database-change-gate.sh"
state_dir="${deploy_path}/.deploy-state"
compose_files=(-f docker-compose.yml -f docker-compose.production.yml)
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
rollback_backend="${project_name}-backend:rollback-${timestamp}"
rollback_frontend="${project_name}-frontend:rollback-${timestamp}"
backend_image="${project_name}-backend:latest"
frontend_image="${project_name}-frontend:latest"

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

fail() {
  log "错误: $*" >&2
  exit 1
}

if [[ $# -ne 1 ]]; then
  fail "用法: $0 <目标提交>"
fi
if [[ ! "$target_commit" =~ ^[0-9a-f]{40}$ ]]; then
  fail "目标提交必须是完整的 40 位 Git 提交哈希"
fi
[[ -x "$gate_script" ]] || fail "缺少数据库变更检查脚本: ${gate_script}"
[[ -d "$deploy_path/.git" ]] || fail "部署目录不是 Git 仓库: ${deploy_path}"
command -v curl >/dev/null || fail "服务器缺少 curl"
command -v flock >/dev/null || fail "服务器缺少 flock"

exec 9>"/tmp/${project_name}-deploy.lock"
flock -n 9 || fail "已有部署任务正在运行"

cd "$deploy_path"
previous_code_commit="$(git rev-parse HEAD)"
runtime_commit="$previous_code_commit"
if [[ -f "$state_dir/runtime_commit" ]]; then
  saved_runtime_commit="$(tr -d '[:space:]' < "$state_dir/runtime_commit")"
  if git cat-file -e "${saved_runtime_commit}^{commit}" 2>/dev/null; then
    runtime_commit="$saved_runtime_commit"
  fi
fi

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  git status --short --untracked-files=no >&2
  fail "部署目录存在已跟踪的本地修改，请先人工处理"
fi

log "拉取 origin/main"
git fetch --prune origin main
git cat-file -e "${target_commit}^{commit}" 2>/dev/null || fail "远端不存在目标提交 ${target_commit}"
git merge-base --is-ancestor "$target_commit" origin/main || fail "目标提交不属于当前 origin/main"
git merge-base --is-ancestor "$previous_code_commit" "$target_commit" || fail "目标提交无法从当前代码快进更新"

"$gate_script" "$runtime_commit" "$target_commit"

bootstrap_paths=(
  backend/Dockerfile.production
  frontend/Dockerfile.production
  docker-compose.production.yml
)
bootstrap_backup="${deploy_path}-bootstrap-backup/${timestamp}"
for path in "${bootstrap_paths[@]}"; do
  if [[ -e "$path" ]] && ! git ls-files --error-unmatch "$path" >/dev/null 2>&1 && git cat-file -e "${target_commit}:${path}" 2>/dev/null; then
    expected_file="$(mktemp)"
    git show "${target_commit}:${path}" > "$expected_file"
    if ! cmp -s "$path" "$expected_file"; then
      rm -f "$expected_file"
      fail "服务器已有未跟踪文件且内容不同，需人工处理: ${path}"
    fi
    rm -f "$expected_file"
    mkdir -p "${bootstrap_backup}/$(dirname "$path")"
    mv "$path" "${bootstrap_backup}/${path}"
    log "已将与仓库一致的历史部署文件备份到 ${bootstrap_backup}/${path}"
  fi
done

unexpected_untracked=()
while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  case "$path" in
    backend/data/backups/*|.deploy-state/*)
      ;;
    *)
      unexpected_untracked+=("$path")
      ;;
  esac
done < <(git ls-files --others --exclude-standard)

if [[ ${#unexpected_untracked[@]} -gt 0 ]]; then
  printf '不允许的未跟踪文件:\n' >&2
  printf '  - %s\n' "${unexpected_untracked[@]}" >&2
  fail "部署目录存在未知文件，请先人工处理"
fi

mkdir -p "$state_dir"
printf '%s\n' "$runtime_commit" > "$state_dir/runtime_commit"

log "快进代码到 ${target_commit}"
git merge --ff-only "$target_commit"
[[ -f .env ]] || fail "部署目录缺少 .env"

compose=(sudo docker compose --project-name "$project_name" --env-file .env "${compose_files[@]}")
"${compose[@]}" config >/dev/null

printf '%s\n' "$target_commit" > "$state_dir/code_commit"

has_backend_rollback="false"
has_frontend_rollback="false"
if sudo docker image inspect "$backend_image" >/dev/null 2>&1; then
  sudo docker tag "$backend_image" "$rollback_backend"
  has_backend_rollback="true"
fi
if sudo docker image inspect "$frontend_image" >/dev/null 2>&1; then
  sudo docker tag "$frontend_image" "$rollback_frontend"
  has_frontend_rollback="true"
fi

health_check() {
  local attempts=30
  local urls=(
    http://127.0.0.1:8000/api/health
    http://127.0.0.1/api/health
    http://127.0.0.1:8080/api/health
  )
  local url
  local attempt
  for url in "${urls[@]}"; do
    for ((attempt = 1; attempt <= attempts; attempt++)); do
      if curl --fail --silent --show-error --max-time 5 "$url" >/dev/null; then
        break
      fi
      if [[ $attempt -eq $attempts ]]; then
        log "健康检查失败: ${url}" >&2
        return 1
      fi
      sleep 2
    done
  done
}

rollback_runtime() {
  log "恢复部署前运行镜像"
  if [[ "$has_backend_rollback" == "true" ]]; then
    sudo docker tag "$rollback_backend" "$backend_image"
  fi
  if [[ "$has_frontend_rollback" == "true" ]]; then
    sudo docker tag "$rollback_frontend" "$frontend_image"
  fi
  if [[ "$has_backend_rollback" != "true" || "$has_frontend_rollback" != "true" ]]; then
    log "缺少完整回滚镜像，无法自动恢复" >&2
    return 1
  fi
  "${compose[@]}" up -d --no-build --force-recreate backend frontend
  health_check
  printf '%s\n' "$runtime_commit" > "$state_dir/runtime_commit"
}

log "构建生产镜像"
"${compose[@]}" build backend frontend

log "更新生产容器"
if ! "${compose[@]}" up -d --no-build --force-recreate backend frontend; then
  rollback_runtime || true
  fail "容器更新失败，已尝试恢复部署前镜像"
fi

if ! health_check; then
  rollback_runtime || true
  fail "新版本健康检查失败，已尝试恢复部署前镜像"
fi

printf '%s\n' "$target_commit" > "$state_dir/runtime_commit"
log "部署成功，当前运行提交: ${target_commit}"
