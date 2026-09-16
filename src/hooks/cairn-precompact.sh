#!/usr/bin/env bash
# Anamnesis / PreCompact —— 压缩前拦一次，给你存档的机会。
#
# 为什么是拦而不是只提醒：exit 0 的话，hook 打印完消息压缩就立刻执行完了，
# 你读到「现在打 /cairn」时对话已经没了——那是讣告不是警报。
# exit 2 才挡得住，让你有机会把认知轨迹存下来再压。
#
# 但每个会话只挡一次：挡完就写个标记，第二次放行。否则你不想存的时候会被卡死。
set -u
. "$HOME/.claude/hooks/cairn-lib.sh"

input=$(cat)
cwd=$(json_field "$input" cwd); [ -n "$cwd" ] || cwd="$PWD"
is_cairn_repo "$cwd" || exit 0

sid=$(json_field "$input" session_id)
stamp="$CAIRN_STATE/$sid.stamp"
blocked="$CAIRN_STATE/$sid.blocked"

# 本次会话已经落过盘就不打扰
if [ -n "$sid" ] && [ -f "$stamp" ]; then
  if [ -n "$(find "$cwd/$CAIRN_DIR/fragments" -name '*.md' -newer "$stamp" 2>/dev/null)" ]; then
    exit 0
  fi
fi

# 已经挡过一次，这次放行——不能让人存不了档就一直压不了
if [ -n "$sid" ] && [ -f "$blocked" ]; then
  echo '{"systemMessage": "[Anamnesis] 已经提醒过一次，这次放行压缩。本次会话的讨论细节将不再可回溯。"}'
  exit 0
fi

[ -n "$sid" ] && : > "$blocked"
echo "[Anamnesis] 上下文满了，压缩会把本次会话的细节抹掉，而本次还没有片段落盘。" >&2
echo "先打 /cairn 存档，再让它压。不想存就再压一次，第二次会直接放行。" >&2
exit 2
