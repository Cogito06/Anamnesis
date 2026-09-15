#!/usr/bin/env python3
"""从 cairn/fragments/ 完全推导出 INDEX.md，并校验片段之间的引用。

索引是片段的纯派生物，不是手写文档——这样它永远不可能和片段不同步。
模型手写索引时漏掉一条是迟早的事，而漏掉的那条会静默地从检索里消失。

身份规则：文件名即 slug 即 id。frontmatter 里不再存 id，
日期存在 date 字段（元数据，不参与身份），所以写 [[链接]] 时不需要记日期。

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
MAX_CONCEPTS = 5        # 索引行只放前 5 个；concepts 按检索概率降序写
LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def scalar(fm, key):
    """取标量字段。空值会被 parse_frontmatter 解析成 []，这里还原成 ""——
    否则 str([]) == "[]" 会让空字段看起来有内容，缺字段的警告就永远不响。"""
    v = fm.get(key, "")
    return v.strip() if isinstance(v, str) else ""


def parse_frontmatter(text):
    """极简 YAML：标量、单行内联列表、缩进块列表。无依赖，够用。"""
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    fm, body, key = {}, m.group(2), None
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t", "-")):          # 块列表的一项
            item = line.lstrip(" \t-").strip()
            item = item.split("  #")[0].strip()        # 只剥「两空格 + #」的注释，
            if key and item:                           # 免得吃掉 path#anchor 的锚点
                fm.setdefault(key, []).append(item)
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        key = k.strip()
        v = v.split("  #")[0].strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        fm[key] = v if v != "" else []
    return fm, body


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "cairn").resolve()   # resolve 之后 .parent 才是仓库根
    frag_dir = root / "fragments"
    if not frag_dir.is_dir():
        sys.exit(f"找不到 {frag_dir}")

    repo = root.parent
    files = sorted(frag_dir.glob("*.md"))
    slugs = {f.stem for f in files}
    rows, warn, labels = {}, [], {}
    out_links, in_links = {}, {s: set() for s in slugs}

    for f in files:
        slug = f.stem
        fm, body = parse_frontmatter(f.read_text(encoding="utf-8"))

        if "id" in fm:
            warn.append(f"{slug}: frontmatter 里还留着 id 字段——文件名即身份，删掉它")
        if "status" in fm:
            warn.append(f"{slug}: 还留着 status 字段——已由 open:N 表达，删掉它")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
            warn.append(f"{slug}: 文件名不合命名规范（全小写 ASCII + 短横线）")

        labels[slug] = scalar(fm, "cluster")

        hook = scalar(fm, "hook")
        if not hook:
            warn.append(f"{slug}: 缺 hook 字段，索引里这条将没有钩子句")

        concepts = fm.get("concepts", [])
        if isinstance(concepts, str):
            concepts = [concepts]

        # 片段间链接
        targets = set(LINK_RE.findall(body))
        out_links[slug] = targets
        for t in targets:
            if t not in slugs:
                warn.append(f"{slug}: 死链 [[{t}]] —— 没有这个片段")
            else:
                in_links[t].add(slug)

        # refs 指向的文件是否存在（锚点 #xxx 先剥掉）
        for r in fm.get("refs", []):
            path = str(r).split("#")[0].strip()
            if path and not (repo / path).exists():
                warn.append(f"{slug}: refs 悬空 → {path}（占位就忽略，笔误就改掉）")

        date = scalar(fm, "date")
        d = re.match(r"(\d{4})-(\d{2})-(\d{2})", date)
        if not d:
            warn.append(f"{slug}: 缺 date 字段，暂用文件修改时间")
            mt = datetime.date.fromtimestamp(f.stat().st_mtime)
            sort_key, shown = mt.strftime("%Y%m%d"), mt.strftime("%m-%d")
        else:
            sort_key = f"{d.group(1)}{d.group(2)}{d.group(3)}"
            shown = f"{d.group(2)}-{d.group(3)}"

        n_open = len(re.findall(r"^- \[ \]", body, re.M))
        rows[slug] = (sort_key, f"- [{slug}] {'/'.join(concepts[:MAX_CONCEPTS])} "
                               f"— {hook} | open:{n_open} | {shown}")

    # ---- 分簇：成员由 cluster 字段声明，图只负责校验 ----
    # 一度想用连通分量自动推导成员，但跨簇链接是正常且值得鼓励的
    # （「Karatsuba 够不到平衡点」理应链向「改模型 vs 改算法」），
    # 而只要有一条这样的边，两个簇就塌成一个。实测 6 条片段被并成 1 个簇。
    # 所以边界必须是声明的，图拿来找桥和查异常。
    adj = {s: set() for s in slugs}
    for a_, outs in out_links.items():
        for b_ in outs:
            if b_ in slugs:
                adj[a_].add(b_); adj[b_].add(a_)

    groups = {}
    for s in sorted(slugs):
        groups.setdefault(labels.get(s, ""), []).append(s)

    # 跨簇链接就是理解之间的桥，值得单独报出来
    bridges = sorted({(labels.get(x, ""), labels.get(y, ""))
                      for x in slugs for y in adj[x]
                      if labels.get(x) and labels.get(y) and labels[x] != labels[y]
                      and labels[x] < labels[y]})

    # 声明成同一簇却互不链接，通常说明簇名用错了或链接忘了写
    for name, members in groups.items():
        if name and len(members) > 1 and not any(adj[m] & set(members) for m in members):
            warn.append(f"簇「{name}」的 {len(members)} 条片段之间没有任何链接"
                        f"——确认它们真是一个板块")

    orphans = [s for s in sorted(slugs) if not adj[s]]

    total_open = sum(int(re.search(r"open:(\d+)", v[1]).group(1)) for v in rows.values())

    # 有名字的簇先排（按最新成员的日期倒序），无名字的最后平铺
    named = sorted(((n, m) for n, m in groups.items() if n),
                   key=lambda kv: max(rows[m][0] for m in kv[1]), reverse=True)
    unnamed = sorted(groups.get("", []), key=lambda m: rows[m][0], reverse=True)

    body_lines = []
    for name, members in named:
        members = sorted(members, key=lambda m: rows[m][0], reverse=True)
        body_lines.append(f"## {name}（{len(members)} 条）")
        body_lines += [rows[m][1] for m in members]
        body_lines.append("")
    if unnamed:
        if named:
            body_lines.append(f"## 尚未归簇（{len(unnamed)} 条）")
        body_lines += [rows[m][1] for m in unnamed]

    while body_lines and body_lines[-1] == "":
        body_lines.pop()

    (root / "INDEX.md").write_text(
        "\n".join([MARKER, "# Cairn Index", ""] + body_lines) + "\n", encoding="utf-8")

    n_links = sum(len(v) for v in out_links.values())
    entry_lines = [l for l in body_lines if l.startswith('- [')]
    total_bytes = sum(len(l.encode()) + 1 for l in body_lines if l)
    avg = total_bytes // max(len(entry_lines), 1)
    print(f"索引已重建：{len(rows)} 条片段，{total_open} 个未解决问题，"
          f"{n_links} 条链接，{len(named)} 个簇")
    print(f"  索引正文 {total_bytes} 字节，平均每行 {avg} 字节")
    for w in warn:
        print(f"  警告 {w}")
    if bridges:
        print("  跨簇的桥（理解之间的连接，通常是最有价值的部分）：")
        for x, y in bridges:
            print(f"    {x} ←→ {y}")
    if orphans:
        print(f"  孤儿片段（没有任何进出链接，可能还没接进你的理解网络）：{', '.join(orphans)}")
    if total_bytes > 12000:
        print("  索引常驻量已超 ~4k token，考虑把 open:0 的片段索引行压缩（见 ARCHITECTURE.md）")


if __name__ == "__main__":
    main()