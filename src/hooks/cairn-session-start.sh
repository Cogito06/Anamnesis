#!/usr/bin/env bash
# Anamnesis / SessionStart —— 注入 cairn 索引与未解决问题。
# 非 cairn 仓库静默退出，不干扰任何其他项目。
set -u
. "$HOME/.claude/hooks/cairn-lib.sh"

MAX_BYTES=32768   # 约 8k token；超过说明该压缩 open:0 的条目了

input=$(cat)
cwd=$(json_field "$input" cwd); [ -n "$cwd" ] || cwd="$PWD"
is_cairn_repo "$cwd" || exit 0

# 记录会话起点，供 PreCompact / SessionEnd 判断本次是否已落盘
sid=$(json_field "$input" session_id)
mkdir -p "$CAIRN_STATE" 2>/dev/null
[ -n "$sid" ] && : > "$CAIRN_STATE/$sid.stamp"
find "$CAIRN_STATE" -name '*.stamp' -mtime +7 -delete 2>/dev/null   # 清理陈旧 stamp

idx="$cwd/$CAIRN_DIR/INDEX.md"

# 只取条目行。魔术标记、标题、"本文件自动生成"那类注释是给 hook 和人看的，
# 每次注入等于白烧 token。
entries=$(grep -E '^(- \[|## )' "$idx" 2>/dev/null)
n=$(printf '%s' "$entries" | grep -c '^- \[')

echo "## Anamnesis —— 已归档的认知片段（$CAIRN_DIR/INDEX.md，共 ${n:-0} 条）"
echo
size=$(printf '%s' "$entries" | wc -c | tr -d ' ')
if [ "${size:-0}" -gt "$MAX_BYTES" ]; then
  printf '%s' "$entries" | head -c "$MAX_BYTES"
  printf '\n\n（索引超过 %s 字节已截断——该压缩 open:0 的条目了，见 ARCHITECTURE.md 第 3 节）\n' "$MAX_BYTES"
else
  printf '%s\n' "$entries"
fi

open=$(grep -rh '^- \[ \]' "$cwd/$CAIRN_DIR/fragments" 2>/dev/null | head -n 30)
if [ -n "$open" ]; then
  echo
  echo "## 未解决的遗留问题"
  echo
  printf '%s\n' "$open"
fi

echo
echo "讨论到索引里已有的主题时，先读 $CAIRN_DIR/fragments/<slug>.md 的全文再往下推，不要重新推导用户已经想通的部分。索引里那句钩子是判断该不该展开的依据，不是片段的全部内容。片段间用 [[slug]] 互相引用，顺着链接能找到相关的那几条。"
exit 0
