#!/usr/bin/env python3
"""把 cairn/ 的片段和 [[链接]] 画成一张力导向知识图谱，输出单文件 HTML。

和 rebuild_index.py 同一个模式：从 fragments/ 推导，随时可重跑，不依赖网络。
图能看出索引看不出的三件事——哪些簇是孤岛、哪些簇之间只有一根细线连着
（那根线通常就是理解刚打通的地方）、哪些片段谁也不认识。

配色只用三个经过 CVD 全配对验证的色相（节点图里任意两簇都可能相邻，
所以适用"全配对"标准而非"相邻配对"；实测第四色相黄↔橙正常视觉 ΔE 13.7 < 15 会挂）。
超出三个的簇归入中性灰，靠节点标签和簇名标签承载身份——颜色从不单独表意。

用法：  python graph.py [cairn 目录，默认 ./cairn] [-o 输出路径]
"""
import json, re, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rebuild_index import parse_frontmatter, scalar, LINK_RE   # 不重复造解析器

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def collect(root):
    frag_dir = root / "fragments"
    if not frag_dir.is_dir():
        sys.exit(f"找不到 {frag_dir}")

    nodes, edges = {}, []
    files = sorted(frag_dir.glob("*.md"))
    slugs = {f.stem for f in files}

    for f in files:
        fm, body = parse_frontmatter(f.read_text(encoding="utf-8"))
        concepts = fm.get("concepts", [])
        if isinstance(concepts, str):
            concepts = [concepts]
        opens = re.findall(r"^- \[ \] (.+)$", body, re.M)
        nodes[f.stem] = {
            "id": f.stem,
            "cluster": scalar(fm, "cluster") or "（未归簇）",
            "hook": scalar(fm, "hook"),
            "concepts": concepts[:6],
            "open": [re.sub(r"\s+", " ", o).strip()[:120] for o in opens],
            "date": scalar(fm, "date"),
            "bytes": len(body.encode()),
            "refs": [str(r) for r in fm.get("refs", [])],
        }

    # 互链（A→B 且 B→A）合成一条边：图上不画箭头，两条重合的线只是把同一条画深。
    # 但互相引用确实是更强的连接，所以标出来画粗一点。
    seen = {}
    for slug in nodes:
        for t in sorted(set(LINK_RE.findall(
                (frag_dir / (slug + ".md")).read_text(encoding="utf-8")))):
            if t not in slugs or t == slug:
                continue
            key = tuple(sorted((slug, t)))
            if key in seen:
                seen[key]["mutual"] = True
            else:
                seen[key] = {"s": key[0], "t": key[1], "mutual": False,
                             "bridge": nodes[key[0]]["cluster"] != nodes[key[1]]["cluster"]}
    edges = [seen[k] for k in sorted(seen)]

    deg = {s: 0 for s in nodes}
    for e in edges:
        deg[e["s"]] += 1
        deg[e["t"]] += 1
    for s, n in nodes.items():
        n["deg"] = deg[s]

    # 颜色只给最大的三个簇；其余中性。节点标签和簇名标签才是身份的主载体。
    sizes = {}
    for n in nodes.values():
        sizes[n["cluster"]] = sizes.get(n["cluster"], 0) + 1
    ranked = sorted(sizes, key=lambda c: (-sizes[c], c))
    slot = {c: (i if i < 3 else 3) for i, c in enumerate(ranked)}
    if "（未归簇）" in slot:
        slot["（未归簇）"] = 3
    for n in nodes.values():
        n["slot"] = slot[n["cluster"]]

    return list(nodes.values()), edges, [(c, sizes[c], slot[c]) for c in ranked]


def main():
    args = [a for a in sys.argv[1:] if a != "-o"]
    out = None
    if "-o" in sys.argv:
        i = sys.argv.index("-o")
        out = pathlib.Path(sys.argv[i + 1])
        args = [a for a in args if a != str(out)]
    root = pathlib.Path(args[0] if args else "cairn").resolve()
    out = out or root / "graph.html"

    nodes, edges, clusters = collect(root)
    tpl = (pathlib.Path(__file__).resolve().parent / "graph_template.html").read_text(encoding="utf-8")
    html = tpl.replace("/*__DATA__*/", json.dumps(
        {"nodes": nodes, "edges": edges, "clusters": clusters,
         "repo": root.parent.name}, ensure_ascii=False))
    out.write_text(html, encoding="utf-8")

    bridges = sum(1 for e in edges if e["bridge"])
    orphans = [n["id"] for n in nodes if n["deg"] == 0]
    print(f"已生成 {out}")
    print(f"  {len(nodes)} 个节点，{len(edges)} 条边（{bridges} 条跨簇的桥），{len(clusters)} 个簇")
    if len(clusters) > 4:
        print(f"  簇超过 4 个，第 4 个起统一用中性灰——节点标签和簇名标签仍然区分得开")
    if orphans:
        print(f"  孤儿节点（图上会被推到边缘）：{', '.join(orphans)}")


if __name__ == "__main__":
    main()
