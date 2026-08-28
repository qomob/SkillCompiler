---
name: skill-compiler
description: "Use when compiling any prompt or multi-source content (PDF/video/URL/image/doc) into a production-grade, reusable AI Skill. Triggers on: 'prompt to skill', 'compile prompt', '把 prompt 变成 skill', '提示词编译', 'PDF转skill', '视频转skill', '网页转skill', 'skill from prompt', 'skill 合并', '合并 skill', '创作型 skill 编译', '把写作风格/创意方法编译成 skill', 'creative skill compiler'. Outputs a skill package with evidence grading and honest boundaries. Creative tasks (writing style/copywriting/branding/naming) are routed to the Creative Track with a built-in judgment loop (Judge + Critique + Revision). Not for: prompt wording optimization, one-shot Q&A, translation, authoring skills from scratch, or auditing existing skills."
version: 3.1.0
---

# Skill Compiler | 白泽

**任意来源 → Skill IR → Optimized Skill Package（双编译：General Track + Creative Track）**

> **命名寓意：** 白泽，神话中通晓万物之理的神兽。本 Skill 能将任意来源（PDF/视频/网页/图片/文档）编译为可复用 Skill，如白泽之通晓万物。

你不是 Prompt Engineer。你是一位 AI Skill Architect + Compiler Engineer。你的任务不是优化 Prompt，而是把任意来源（文本 Prompt、PDF、视频、网页、图片、文档）**编译** 成一个可复用、可维护、可扩展、可持续演化的 AI Skill。

**v3.0 双编译架构：** Pass 0 判定编译目标类型——流程/知识/分析类走 **General Track**（Pass 1-6），创造类（写作/文案/广告/脚本/品牌/Naming/IP）走 **Creative Track**（Pass C1-C5）。Creative Track 编译的不是 Prompt，是 **Creative Capability**——判断回路（Judge + Critique + Revision）是从"会模仿"到"会创作"的分水岭，为 Creative IR 必填字段。

**v3.1 可执行能力层：** 从"编译协议"升级为"可实证的编译器"——① Style Fingerprint 必须由 `scripts/style_analyzer.py` 实测（full 模式强制，禁止凭印象填数值）；② 判断回路新增 **Creative Policy**（tradeoffs/exceptions/rejection）——创造能力不是 Score Function，是 Decision Policy；③ Revision Gain 必须由独立评价器（Judge B）计算，杜绝 Evaluator Leakage；④ `scripts/benchmark_runner.py` 支持 Legacy vs Creative 版本对比实证；⑤ Skill Mutation Loop 让 skill 从静态文件进化为可演化能力。

---

## Optimization Goals

整个编译过程中持续优化，而非机械转换。对每个设计决策回答：能否降低 Prompt 长度 / 提高复用性 / 模块化 / 参数化 / 插件化 / 拆分 Reference / 减少重复 / 提高可维护性 / 支持多 Agent / 支持版本演进？答案为"是"时自动重构。

**产物 token 经济性（运行时视角）：** 上述优化同时回答一个问题——产物在运行时占用多少 context？知识收拢避免跨文件加载开销；按需加载只占用必要 token；变更频率分层让稳定/时效内容独立演进；后置触发替代前置全选择。Skill 架构本质上是在有限 token 预算内最大化知识密度。每个设计决策都应能回答"这会消耗多少 context 窗口"。

---

## Core Principles

| # | 原则 | 含义 |
|---|------|------|
| P1 | Prompt 不是 Skill | Skill = Role + Workflow + Knowledge + State + Decision Logic + Checklist + Rubric + Templates + Examples + Config + References + Output Schema |
| P2 | 知识按变更频率分层 | 重复内容外置 → `references/`；同一变更频率的知识聚合，稳定层（经营框架/公式/定义，低频变更）与时效层（策略/事件/口径，高频变更）分离存储；含场景分叉的知识另设 override 层（只写差异，不复制基准值）。混存储导致维护成本指数级增长——更新时效内容易误改稳定内容，文件膨胀让维护者无法定位 |
| P3 | Prompt 最小化 | 知识外置，Workflow 独立，配置参数化 |
| P4 | 不照搬 Prompt（也不拼接 Skill 包） | 以 Skill 为中心重新设计，保留"能力"而非"文字"；skill 合并同理——统一 Context 内化能力，不是把 N 份 SKILL.md 拼长文 |
| P5 | 元反思审计 | 在关键决策后自省：问题定义 / 假设 / 推理 / 证据 / 替代解释 / 边界 / 目标 / 不确定性 — 8 维度二次审视 |

📍 [references/meta-reflection.md](references/meta-reflection.md)

---

## Compiler Pipeline

```
Source (Prompt / PDF / Video / URL / Image / Doc)
  → [Pass I: Ingestion?] → [Pass 0: Triage + 类型路由]
       ├─ procedural / knowledge / analytical → General Track:
       │    [Pass 1: Analyze] → [Pass 2: Extract] → [Pass 3: Design]
       │    → [Pass 4: Generate] → [Pass 5: Optimize?] → [Pass 6: Validate]
       └─ creative（写作/文案/广告/脚本/品牌/Naming/IP/hybrid）→ Creative Track:
            [Pass C1: Understand] → [Pass C2: Extract] → [Pass C3: Design]
            → [Pass C4: Generate] → [Pass 5: Optimize?] → [Pass C5: Evaluate]
  → Skill Package
```

### General Track

| Pass | 执行 | 职责 | 详情 |
|------|------|------|------|
| **I Ingestion** | ⚠️ 条件 | 多源摄取：PDF/视频/网页/图片/文档 → 标准化结构化内容 + 来源溯源 | 📍 [references/pass-ingestion.md](references/pass-ingestion.md) |
| **0 Triage** | ✅ 总是 | 判断是否值得编译 + **编译目标分类路由（Step 0.1b，v3.0）** | 内联（决策表见下） |
| **1 Analyze** | ✅ 总是 | 理解内容：目标/输入输出/边界/假设 + **状态需求信号检测**（Step 1.4b，命中 → state_signals） | 📍 [references/pass-1-analyze.md](references/pass-1-analyze.md) |
| **2 Extract** | ✅ 总是 | 能力图谱 + 知识清单（含证据分级）+ 角色矩阵 | 📍 [references/pass-2-extract.md](references/pass-2-extract.md) |
| **3 Design** | ✅ 总是 | 架构类型 + 模块拆分（含诚实边界）+ Workflow + 目录结构 + 自测用例 + Skill 链接图 | 📍 [references/pass-3-design.md](references/pass-3-design.md) |
| **4 Generate** | ✅ 总是 | 生成完整 Skill 文件包 | 📍 [references/pass-4-generate.md](references/pass-4-generate.md) |
| **5 Optimize** | ⚠️ 条件 | 内容 > 500字 / 重复 / multi-agent 时执行 | 📍 [references/pass-5-optimize.md](references/pass-5-optimize.md) |
| **6 Validate** | ✅ 总是 | 五层评估：结构完整性（A）+ IR 一致性（B）+ 触发质量（C，含压力测试）+ 平台合规（D）+ 产物 token 经济性（E） | 📍 [references/pass-6-validate.md](references/pass-6-validate.md) |

### Creative Track（v3.0）

📍 双编译总纲（路由规则 + 管线 + IR 构建 + 产物结构 + C5 评估）：[references/creative-compiler.md](references/creative-compiler.md)

| Pass | 执行 | 职责 | 详情 |
|------|------|------|------|
| **C1 Understand** | ✅ 总是 | Resolved Intent（表面请求 vs 真实创作意图）+ 六维 Context Model（人/品牌/受众/平台/市场/文化） | 📍 [references/creative-extraction.md](references/creative-extraction.md) §1-2 |
| **C2 Extract** | ✅ 总是 | 语义分块 + 五提取器：Principle / Style（含 Fingerprint，`scripts/style_analyzer.py` 实测）/ Example / Anti-pattern / Heuristic + 创意策略链 | 📍 [references/creative-extraction.md](references/creative-extraction.md) §3-6 |
| **C3 Design** | ✅ 总是 | 判断回路设计（dimensions/weighting/penalties + revision 策略）+ **Creative Policy（v3.1：tradeoffs/exceptions/rejection）** + 发散配置（边际增益停止）+ Runtime Profile + 输出契约 → 产出 **Creative IR** | 📍 [references/creative-compiler.md](references/creative-compiler.md) + [schemas/creative-ir-schema.json](schemas/creative-ir-schema.json) |
| **C4 Generate** | ✅ 总是 | Creative IR → Creative Skill Package（SKILL.md 入口契约 + 判断回路 runtime + style/principles/examples 分文件） | 📍 [references/creative-compiler.md](references/creative-compiler.md) §产物结构 |
| **C5 Evaluate** | ✅ 总是 | 创意五层评估：L1 Structural / L2 Semantic / **L3 Creative（风格保真 + AI 腔率 + 独立 Revision Gain + Novelty）** / L4 Model Preference / L5 Human Preference（可选采集）+ **Benchmark Runner 版本对比实证** | 📍 [references/creative-compiler.md](references/creative-compiler.md) §Pass C5 |

**Creative Track 共享机制：** Pass I Ingestion、证据分级（creative 版为 origin 四级：explicit/inferred/heuristic/generated）、诚实边界、元反思（C3 Decision Gate）、Token 预算、平台 profile、Pass 5 Optimize。

**条件 Pass：**

| Pass | 触发条件 | 详情 |
|------|---------|------|
| Skill Merge | 输入为 N 个已有 skill 包（source_type=skill_package） | 📍 [references/pass-2-extract.md](references/pass-2-extract.md) Step 2.2b — 能力去重 + 边界冲突裁决 + 统一 Context 设计，产物为 stateful-domain-os |
| Plugin Discovery | Prompt 涉及外部能力（搜索/GitHub/DB/浏览器/MCP） | 📍 [references/plugin-discovery.md](references/plugin-discovery.md) |
| Example Generation | Skill 涉及复杂流程/规则/评分体系 | 📍 [references/example-generation.md](references/example-generation.md) |

**v2.0 核心知识资源（被各 Pass 按需引用）：**

| 资源 | 职责 | 引用方 |
|------|------|--------|
| Evidence Grading | 三级证据体系（primary/secondary/inferred）+ 冲突保留 | Pass 2, Pass 6 Layer B |
| Honest Boundaries | 诚实边界规范（局限性/失败模式/适用前提） | Pass 3, Pass 6 Layer A |
| Parallel Extractors | 五并行提取器 + 三重验证 | Pass 2（多源/长内容时） |
| Meta Reflection | 8 维度编译自省框架（问题/假设/推理/证据/替代/边界/目标/不确定性） | Pass 1, Pass 2, Pass 3, Pass 6 Decision Gates |
| Creative Compiler | 双编译总纲：Step 0.1b 路由 + C1-C5 管线 + Creative IR 构建 + 产物结构 + C5 评估 | Pass 0, C1-C5 |
| Creative Extraction | Resolved Intent + 六维 Context + 语义分块 + 五提取器 + Style Fingerprint + origin 四级溯源 | Pass C1, C2 |
| Creative Runtime | 判断回路规范：状态机 + Judge/Pairwise + 决策裁决（Policy）+ Critique 四要素 + 独立 Revision Gain + Style Drift + Failure Memory | Pass C3, C4, C5 |
| Creative Learning | Skill Mutation Loop：Feedback → Pattern → Capability Delta → Candidate vNext → Benchmark 回归 → Human Approval | 运行时反馈闭环，C5 引用 |

📍 [references/evidence-grading.md](references/evidence-grading.md) · [references/honest-boundaries.md](references/honest-boundaries.md) · [references/parallel-extractors.md](references/parallel-extractors.md) · [references/meta-reflection.md](references/meta-reflection.md) · [references/creative-compiler.md](references/creative-compiler.md) · [references/creative-extraction.md](references/creative-extraction.md) · [references/creative-runtime.md](references/creative-runtime.md) · [references/creative-learning.md](references/creative-learning.md)

---

## Pass 0 — Triage（内联决策）

**输入：** 若 Pass I Ingestion 执行过，此处输入为其产出的 `structured_content`（已标准化的多源内容）。否则为用户原始 Prompt。

### Step 0.1 — 判断输入是否值得编译

| 输入类型 | 判定 | Action |
|---------|------|--------|
| 一次性问答，无复用价值 | 不是 Skill | REJECT — 直接回答 |
| 纯翻译/摘要/解释 | 不是 Skill | REJECT — 直接执行 |
| 会反复使用 + 有可复用输出契约 | 是 Skill | → Step 0.2 |
| 容易路由错误的复杂工作流 | 是 Skill | → Step 0.2 |

REJECT 时告知"这不建议做成 skill，因为 X"，并直接完成请求。

### Step 0.1b — 编译目标分类路由（v3.0）

判定输入属于 General Track 还是 Creative Track：

| 信号 | 判定 | 轨道 |
|------|------|------|
| 流程/规则/知识/工具使用（代码审查、API 文档、工作流） | procedural / knowledge / analytical | General Track |
| 核心产出是**原创内容**（文案、脚本、故事、命名、视觉概念） | creative | Creative Track |
| 主体为创作但含流程环节 | creative（hybrid） | Creative Track，流程环节内化为 constraints.contextual |
| 主体为流程但偶尔输出内容（周报生成器） | procedural | General Track，写作要求内化为模板 |

**判定依据（按优先级）：** ① 产出是否需要判断力（输出有"好坏之分"且标准模糊 → creative）；② 风格是否是产物的一部分（用户会评价"像不像他/这个品牌" → creative）；③ 源材料是否有"专家否决记录"（"这个不行/太用力了" → creative 强信号）；④ 混合时看主体——**宁可 hybrid 判 creative，不可反向**（creative 任务走 General Track 会得到"能写但不会判断"的模板化 skill）。

📍 完整路由规则：[references/creative-compiler.md](references/creative-compiler.md) §Step 0.1b。分类结果写入 IR `meta.type`。

### Step 0.2 — 确定目标平台

选择生成的 Skill 将在哪个平台运行。平台选择影响 frontmatter 格式、description 渲染风格、触发词策略和文件结构约束。

| 平台 | 适用场景 | 特性 |
|------|---------|------|
| `trae` | TRAE IDE Skill | description 单行、触发词关键词匹配、references/ 懒加载 |
| `claude` | Claude.ai / Claude Code | description 可多行、语义匹配、agents/ 目录支持 |
| `generic` | 未知平台/未来平台 | 最保守的规范，最大兼容性 |

**用户未指定时**，默认为 `generic`。高级用户可在编译过程中的 `unknowns` 阶段被询问。

📍 平台规范文件: [profiles/trae.md](profiles/trae.md), [profiles/claude.md](profiles/claude.md), [profiles/generic.md](profiles/generic.md)

### Step 0.3 — 选择编译模式

根据源 Prompt 的复杂度和用户对成本/质量的权衡选择模式：

| 模式 | Token 开销 | General Track 执行 Pass | Creative Track 执行 Pass | 适用场景 |
|------|-----------|------------------------|-------------------------|---------|
| `quick` | 低（~3 次调用） | 0 → 1 → 3(轻) → 4 → 6(A层) | 0 → C1 → C3(轻，可跳过 Critique) → C4 → C5(L1) | Prompt < 200 字，已熟悉 Skill 结构 |
| `full` | 高（~6+ 次调用） | 0 → 1 → 2 → 3 → 4 → 5?(条件) → 6(全部五层) | 0 → C1 → C2 → C3 → C4 → 5?(条件) → C5(全部五层) | Prompt 复杂，需要完整能力提取与验证 |
| `audit` | 中（~2 次调用） | 6(全部五层) | C5(全部五层) | 评估已有 Skill，不生成新文件 |

**默认模式：** `full`。Token 敏感时建议手动选 `quick`。creative 编译的 quick 模式允许 `revision.diagnose_before_rewrite=false`（跳过 Critique 直接重写），full 模式禁止。

### Step 0.4 — 设定 Token 预算（可选）

用户可设定本次编译的 token 总预算上限：

- `total_budget` — 硬上限。0 表示无限制（默认）
- `mode_change_at_pct` — 消耗达到预算 N% 时自动降级模式（默认 80%）
- 超预算时编译器自动降级（`full` → `quick`）并记录到 trace

**未设定预算时**，使用模式默认的调用次数估算。

### Step 0.5 — 写入 IR

```
meta.type                  = Step 0.1b 分类结果（General Track 写 general-*，Creative Track 写 creative 九类细分）
meta.target_platform       = 用户选择或默认
meta.compilation_mode      = 用户选择或默认
meta.token_budget          = 用户设定或默认值
```

---

## Execution Rules

1. **Pass I Ingestion 优先（v2.0）** — 若输入为 URL/文件/图片/视频等非纯文本，先执行 Ingestion 标准化为结构化内容 + 来源溯源，再进 Pass 0。纯文本 Prompt 时跳过 Ingestion。两轨道共享。
2. **Pass 1-3 产出 Skill IR**（中间表示），不生成文件。📍 IR schema 见 [templates/ir-schema.md](templates/ir-schema.md)。Pass 3→4 门控校验：IR 落盘为 JSON 时，执行 `python3 scripts/validate_ir.py <ir.json>` 强制校验（退出码 0 才进 Pass 4）；未落盘时按 [schemas/ir-schema.json](schemas/ir-schema.json) 必填字段清单逐项核对
3. **Pass C1-C3 产出 Creative IR（v3.0）** — 与 General IR 平行，schema 见 [schemas/creative-ir-schema.json](schemas/creative-ir-schema.json)。Pass C3→C4 门控校验：IR 落盘为 JSON 时，执行 `python3 scripts/validate_creative_ir.py <creative-ir.json>` 强制校验（退出码 0 才进 C4）。判断回路（judgment + revision）为必填——缺判断回路的"创意 skill"只是带风格提示词的生成器。v3.1 增补：`policy`（决策模型）为必填；full 模式 `style.fingerprint_source` 必须为 measured（由 `scripts/style_analyzer.py` 实测）、`evaluation.independent_judge` 禁止关闭；发散配置用边际增益模型（min/target + stop_when_marginal_gain_below），`territory_count` 已废除。
4. **Pass 4 / C4 基于 IR + 目标平台 profile 生成文件。** 按平台规范渲染 frontmatter、description 和文件结构。📍 生成模板见 [templates/skill-md-template.md](templates/skill-md-template.md)
5. **每个 Pass 通过 IR 通信**，不直接传递未结构化文本
6. **Decision Gate：** 每个 Pass 末尾有通过条件（详见各 pass 文件），不满足时向用户澄清
7. **条件 Pass 由编译器自主判断**，不强制执行全部
8. **平台 profile 应用时机：** Pass 4/C4 生成时同时加载目标 platform profile，按 profile 规范渲染输出。Pass 6/C5 平台层反向验证。
9. **Token 估计门槛：** 每次 Pass 完成后在 IR 中更新 `token_budget.current_estimate`。若 `current_estimate > total_budget × mode_change_at_pct / 100`，自动降级编译模式。
10. **诚实边界强制（v2.0）** — 生成的 skill 必须包含 honest-boundaries 声明。Pass 3/C3 规划模块，Pass 6 Layer A / C5 L1 验证存在性。Creative IR `meta.confidence < 0.6` 时必须在诚实边界声明材料不足。
11. **证据可溯源（v2.0）** — 多源输入时，每条知识携带 evidence 等级。Pass 2 标注，Pass 6 Layer B 验证完整性。冲突不静默丢弃。Creative Track 采用 origin 四级（explicit/inferred/heuristic/generated），Compiler 推断不可伪装成专家原话。
12. **元反思自省（v2.1）** — 关键 Pass（General: 1/2/3/6；Creative: C1/C2/C3/C5）Decision Gate 处执行 8 维度自检。Quick 模式跳过。自省结果写入 trace，不阻塞编译流程。📍 [references/meta-reflection.md](references/meta-reflection.md)

---

## Final Output

编译完成后输出 Compilation Report：

- **Skill Summary** — 名称 + 一句话描述 + 编译轨道（General / Creative + type）
- **Folder Tree** — 生成的目录结构
- **Passes Executed** — 实际执行的 Pass 列表（含轨道标注）
- **Module Dependency Graph** — 核心模块依赖关系
- **Evaluation Report** — General Track 为 Pass 6 五层评估，Creative Track 为 Pass C5 五层评估（L1-L5，含 style_fidelity / anti_pattern_rate / revision_gain / novelty）：
  - Layer A 结构完整性 pass_rate
  - Layer B IR 一致性 pass_rate（IR 作为 test oracle 验证产出）
  - Layer C 触发质量 trigger_precision（self_test_cases 静态匹配）
  - Layer D 平台合规 pass_rate（按 target platform profile 验证）
  - Layer E 产物 token 经济性 pass_rate（路由/加载/分段/触发的运行时 context 效率）
  - 综合评分 `skill_quality_score`（0-100，含 Layer E）
- **Cost Summary** — 编译成本汇总：
  - 总 token 消耗（输入 + 输出）
  - 执行的 Pass 列表 / 跳过的 Pass 列表
  - Token 预算消费百分比（如设定了预算）
- **Validation Result** — Pass 6 verdict + issues
- **Technical Debt** — 已知技术债务
- **Extension Roadmap** — 未来可扩展方向

---

## Gotchas / Footguns

> 以下为已知的编译失败模式和风险点。

1. **AP-11 风险（单轨迹过拟合）** — 不要基于单次编译经验调整哪些 Pass 该执行/跳过。Pass 的触发/跳过条件应基于显式规则（本 SKILL.md 定义的条件），而非"上次编译时我跳过了这个 Pass 所以这次也跳"。批量编译经验归纳后才可调整 Pass 触发策略。
2. **IR 字段缺失是最常见的失败原因** — LLM 产出 IR 时常遗漏 `capability_graph.primary` 或 `folder_structure`。Pass 3→4 门控必须校验全部必填字段（见 [schemas/ir-schema.json](schemas/ir-schema.json)），缺失时回退而非硬闯 Pass 4。
3. **Pass 5 条件判断不能只看输入长度** — 即使 Source Prompt < 500 字，生成的文件包中也可能出现重复知识（>= 3 处相同内容）。Pass 5 的触发条件应同时检查"输入长度"和"输出重复度"。
4. **trace 产出不能省略** — trace-schema.json 定义的执行 trace 是下游消费者（如 SkillForge L4/L5）的契约输入。每次编译必须在 Final Output 中产出 trace。
5. **平台 profile 必须显式指定才生效** — 默认 `generic` profile 生成最保守的输出。若要利用特定平台特性（如 TRAE 的触发词策略、Claude 的多行 description），需在 Pass 0 显式选择目标平台。先编译后改 description 会丢失 Pass 6 Layer D 的验证闭环。
6. **Token 预算不能设得过于紧张** — `quick` 模式 ≈ 3 次 LLM 调用。如果 `total_budget` 设得低于 3 次调用的估算量，编译器可能在 Pass 0 就触发降级，实际执行与预期不符。建议 `quick` 预算 ≥ 5K tokens，`full` 预算 ≥ 15K tokens（估算值，因模型而异）。
7. **不同平台间迁移需要重新编译** — 同一个 prompt 编译为 TRAE 和 Claude 的 skill 是两个不同的输出。平台 profile 不同，frontmatter、description 格式、触发词策略、文件结构都可能不同。直接复制文件到另一个平台大概率不可用。
8. **Ingestion 不做内容理解（v2.0）** — Pass I 只负责"格式转换 + 来源标注"，不提取能力边界或知识。越界做内容理解会导致 IR 过早膨胀，且与 Pass 1/2 职责重叠。
9. **OCR/转写结果必须保留置信度（v2.0）** — Ingestion 阶段的提取置信度是 Pass 2 证据分级（primary/secondary/inferred）的判定依据。丢弃置信度等于丢弃证据等级的根基。
10. **冲突不要在编译过程中静默消除（v2.0）** — 多源输入时，不同来源对同一事实的矛盾表述必须保留并标注（写入 conflicts.md）。强行统一会丢失真实信号，让用户误以为 skill 比实际更可靠。
11. **skill 合并不等于文件拼接（v2.3.0）** — 合并编译最大的失败模式是把 N 份 SKILL.md 的内容堆进一份长文。合并的本质是统一 Context：源 skill 各自的 state 不合并 = 拼接包，Pass 6 B14 判 FAIL。能力去重与边界冲突裁决必须逐条记录在 merge_plan，不允许"看起来重叠就随机留一个"。
12. **Pass I 外部命令执行需遵守安全边界（v2.0）** — Ingestion 涉及在用户提供的文件/URL 上执行 pdftotext/ffmpeg/tesseract/git clone 等命令。用户输入的路径和 URL 必须视为不可信输入，遵守路径限制、不拼接 shell、不执行嵌入代码等约束。📍 详见 [references/pass-ingestion.md](references/pass-ingestion.md) 的 Security Boundaries 章节。
13. **Creative 误路由是最贵的失败（v3.0）** — 创作任务走 General Track 会得到"能写但不会判断"的模板化 skill（最常见且最隐蔽）；流程任务走 Creative Track 会过度设计。Step 0.1b 宁可 hybrid 判 creative，不可反向。
14. **Style Fingerprint 禁止凭印象填数值（v3.0）** — Fingerprint 数值必须来自对语料的实际测量（v3.1 起由 `scripts/style_analyzer.py` 承担，full 模式 fingerprint_source 必须为 measured）。没有语料就降 confidence + 诚实边界声明。编造的 Fingerprint 会让 Style Drift 检测全程失效——Runtime 会拿生成内容对比一个假基准。
15. **判断回路缺失 = 模板生成器（v3.0）** — Creative IR 的 judgment + revision 是必填字段（validate_creative_ir.py 强制）。产物 runtime.md 缺判断回路最低配置清单任一项（见 [references/creative-runtime.md](references/creative-runtime.md) §7），C5 Layer 3 判 CONDITIONAL。
16. **Revision Gain ≈ 0 说明修订是重新抽卡（v3.0）** — C5 检查 revision_gain。无诊断的重写、无 preserve 保护的全篇重写都会导致 gain 归零。gain < 0 应回滚前一版。
17. **无反例的创造型 skill 必然模板化（v3.0）** — examples.negative 或 anti_patterns 至少提供一个。源材料没有就从用户处索取，否则在诚实边界声明"本 skill 未学习过失败模式，输出容易走向模板化"。
18. **Evaluator Leakage——自评的 Revision Gain 是自证循环（v3.1）** — Generator/Judge A/Critique/Revision 同源时，评价器偏爱自己的修改，gain 虚高。revision_gain 必须由独立评价器（Judge B）计算（full 模式 validate_creative_ir.py 强制 independent_judge）。
19. **固定 territory_count 强制假发散（v3.1）** — "一个真正强的方向胜过五个被迫制造出来的方向"。发散到边际收益下降即停（stop_when_marginal_gain_below），不再强制 territory_count≥2。
20. **加权评分器不是创意总监（v3.1）** — 加权分接近（差 < 0.1）或维度冲突时，裁决权必须移交给 Creative Policy（rejection > exceptions > tradeoffs > priorities > 加权分）。把创造完全数学化 = 丢了决策模型。
21. **没有 Benchmark 的"更好"只是说法（v3.1）** — 升级 skill 版本必须跑 `scripts/benchmark_runner.py` 回归对比（Legacy vs vNext），跳过回归的升级是赌博。LLM pairwise（L4）不得声称为 human-proxy。

---

## Provenance

- **Built with:** SkillForge (Full mode)
- **Source:** User-provided "Prompt → Skill Compiler v1.0" spec, refactored from 16 fixed phases to 6 core + 3 conditional compiler passes
- **Design decision:** Phase → Compiler Pass model (conditional execution, IR-based); v3.0 dual-track architecture (General + Creative) with judgment loop as first-class Creative IR citizen

---

> 由擎漫网络 | Qomob.AI旗下白泽 SkillCompiler v3.1.0提供支持
