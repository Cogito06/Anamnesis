#!/usr/bin/env bash
# Anamnesis / PreCompact —— 只提醒，不阻塞。
# PreCompact 拿不到 additionalContext，能做的上限就是发一条 systemMessage。
set -u
. "$HOME/.claude/hooks/cairn-lib.sh"

input=$(cat)
cwd=$(json_field "$input" cwd); [ -n "$cwd" ] || cwd="$PWD"
is_cairn_repo "$cwd" || exit 0

sid=$(json_field "$input" session_id)
stamp="$CAIRN_STATE/$sid.stamp"

# 本次会话已经落过盘就不啰嗦
if [ -n "$sid" ] && [ -f "$stamp" ]; then
  if [ -n "$(find "$cwd/$CAIRN_DIR/fragments" -name '*.md' -newer "$stamp" 2>/dev/null)" ]; then
    exit 0
  fi
fi

echo '{"systemMessage": "[Anamnesis] 上下文即将压缩，本次会话还没有片段落盘。压缩之后这些讨论就捞不回来了 —— 现在打 /cairn 垒一块。"}'
exit 0
