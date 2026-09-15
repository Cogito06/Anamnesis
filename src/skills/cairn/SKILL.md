---
name: cairn
description: 把本次会话里挣来的理解归档成片段，存进仓库的 cairn/ 目录并重建索引（Anamnesis 系统）。Use this whenever the user types /cairn, finishes working through a hard concept or problem, says things like 记一下 / 存档 / 这个要记住 / 别忘了, or is warned that context is about to be compacted. Also use it proactively when a learning discussion has clearly resolved something the user was stuck on — that understanding evaporates at the next compaction unless it is written down, so prompt the user rather than letting it vanish.
---

# Cairn —— 垒一块路标

把本次会话里**值得未来的用户看到**的东西，写成片段存进 `cairn/`。

石堆不是地图。它不告诉你全貌，只在你可能走错的岔路口说一句「这边」。
片段也一样：它不复述教科书，只标记用户摔过的那个坑。

## 第 0 步：确认这是一个 cairn 仓库

检查当前工作目录下 `cairn/INDEX.md` 是否存在、首行是否为 `<!-- cairn:v1 -->`。

**不存在** → 问用户「这个文件夹还不是 cairn 仓库，要初始化吗？」。
同意后只创建这两样：

```
cairn/
├── INDEX.md        # 内容就一行：<!-- cairn:v1 -->  加一个标题，其余交给脚本
└── fragments/
```

**不要重排或改动仓库里任何已有的文件和目录。** 用户的学习仓库用的是课程自带的骨架
（`slides/ hw/ lab/ proj/` 之类），那个结构是他熟悉的，`cairn/` 是唯一的新增物。

## 第 1 步：回顾并筛选

回看本次会话，列出候选片段，然后逐条过**质量闸门**：

| 情况 | 处理 |
|---|---|
| 内容在课程材料 / 教科书里查得到 | **存指针，不存内容**——写进 `refs`，正文不复述 |
| 既没有卡点、也没有 insight | **丢弃**，不要为了凑数留 |
| 只是复述了你（agent）给出的正确答案 | **丢弃**，那是你的输出，不是用户的认知轨迹 |

留下的每条都要能回答：

> 三个月后的用户读到它，会得到什么书里没有的东西？

答不上来就丢掉。这道闸门是整个系统能否长期可用的关键：索引是常驻上下文，
每混进一条教科书摘要，未来每一轮对话都要为它付 token，而它的检索价值是负的——
它会挤掉真正有用的条目，让人不如直接翻书。放水一次，信噪比就永久降一格。

**最有价值的素材依次是**：卡住又解开的地方、被推翻的误解、书上没写的跨章节连接、
用户自己的记号约定、还没搞懂的问题。

## 第 2 步：提议，不要写盘

把筛选结果列成表，**此时一个文件都不要创建**：

```
建议归档 N 条：

1. [id] 标题
   卡点：（一句话）
   insight：（一句话）
   钩子：（准备写进索引的那句话）
   遗留：（如果有）

已丢弃 M 条：（各一句话说明理由，让用户有机会捞回来）
```

然后停下等用户砍、改、补。这一步不能省——用户对自己认知轨迹的判断比你准，
而且他记得哪些是真卡过、哪些只是顺口聊到。你从对话记录里分不出这个差别。

## 第 3 步：落盘

用户确认后，按 `${CLAUDE_SKILL_DIR}/assets/fragment-template.md` 的结构写入
`cairn/fragments/<YYYY-MM-DD>-<短横线-slug>.md`。

写作要求：

- **用用户自己的话和记号**，不要改写成教科书腔。他认得出自己的语言，认不出百科腔
- `concepts` 中英术语都写（`[保角变换, conformal map]`），否则 grep 会漏
- `卡点 / 误解` 要写清楚**错误的想法本身**，不只是正确答案。复用价值全在这里——
  正确答案书上有，而「我为什么会那样想错」只有这里有
- `hook` 字段是索引里唯一显示的那句话，认真写。它要让未来的 agent 判断
  「该不该展开读这个片段」：写「保角变换的性质」是失败的钩子，
  写「误以为保调和性来自链式法则，实际根源是 CR 方程」才是
- 遗留问题用 `- [ ]` 前缀，脚本和 hook 都靠它识别

## 第 4 步：重建索引

**跑脚本，不要手写索引**：

```bash
python ${CLAUDE_SKILL_DIR}/scripts/rebuild_index.py cairn
```

索引是片段的纯派生物。手写迟早会漏条目，而漏掉的那条会**静默地**从检索里消失——
片段还在磁盘上，但没人再找得到它。让脚本从磁盘重新推导，这种错误就不可能发生。

脚本会重排序、重算每条的 `open:N`、统计总数，并在超过 200 条时提醒该分片了。
如果它报告某个片段缺 `hook` 字段，回去补上再跑一次。

## 第 5 步：报告

告诉用户：新增几条、索引现共几条、当前未解决问题几个。

如果这次有片段的遗留问题被解决了，提醒用户把对应片段的 `status` 改成 `resolved`
并划掉那个 `- [ ]`——未解决问题列表每次开会话都会注入，留着已经解决的会稀释它。
