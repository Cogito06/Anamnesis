#!/usr/bin/env python3
"""从 cairn/fragments/ 完全推导出 INDEX.md。

索引是片段的纯派生物，不是手写文档——这样它永远不可能和片段不同步。
模型手写索引时漏掉一条是迟早的事，而漏掉的那条会静默地从检索里消失。

用法：  python rebuild_index.py [cairn 目录，默认 ./cairn]
"""
import re, sys, pathlib, datetime

# Windows 控制台默认 codepage 会把中文输出吃成乱码
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

MARKER = "<!-- cairn:v1 -->"

def parse_frontmatter(text):
    """极简 YAML 解析：只处理标量和单行内联列表，够用且无依赖。"""
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    fm, body = {}, m.group(2)
    for line in m.group(1).splitlines():
        if not line.strip() or line.startswith("#") or line.startswith(" ") or line.startswith("-"):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        v = v.split("  #")[0].strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        fm[k.strip()] = v
    return fm, body

def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "cairn")
    frag_dir = root / "fragments"
    if not frag_dir.is_dir():
        sys.exit(f"找不到 {frag_dir}")

    rows, warnings = [], []
    for f in sorted(frag_dir.glob("*.md")):
        fm, body = parse_frontmatter(f.read_text(encoding="utf-8"))
        fid = fm.get("id") or f.stem
        hook = fm.get("hook", "").strip()
        if not hook:
            warnings.append(f"{f.name}: 缺 hook 字段，索引里这条将没有钩子句")
        concepts = fm.get("concepts", [])
        if isinstance(concepts, str):
            concepts = [concepts]
        n_open = len(re.findall(r"^- \[ \]", body, re.M))

        d = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(fid))
        date = f"{d.group(2)}-{d.group(3)}" if d else \
               datetime.date.fromtimestamp(f.stat().st_mtime).strftime("%m-%d")
        sort_key = f"{d.group(1)}{d.group(2)}{d.group(3)}" if d else "0000"

        short = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", str(fid))
        rows.append((sort_key, f"- [{short}] {'/'.join(concepts)} — {hook} | open:{n_open} | {date}"))

    rows.sort(key=lambda r: r[0], reverse=True)
    total_open = sum(int(re.search(r"open:(\d+)", r[1]).group(1)) for r in rows)

    out = [MARKER, "# Cairn Index", "",
           f"<!-- {len(rows)} 条片段，{total_open} 个未解决问题。"
           f"本文件由 scripts/rebuild_index.py 自动生成，不要手改。 -->", ""]
    out += [r[1] for r in rows]
    (root / "INDEX.md").write_text("\n".join(out) + "\n", encoding="utf-8")

    print(f"索引已重建：{len(rows)} 条片段，{total_open} 个未解决问题")
    for w in warnings:
        print(f"  警告 {w}")
    if len(rows) > 200:
        print("  索引已超 200 条，考虑按 course 字段分片（见 ARCHITECTURE.md 第 3 节）")

if __name__ == "__main__":
    main()
