#!/usr/bin/env bash
# Anamnesis / SessionEnd —— 收尾提醒。
# 注意：所有 SessionEnd hook 共享 1.5 秒总预算，这里只能做几次 stat，不能跑重活。
set -u
. "$HOME/.claude/hooks/cairn-lib.sh"

input=$(cat)
cwd=$(json_field "$input" cwd); [ -n "$cwd" ] || cwd="$PWD"
is_cairn_repo "$cwd" || exit 0

sid=$(json_field "$input" session_id)
stamp="$CAIRN_STATE/$sid.stamp"
[ -n "$sid" ] && [ -f "$stamp" ] || exit 0

if [ -z "$(find "$cwd/$CAIRN_DIR/fragments" -name '*.md' -newer "$stamp" 2>/dev/null)" ]; then
  echo '{"systemMessage": "[Anamnesis] 本次会话结束，没有片段落盘。如果聊出了值得留的东西，下次开会话时还能从 transcript 里捞 —— 但不如现在记得清楚。"}'
fi
rm -f "$stamp" "$CAIRN_STATE/$sid.blocked" 2>/dev/null
exit 0
