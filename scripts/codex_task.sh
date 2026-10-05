#!/usr/bin/env bash
# Dùng: scripts/codex_task.sh new "task"        -> session mới
#       scripts/codex_task.sh resume "feedback" -> tiếp tục session gần nhất (cùng thư mục)
set -uo pipefail
mode="${1:?new|resume}"; shift
prompt="$*"
mkdir -p .codex
log=".codex/last.log"
msg=".codex/last_message.txt"
: > "$log"

opts=(-c 'sandbox_mode="workspace-write"' -c 'approval_policy="never"' -c 'sandbox_workspace_write.network_access=true' -o "$msg")

if [ "$mode" = "resume" ]; then
  timeout 3600 codex exec resume --last "${opts[@]}" "$prompt" >> "$log" 2>&1
else
  timeout 3600 codex exec "${opts[@]}" "$prompt" >> "$log" 2>&1
fi
echo "exit=$?" >> "$log"
echo "--- git status ---" >> "$log"; git status --short >> "$log"
