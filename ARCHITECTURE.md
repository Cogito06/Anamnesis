# Anamnesis

> 柏拉图的「回忆说」：学习不是获取新知，而是回忆灵魂本已知道的东西。
> 这套系统用回忆对抗遗忘——把会话里挣来的理解，在 `/compact` 抹掉它之前垒成路标。

| | |
|---|---|
| 系统名 | **Anamnesis** |
| 每个学习仓库里的目录 | **`cairn/`** —— 玛尼堆、敖包那种路标石堆 |
| 归档命令 | **`/cairn`** —— 垒一块石头 |
| 状态 | **Phase 1 已建成并通过验收**（2026-09-14） |

石堆不是地图。它不告诉你全貌，只在你可能走错的岔路口说一句「这边」。
这正是片段该起的作用：不复述教科书，只标记你摔过的那个坑。

---

## 0. 设计约束

来自对 `E:\Cogito006\cs61b` 实际使用习惯的观察，不是凭空设定：

1. **不发明目录结构。** cs61b 用的是课程上游骨架（`core/ disc/ hw/ lab/ proj/ slides/ library-sp24/`）。
   每门课结构都不同，系统不能要求统一形状。
2. **课程材料和个人产出是交错的。** `hw/hw2/inputFiles/` 是发的，`hw/hw2/src/` 是自己写的，
   同一棵子树。因此**无法按目录划分读写权限**。
3. **当前学习不产出书面记录。** 整个 cs61b 仓库只有一个 `.txt`，零篇笔记。
   认知轨迹完全存在于对话里，`/compact` 一到就蒸发。这是系统要补的缺口。
4. **要能在任意文件夹使用**，不是单个仓库的专属配置。

## 1. 总体形状

**机制装在用户级，数据长在项目级。**

```
~/.claude/                              安装一次，全局生效
├── settings.json                       hooks 注册（增量合并，未覆盖原有配置）
├── skills/cairn/
│   ├── SKILL.md                        /cairn 命令（104 行）
│   ├── assets/fragment-template.md     片段模板
│   └── scripts/rebuild_index.py        从片段推导 INDEX.md
├── hooks/
│   ├── cairn-lib.sh                    公共函数
│   ├── cairn-session-start.sh          开局注入索引
│   ├── cairn-precompact.sh             压缩前提醒
│   └── cairn-session-end.sh            收尾提醒
└── anamnesis-state/                    会话 stamp，用于判断本次是否已落盘

E:\Cogito006\cs61b\                     学习仓库 A —— 结构完全不变
├── core/ disc/ hw/ lab/ proj/ slides/         ← 课程自带，系统不碰
└── cairn/                              ← 唯一新增
    ├── INDEX.md
    └── fragments/

E:\...\math-physics\                    学习仓库 B —— 结构随它自己
└── cairn/
```

一次安装，N 个学习仓库。知识库跟着仓库走，可 commit、可换机器、可单独分享。

**为什么不用 Claude Code 原生 memory**：它在 `~/.claude/projects/<slug>/memory/`，
即仓库**外**。核心诉求是「把学习经历转化为持续存在、可调用的包」，那就得能跟着仓库走。

### 激活判据

hook 检查 `<cwd>/cairn/INDEX.md` 首行是否含魔术标记：

```
<!-- cairn:v1 -->
```

**不看目录名**——`cairn` 是个通用词，某个真实项目也可能有同名目录，只看名字会误激活。
有标记则注入，没有则**静默退出**。这是「不干扰非学习项目」的实现。

## 2. 片段 —— 存储单元

`cairn/fragments/2026-09-14-conformal-only-laplace.md`

```markdown
---
id: 2026-09-14-conformal-only-laplace
course: math-physics          # 日后按学科分化 agent 的切分依据
concepts: [共形映射, conformal map, Laplace 方程, Helmholtz, Dirichlet 能量]
hook: 以为共形映射能简化任意二维 PDE，实际只对 Δu=0 有效，因为 Δ(u∘f)=|f'|²(Δu)∘f
refs:
  - slides/Lecture 9.pdf
  - hw/hw03.md#p2
status: open                  # open | resolved
---

## 触发
hw03 第二题把上半平面的 Dirichlet 问题映到单位圆盘。做完顺手想：
那 Helmholtz 方程也这么映一下，是不是也能化简？

## 卡点 / 误解
我一直把共形映射当成「把区域变简单」的通用工具，对任何二维 PDE 都能用。
不是。它只对 **Δu = 0** 有效，全部关键在这个恒等式（f 解析）：

    Δ(u∘f) = |f'|² · (Δu)∘f

右边是原方程乘一个**处处为正的标量因子**，所以：

- `Δu = 0` → 两边乘 |f'|² 还是 0，保住了
- `Δu = ρ` → 变成 Δ(u∘f) = |f'|²·(ρ∘f)，源项被 |f'|² 扭曲，已经不是原来的 Poisson 问题
- `Δu + k²u = 0` → 最糟。Δ 项带 |f'|²，k²u 项不带，
  变成 Δ(u∘f) + |f'|²k²·(u∘f) = 0 —— **常系数变成了变系数**，方程结构直接破了

所以共形映射保的不是「PDE」，是「齐次 + 只有二阶主部」这个很窄的形状。
它不是坐标变换的万能技巧，是 Laplace 方程的专属特权。

## 关键 insight
同一个 |f'|² 因子还管着另一件事：**Dirichlet 能量的共形不变性只在二维成立**。

梯度那边贡献 |∇(u∘f)|² = |f'|²·|∇u∘f|²，体积元那边 dV' = |f'|ⁿ dV，
n 维下两者的比值留下 |f'|^(2-n) 的权重——**只有 n = 2 时正好抵消**。

这才是共形映射法是二维专属技术的根本原因，不是「三维太难算」。
n ≥ 3 时 Liouville 定理说共形映射就只剩 Möbius 变换那么几个；
而且即使用它们，调和性也得靠 Kelvin 变换 u ↦ |x|^(2-n)u(x/|x|²) 的权重才保得住，
不再是简单复合。

课本把「共形映射解 Laplace」和「Dirichlet 原理」分在两章，这层联系被切断了。

## 遗留问题
- [ ] Helmholtz 变成 Δv + |f'|²k²v = 0 之后，|f'|² 取什么特殊形式时还可解？
      感觉和「Helmholtz 能分离变量的那几套坐标系」是同一件事
```

| 字段 | 为什么 |
|---|---|
| `触发` | 检索时的场景线索。三个月后靠概念名想不起来，靠场景能 |
| `卡点 / 误解` | **全文价值最高**。人在同一个坑反复摔，而这是教科书必然没有的内容 |
| `refs` | 指针，不是内容。避免系统退化成教科书的有损压缩版 |
| `遗留问题` | 「学习助手」区别于「知识库」之处：让系统反推着你走，而不只是被查询 |
| `hook` | 索引里唯一显示的那句话。它决定未来的 agent 要不要展开读这个片段 |
| `concepts` | 中英术语并存，否则 grep 会漏 |
| `course` | Phase 3 分化学科 agent 用，现在只存不用 |

### 质量闸门

写在 `SKILL.md` 里，是系统能否长期可用的关键：

- 能在课程材料里查到的 → **存指针，不存内容**
- 没有卡点、也没有 insight → **丢弃**
- 只是复述 agent 给的正确答案 → **丢弃**，那不是你的认知轨迹

每条必须能回答：*三个月后的我读到它，会得到什么书里没有的东西？*

放水一次，索引的信噪比就永久下降一格。

## 3. 索引 —— 常驻层

`cairn/INDEX.md` 一行一条，**是钩子不是标题**：

```
- [conformal-only-laplace] 共形映射/conformal map/Laplace/Helmholtz — 以为共形映射能简化任意二维 PDE，实际只对 Δu=0 有效，因为 Δ(u∘f)=|f'|²(Δu)∘f | open:1 | 09-14
```

破折号后那句要让 agent 能判断「该不该展开读」。
写「共形映射的性质」是失败的钩子，写「以为能简化任意 PDE，实际只对 Δu=0 有效」才是。

**索引是片段的纯派生物，不是手写文档。** 由 `scripts/rebuild_index.py` 从
`fragments/` 的 frontmatter 完全重新推导——钩子句存在片段的 `hook` 字段里，
`open:N` 由正文的 `- [ ]` 实时统计。

这样索引永远不可能和片段不同步。让模型凭记忆手写索引，漏掉一条是迟早的事，
而漏掉的那条会**静默地**从检索里消失：片段还在磁盘上，但再也没人找得到它。

- 一行约 40 token。一学期 30–60 条 ≈ 1.5–2.5k token，常驻可接受
- 阈值 **200 条 / 32KB**，超了脚本和 hook 都会提示按 `course` 分片。现在分片是过度设计
- **整体重写，不追加**。稳定前缀命中 prompt cache，零散追加会反复打掉它

## 4. 写路径 —— 三档触发

| 档 | 挂载点 | 行为 |
|---|---|---|
| 主 | `/cairn` | 语义边界，手动打 |
| 兜底 | `PreCompact` hook | 只提醒，不阻塞 |
| 收尾 | `SessionEnd` hook | 本次没落盘就提醒 |

**为什么主触发不能是 compact**：compact 边界是随机的语义切点，会把话题从中间切开；
且上下文 90% 满时 agent 状态最差，最容易输出正确但没用的摘要。
`PreCompact` 在能力上也做不了主力——它拿不到 `additionalContext`，
**没有把内容写回对话的通道**，只能发 `systemMessage` 或 exit 2 阻塞。它天生是个闹钟。

两个提醒 hook 都会先查「本次会话是否已落盘」（比对 `anamnesis-state/<sid>.stamp`
与 `fragments/` 的 mtime），已落盘就闭嘴，不啰嗦。

**`/cairn` 流程**（人在环里）

```
/cairn
  → 验魔术标记（没有 → 问要不要初始化）
  → 回顾会话，过质量闸门
  → 列提议表，一个文件都不写      ← 你在这里砍和改
  → 写 fragments/*.md
  → 跑 rebuild_index.py 重建 INDEX.md
```

第三步不能省——你对自己认知轨迹的判断比 agent 准。

## 5. 读路径 —— 注入指针，不注入内容

`SessionStart` 注入 `additionalContext`（纯文本 stdout 即可），开局给三样：

1. `INDEX.md` 全文 + 条数
2. 所有 `- [ ]` 未解决的遗留问题（上限 30 条）
3. 一句使用指令：讨论到索引里已有的主题，先读片段全文再往下推

**注入的是索引，不是片段内容。** agent 看钩子自己决定要不要展开。
这比向量检索稳——选择过程可解释、可调试，召回错了你看得见。

**白捡的好处**：`SessionStart` 的 `reason` 取值是 `startup|resume|clear|compact|fork`，
**compact 之后也会触发**。压缩一发生索引立刻重新注入——
IDEA.md 里担心的「compact 后忘掉一切」，读路径这一侧是自愈的。

实现细节：cwd 从 stdin 的 JSON 取，用 sed 解析（**Windows 下没有 jq**），
Windows 路径的 `\` 还原成 `/`。两种路径形式都已验证。

## 6. 权限

原计划用 `permissions.deny` 硬隔离只读材料目录，**因约束 2 作废**——
材料与产出交错在同一棵树，按目录切会连带禁掉「帮我改 hw 代码」这种正当用途。

改为：`cairn/` 是 agent 自由写区，其他路径照常走权限提示。
需要保护的目录在**单个仓库**的 `.claude/settings.json` 里按需加，不放用户级。

写规则时的陷阱：**必须写 `Edit(slides/**)`，不能写 `Write(...)`**。
Claude Code 只用 `Edit(path)` 和 `Read(path)` 做文件权限检查，
`Write` / `NotebookEdit` / `MultiEdit` 的路径规则会被接受但**永不生效**（仅启动时告警）。

## 7. 完整循环

**Session 1**
SessionStart 注入（库空）→ 聊共形映射，卡在「为什么 Helmholtz 映过去就烂了」→ 聊通 → `/cairn`
→ agent 提议 3 条，你砍掉 1 条纯教科书复述的 → 落盘 2 条 + 重建 INDEX

**Session 2（两周后）**
SessionStart 注入 INDEX + 1 个 open question
→ 你问「三维的 Dirichlet 问题能不能也这么映过去」
→ agent 从钩子判断需要细节 → 读 `conformal-only-laplace.md`
→ **不重新推导 |f'|² 恒等式**，直接答「只有 n=2 时梯度和体积元的因子才抵消」，
  并接上那个还开着的 Helmholtz 遗留问题

省下的不是压缩带来的 token，是「不用第二次解释同一件事」——
而且质量更高，因为它知道你的误解史。

## 8. Token 账

| 项 | 成本 | 频率 |
|---|---|---|
| INDEX 常驻 | 1.5–2.5k（一学期规模） | 每轮，但命中 prompt cache |
| `/cairn` 一次 | 3–5k | 每个语义边界 |
| recall subagent（Phase 2） | 主上下文 +500，子上下文 15k 一次性 | 每次检索 |

对照组是「不做这件事」：每个新会话重新解释同一批概念，5–10k token 且质量更差。

## 9. Phase 2：检索 subagent（未建）

解决「导入太多反而降低讨论质量」。

subagent 有独立上下文窗口，grep 和文件读取全留在它自己的上下文里，
**只有最终结论回主对话**。

```
主对话 ──派发──> recall subagent（tools: Read, Grep, Glob）
                  读 20 个候选，自己烧 15k token
       <──返回── ≤500 token 结论 + 片段 id
主对话只涨 500
```

**片段少于约 20 条时这是负收益**：agent 直接从 INDEX 开文件更快更准。等库长起来再建。

同期还要评估 `UserPromptSubmit` 指针注入（能注入也能改写输入，但每轮都跑，
容易变噪声源）和索引分片。**都得等两周真实数据**——现在设计等于瞎猜笔记长什么样。

## 10. Phase 3：按学科分化 agent（待定）

数学 / 物理 / CS 各自的 recall 策略与讨论风格。片段 schema 的 `course` 字段已为此预留。

## 11. 已核实的技术事实

| 事实 | 影响 |
|---|---|
| `PreCompact` 不能注入 `additionalContext`，只能 `systemMessage` / exit 2 | 它只能当闹钟，做不了主触发 |
| `SessionStart` / `UserPromptSubmit` 能注入；纯文本 stdout 即被当作上下文 | 索引注入的挂载点 |
| `SessionStart` 在 `reason=compact` 时也触发 | 压缩后索引自动重注入 |
| 所有 `SessionEnd` hook 共享 **1.5 秒**总预算 | 该 hook 只能做几次 stat |
| subagent 上下文隔离，只有最终结论回主对话 | recall 机制成立的前提 |
| 文件权限只认 `Edit(path)` / `Read(path)`，`Write(path)` 规则永不生效 | 写 deny 规则时的陷阱 |
| deny 由 Claude Code 进程执行而非模型自觉，且不需 workspace trust | 隔离是硬的 |
| skills 已取代 commands 文件；支持附属文件与会话内热重载 | `/cairn` 用 skill 实现 |
| skill 的 description 是触发的唯一依据，且模型倾向**漏触发** | description 写得主动、列足触发语境 |
| skill 附属文件按 `scripts/` `references/` `assets/` 三分 | 模板进 assets，脚本进 scripts |
| Python 在 Windows 控制台输出中文需 `reconfigure(encoding='utf-8')` | 否则脚本回显乱码 |
| 环境无 jq，有 Python 3.14 | hook 用 sed 解析 JSON |
| settings.json 改动会被热重载，无需重启 | 但 SessionStart 要新会话才触发 |

来源：https://code.claude.com/docs/en/hooks · /sub-agents · /permissions · /settings · /slash-commands

## 12. Phase 1 验收记录（2026-09-14 全部通过）

| 关卡 | 标准 | 结果 |
|---|---|---|
| 注入生效 | cairn 仓库开会话能看到索引 | PASS（576 字节） |
| **静默生效** | 子目录 / 本仓库 / cs61b / 家目录均无输出 | PASS ×4 |
| 路径解析 | 转义反斜杠与正斜杠两种形式都能解析 | PASS |
| 提醒生效 | 未落盘时 PreCompact 发合法 JSON | PASS |
| **不啰嗦** | 已落盘后 PreCompact / SessionEnd 静默 | PASS |
| 状态清理 | SessionEnd 清除 stamp | PASS |
| 索引重建 | 3 个片段 → 正确排序、`open:N` 正确、缺 `hook` 报警告 | PASS |

尚未验证（需新会话）：真实 SessionStart 注入、`/cairn` 端到端落盘、跨会话引用。

## 13. 未决

- [ ] 在 cs61b 初始化 `cairn/`（只新增目录，不碰已有文件）—— 待确认
- [ ] 仓库改名 `learning-helper` → `anamnesis`（需在会话外做，改 cwd 会断当前会话）
- [ ] `PreCompact` 是否需要真阻塞选项（当前：不阻塞）
- [ ] 跑满两周后复盘：片段实际长什么样、索引钩子够不够用、是否该建 recall subagent
