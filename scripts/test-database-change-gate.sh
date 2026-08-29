#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gate_script="${script_dir}/database-change-gate.sh"
fixture_dir="$(mktemp -d)"

cleanup() {
  rm -rf "$fixture_dir"
}
trap cleanup EXIT

mkdir -p "$fixture_dir/scripts" "$fixture_dir/backend/app/core"
cp "$gate_script" "$fixture_dir/scripts/database-change-gate.sh"

cd "$fixture_dir"
git init -q
git config user.name "IdeaWeave CI"
git config user.email "ci@ideaweave.local"

write_config() {
  local database_url="$1"
  local trial_reset_minutes="$2"
  printf 'database_url: str = "%s"\ntrial_reset_minutes: int = %s\n' \
    "$database_url" "$trial_reset_minutes" > backend/app/core/config.py
}

write_compose() {
  local database_url="$1"
  local trial_reset_minutes="$2"
  printf 'services:\n  backend:\n    environment:\n      DATABASE_URL: %s\n      TRIAL_RESET_MINUTES: %s\n' \
    "$database_url" "$trial_reset_minutes" > docker-compose.prod.yml
}

write_config "sqlite:///data/bstar.db" 60
write_compose "mysql+pymysql://ideaweave@db/ideaweave" 60
git add .
git commit -qm "基准"
base_commit="$(git rev-parse HEAD)"

start_case() {
  local branch="$1"
  git checkout -q -B "$branch" "$base_commit"
}

assert_gate() {
  local expected="$1"
  local label="$2"
  local output
  output="$(scripts/database-change-gate.sh "$base_commit" HEAD --report-only)"
  if ! grep -q "^DATABASE_CHANGE_DETECTED=${expected}$" <<< "$output"; then
    echo "门禁测试失败: ${label}" >&2
    echo "$output" >&2
    exit 1
  fi
}

start_case test-trial-config
write_config "sqlite:///data/bstar.db" 10
git add backend/app/core/config.py
git commit -qm "修改体验配置"
assert_gate false "非数据库后端配置应允许自动部署"

start_case test-database-config
write_config "sqlite:////app/data/bstar.db" 60
git add backend/app/core/config.py
git commit -qm "修改数据库配置"
assert_gate true "数据库后端配置应阻止自动部署"

start_case test-trial-compose
write_compose "mysql+pymysql://ideaweave@db/ideaweave" 10
git add docker-compose.prod.yml
git commit -qm "修改体验编排配置"
assert_gate false "非数据库编排配置应允许自动部署"

start_case test-database-compose
write_compose "mysql+pymysql://ideaweave@db/new_schema" 60
git add docker-compose.prod.yml
git commit -qm "修改数据库编排配置"
assert_gate true "数据库编排配置应阻止自动部署"

start_case test-sql
mkdir -p deploy
printf 'SELECT 1;\n' > deploy/schema.sql
git add deploy/schema.sql
git commit -qm "增加数据库脚本"
assert_gate true "数据库脚本应始终阻止自动部署"

echo "数据库变更门禁测试通过"
