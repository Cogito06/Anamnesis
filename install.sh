#!/usr/bin/env bash
# Anamnesis 安装脚本
#   把 src/ 下的 skill 与 hooks 装进 ~/.claude/，并把三个 hook 合并进 settings.json。
#   幂等：重复运行只会覆盖 Anamnesis 自己的文件，不动你的其他配置。
set -eu

SRC="$(cd "$(dirname "$0")" && pwd)/src"
DEST="${CLAUDE_HOME:-$HOME/.claude}"

[ -d "$SRC" ] || { echo "找不到 $SRC，请在仓库根目录运行"; exit 1; }
# 注意：Windows 上 python3 常常是商店的占位符——存在但不执行，静默退出。
# 所以不能只看 command -v，要真跑一句看有没有输出。
PY=""
for cand in python3 python py; do
  if command -v "$cand" >/dev/null 2>&1 && [ "$("$cand" -c 'print(42)' 2>/dev/null)" = "42" ]; then
    PY="$cand"; break
  fi
done
[ -n "$PY" ] || { echo "找不到可用的 Python（合并 settings.json 需要，只用标准库）"; exit 1; }

mkdir -p "$DEST/skills" "$DEST/hooks" "$DEST/anamnesis-state" "$DEST/anamnesis"
rm -rf "$DEST/skills/cairn" "$DEST/anamnesis/graph"
cp -r "$SRC/skills/cairn" "$DEST/skills/cairn"
cp -r "$SRC/graph" "$DEST/anamnesis/graph"
cp "$SRC/hooks/"cairn-*.sh "$DEST/hooks/"
chmod +x "$DEST/hooks/"cairn-*.sh
echo "已安装 skill、图谱工具与 hooks 到 $DEST"

# hooks 配置里要写绝对路径。Git Bash 下 /c/... 形式换成 C:/... 更稳妥。
if command -v cygpath >/dev/null 2>&1; then
  HOOKDIR="$(cygpath -m "$DEST/hooks")"
else
  HOOKDIR="$DEST/hooks"
fi

CLAUDE_SETTINGS="$DEST/settings.json" HOOKDIR="$HOOKDIR" "$PY" - << 'PYEOF'
import json, os, pathlib, datetime, shutil, sys

# Windows 控制台默认 codepage 会把中文输出吃成乱码
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

p = pathlib.Path(os.environ["CLAUDE_SETTINGS"])
hookdir = os.environ["HOOKDIR"]

if p.exists():
    shutil.copy(p, p.with_suffix(f".json.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"))
    cfg = json.loads(p.read_text(encoding="utf-8"))
else:
    cfg = {}

def entry(script, timeout=None):
    h = {"type": "command", "command": "bash", "args": [f"{hookdir}/{script}"]}
    if timeout:
        h["timeout"] = timeout
    return {"hooks": [h]}

cfg.setdefault("hooks", {})
cfg["hooks"]["SessionStart"] = [entry("cairn-session-start.sh")]
cfg["hooks"]["PreCompact"]   = [entry("cairn-precompact.sh")]
cfg["hooks"]["SessionEnd"]   = [entry("cairn-session-end.sh", timeout=10)]

p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"已注册 hooks 到 {p}（原文件已备份）")
PYEOF

cat <<'MSG'

安装完成。三个 hook 已注册：SessionStart / PreCompact / SessionEnd。

下一步：
  1. 到任意学习仓库里开一个新会话（hooks 会热重载，但 SessionStart 要新会话才触发）
  2. 打 /cairn，它会问你要不要初始化 cairn/ 目录
  3. 攒下几条片段后，在学习仓库根目录跑：
       python ~/.claude/anamnesis/graph/graph.py cairn
     生成 cairn/graph.html，浏览器打开即可
MSG
