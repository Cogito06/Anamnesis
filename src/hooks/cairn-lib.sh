# Anamnesis 公共函数。被三个 hook source。
# Windows 下 jq 不一定存在，所以用 sed 解析。

CAIRN_DIR="cairn"
CAIRN_MARKER="cairn:v1"
CAIRN_STATE="$HOME/.claude/anamnesis-state"

# json_field <json> <key>  —— 取字符串字段，Windows 路径的 \ 还原成 /
json_field() {
  printf '%s' "$1" \
    | sed -n "s/.*\"$2\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" \
    | sed 's|\\|/|g' \
    | head -n 1
}

# is_cairn_repo <cwd> —— 是 cairn 仓库返回 0
is_cairn_repo() {
  idx="$1/$CAIRN_DIR/INDEX.md"
  [ -f "$idx" ] || return 1
  head -n 1 "$idx" | grep -q "$CAIRN_MARKER" || return 1
  return 0
}
