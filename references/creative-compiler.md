# Creative Compiler — 双编译总纲（General Track + Creative Track）

**加载时机：** 📍 Pass 0 Step 0.1b 判定 `creative` 后加载本文件，作为 Creative Track 全程的路由总纲。

***

## 为什么需要双编译架构

General Compiler 编译的是**能力**（Role + Workflow + Knowledge + State），产物是一个"知道怎么做"的 skill。

但创造型任务（写作/文案/广告/脚本/品牌/Naming/IP）的核心不是"知道怎么做"，而是**判断**：

> 专家和普通人的差距，不在于会不会写，而在于：能判断哪个方案更好、知道哪里不对、以及怎么改。

所以 Creative Compiler 的编译对象不是 Prompt，而是 **Creative Capability**：

```
General Skill  = 知道（Know）
Creative Skill = 知道 + 会判断（Judge）+ 会否决（Reject）+ 会改进（Improve）
```

**判断回路（judgment + revision）是从"会模仿"到"会创作"的分水岭，因此是 Creative IR 的必填字段。**

**完整闭环（v3.1）：**

```
Understand → Model → Create → Judge → Revise → Evaluate → Learn
   C1/C2      IR      DIVERGE   JUDGE   CRITIQUE/    C5      LEARN
                      DIVERGE           REVISE              （Memory≠Learning）
```

**Creative Skill 的最终定义（v3.2）：**

```
Creative Skill = Context + Knowledge + Style(实测) + Principles
               + Decision Policy + Examples + Anti-patterns
               + Generation(边际收益发散) + Judgment + Revision + Learning
```

五层分工（缺任何一层，Compiler 不成立）：

| 层 | 解决的问题 | 载体 |
|----|-----------|------|
| IR | 我知道什么 | Creative IR（18+ 字段 + measurements 证据） |
| Decision Policy | 我怎么选 | policy（priorities/tradeoffs/decision_rules/exceptions/risk_tolerance） |
| Runtime | 我怎么做 | 判断回路状态机（13+1 态，含 LEARN） |
| Evaluator | 我做得怎么样 | 五层评估 + 独立评价 + benchmark_runner |
| Learning | 下一次怎么更好 | capability_delta → mutation_proposal → 双门 |

```
Creative Compiler = Extraction × Representation × Decision × Execution × Evaluation × Learning
```

**North Star Metric（编译器演进的唯一北极星）：**

> **"这个 Compiler 编译出来的 Skill，到底是不是比原来的 Skill（或 Legacy prompt）更会创作？"**

一切架构决策以该问题的可实证性为准。`scripts/benchmark_runner.py` 是其度量载体（见 §Benchmark Runner）。继续堆 IR 字段与 reference 之前，先回答这个问题——架构漂亮但能力增量不足时，方向是补证据，不是补文档。

***

## Step 0.1b — 编译目标分类路由

Pass 0 Step 0.1（是否值得编译）通过后，执行编译目标分类：

| 信号                                  | 判定                                        | 编译轨道                                                          |
| ----------------------------------- | ----------------------------------------- | ------------------------------------------------------------- |
| 输入是流程/规则/知识/工具使用（代码审查、API 文档生成、工作流） | `procedural` / `knowledge` / `analytical` | **General Track**（Pass 1-6）                                   |
| 输入的核心产出是**原创内容**（文案、脚本、故事、命名、视觉概念）  | `creative`                                | **Creative Track**（Pass C1-C5）                                |
| 主体为创作但含流程性环节（如"写小红书笔记 + 排版发布规范"）    | `creative`（hybrid）                        | **Creative Track**，流程环节按 General 规范内化为 constraints.contextual |
| 主体为流程但偶尔输出内容（如"周报生成器"）              | `procedural`                              | **General Track**，写作要求内化为模板                                   |

### 判定依据（按优先级）

1. **产出是否需要判断力** — 输出有没有"好坏之分"且标准模糊？周报无判断力需求（模板即可），标题有（同一信息 10 种写法高下立判）→ creative
2. **风格是否是产物的一部分** — 用户会评价"像不像他/像不像这个品牌"吗？是 → creative
3. **是否存在"专家否决记录"** — 源材料里有"这个不行/太用力了/删掉"类内容？是 → creative 的强信号
4. **混合时看主体** — 判断失误的代价：creative 任务走 General Track 会得到一个"能写但不会判断"的模板化 skill（最常见失败模式）；procedural 任务走 Creative Track 会过度设计。**宁可 hybrid 判 creative，不可反向**

分类结果写入 IR：`meta.type`（九类 creative 细分见 creative-ir-schema.json）+ `meta.compilation_mode`。

***

## Creative Track 管线

```
Source (Prompt / PDF / Video / 访谈 / 范例集 / 旧 Skill)
  → [Pass I: Ingestion — 共享] 
  → [Pass 0: Triage — 共享，含 Step 0.1b 路由]
  → Pass C1: Understand   意图 + 场景解析
  → Pass C2: Extract      创造能力抽取（五提取器）
  → Pass C3: Design       判断回路设计 + Runtime Profile  → 产出 Creative IR
  → Pass C4: Generate     生成 Creative Skill Package
  → [Pass 5: Optimize — 共享，条件执行]
  → Pass C5: Evaluate     创意五层诚实评估
```

| Pass              | 职责                                                                                  | 核心产出                                                                                                | 详情                                                                     |
| ----------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **C1 Understand** | Resolved Intent（表面请求 vs 真实创作意图）+ Context Model（人/品牌/受众/平台/市场）                       | `intent` + `context` 字段                                                                             | 📍 [creative-extraction.md](creative-extraction.md) §1-2               |
| **C2 Extract**    | 语义分块 + 五提取器：Principle / Style / Example / Anti-pattern / Heuristic（含 Constraint）    | `style`(含 fingerprint) + `principles` + `examples` + `anti_patterns` + `heuristics` + `constraints` | 📍 [creative-extraction.md](creative-extraction.md) §3-7               |
| **C3 Design**     | 判断回路配置（dimensions/weighting/penalties + revision 策略）+ 发散配置 + Runtime Profile + 输出契约 | 完整 Creative IR，过 `validate_creative_ir.py` 门控                                                       | 本文件 §Creative IR 构建 + [creative-runtime.md](creative-runtime.md) §配置映射 |
| **C4 Generate**   | IR → Skill Package：SKILL.md（入口契约）+ runtime workflow + style/principles/examples 分文件 | Creative Skill Package                                                                              | 本文件 §产物结构                                                              |
| **C5 Evaluate**   | 五层评估：Structural / Semantic / Creative（风格保真 + 判断回路有效性）/ LLM Preference Proxy / Human Preference（可选采集）                  | 评分 + GO/NO-GO                                                                                       | 本文件 §评估                                                                |

**共享机制（Creative Track 复用，不重复实现）：**

* Pass I Ingestion — 多源摄取 + 溯源 + 置信度（OCR/转写等级直接喂给 C2 证据分级）

* 证据分级 — creative 版采用 origin 四级（explicit/inferred/heuristic/generated），与 General 的 primary/secondary/inferred 平行

* 诚实边界 — confidence < 0.6 时强制声明材料不足（C3 判定，C5 验证）

* 元反思 — C3 Decision Gate 处执行 8 维度自省（quick 模式跳过）

* Token 预算 / 平台 profile — 语义与 General Track 一致

***

## Creative IR 构建

📍 完整 Schema：[schemas/creative-ir-schema.json](../schemas/creative-ir-schema.json)（Pass C3→C4 Decision Gate 强制校验）

### 构建顺序（依赖关系）

```
C1: intent ← 用户真实意图（非表面任务）
    context ← 人/品牌/受众/平台/市场（同一主题不同场景完全不同）
C2: style.fingerprint ← 运行 scripts/style_analyzer.py 实测语料（v3.1，禁止手填）
    style.measurements + style.style_confidence ← 分析器自动产出（v3.2：逐维 value/sample_size/confidence/measurement 证据）
    style.fingerprint_provenance ← 分析器自动产出（tool/method/corpus_size/measured_at）
    principles ← 原文直引优先，每条必带 source_refs + priority
    examples ← before/after > contrastive > positive > negative
    anti_patterns ← 必带 detection_signals + correction（否则无法进判断回路）
    heuristics ← 承载"太用力了"式模糊经验：信号→倾向→纠正
C3: judgment.dimensions ← 从 intent.success_criteria + principles 派生（禁空洞维度）
    judgment.weighting ← 键与 dimensions 一一对应，和 = 1.0；禁止无理由的均匀分配
    policy ← 冲突裁决规则：priorities（dimension+数值 priority）/ tradeoffs（when 对象：dimension_a×dimension_b@context + tolerance）
             / decision_rules（action 枚举 keep/revise/reject/explore_more）/ exceptions / risk_tolerance / rejection_reasons
             ——从源材料的取舍记录提取："他为什么放弃好看的那个"；advertising/branding/naming 必备（缺或空 tradeoffs 校验器 FAIL）
    revision ← max_rounds 按任务价值定（普通 1-3，高价值 3-5）；rejudge_isolation=true；marginal_gain_threshold（默认 0.15）
    generation.divergence ← min/target/stop_when_marginal_gain_below（边际收益发散）
    learning ← 可选：capability_deltas（target/operation/magnitude/evidence）→ mutation_proposals → 双门配置
    runtime_roles ← 可选：标注每个顶层字段的运行时角色（缺省用 §映射表）
    runtime_profile ← 按 meta.type 查 §Runtime Profile 基准表
```

### 关键构建规则

1. **Style Fingerprint 禁止凭印象填（v3.1 落地为工具链）** — 执行 `python3 scripts/style_analyzer.py <语料文件...> --json fingerprint.json`，fingerprint 与 fingerprint_provenance 一起进 IR。没有语料就降低 confidence 并在诚实边界声明，不许编造。full 模式缺 provenance 会被校验器 WARN（#9）。
2. **原则 ≠ 约束** — "标题不能超过20字"是 constraint（硬边界），"先让读者感受到问题，再给答案"是 principle（创作哲学）。混放会导致判断回路把哲学当规则机械执行。
3. **示例必须有 explanation** — 没有解释的示例只是语料。价值排序：专家修改前→修改后 ＞ A/B 对比 ＞ 单纯好例。
4. **编译器推断不能伪装成专家原话** — 每条知识的 source\_refs.origin 必须如实标注。inferred/heuristic 占比过高 → confidence 相应下调。
5. **无反例的创造型 skill 必然模板化** — examples.negative 和 anti\_patterns 至少提供一个，源材料没有就从用户处索取或在诚实边界声明。
6. **冲突取舍是专家判断力的最高密度区（v3.1）** — 源材料中的取舍记录（"两个都好，但他选了 B，因为…"）编译为 policy.tradeoffs。没有取舍记录时 policy 可缺省，但 advertising/branding/naming 三类必须从用户处索取或以 heuristic 标注生成（校验器 #10 WARN）。
7. **字段齐全主义警报（v3.1）** — IR 每个顶层字段应能回答"运行时谁消费它"。纯 documentation 字段应显式标注（runtime_roles），否则 Pass 5 O10 有权瘦身。默认映射见 §IR 字段 runtime_role 映射表。

### Pass C3→C4 Decision Gate

Creative IR 落盘为 JSON 时，执行：

```bash
python3 scripts/validate_creative_ir.py <creative-ir.json>
```

退出码 0 才进 C4。校验覆盖：判断回路必填性（dimensions ≥3 / weighting 一致 / revision 就位）、Style Fingerprint 六项核心指标 + **逐维测量证据（V1：full 模式缺 style.measurements → FAIL，裸数字不可验证）**、溯源闭环（source\_refs.document\_id 必须在 provenance 登记）、**Capability 检查（#5 空洞维度 FAIL / #6 均匀权重 / #7 空洞原则 / #8 不可操作检测信号 / #10 三类高决策型缺 policy 或无 tradeoffs FAIL）**、policy/learning/runtime_roles/divergence 边际收益字段结构。未落盘时按 schema 必填字段清单逐项核对。

**V1-V6 Capability Validation 对照（v3.2）：**

| # | 检查项 | 级别（full 模式） |
|---|--------|-----------------|
| V1 | Style 存在真实测量证据（style.measurements：value+measurement 必填） | 缺失 FAIL；quick WARN |
| V2 | Decision Policy 有 Trade-off（三类高决策型） | 缺 policy 或空 tradeoffs FAIL |
| V3 | Evaluator 与 Generator 解耦（revision.rejudge_isolation） | false FAIL |
| V4 | Revision 具备 Stop Condition（stop_conditions 或 marginal_gain_threshold） | 两者皆缺 WARN |
| V5 | Novelty 与 Diversity 分开 | 指标定义层（本文件 §C5），静态不查 |
| V6 | Learning 具备 Regression Gate（upgrade_gate.benchmark_required） | false FAIL |

***

## Runtime Profile 基准表

不同创意类型需要不同运行策略。C3 设计阶段按 `meta.type` 查此表定基准，再按源材料特征微调：

| type             | creativity | style\_dep | context\_dep | knowledge\_dep | iteration\_dep | judgment\_dep |
| ---------------- | ---------- | ---------- | ------------ | -------------- | -------------- | ------------- |
| creative-writing | 0.7        | **0.95**   | 0.8          | 0.5            | 0.9            | 0.8           |
| copywriting      | 0.7        | 0.7        | 0.8          | 0.6            | 0.7            | 0.8           |
| advertising      | 0.9        | 0.4        | 0.9          | 0.7            | 0.8            | **0.95**      |
| script           | 0.8        | 0.7        | 0.9          | 0.6            | 0.8            | 0.85          |
| branding         | 0.75       | 0.3        | **1.0**      | **0.95**       | 0.7            | **1.0**       |
| naming           | **0.95**   | 0.4        | 0.9          | 0.6            | **0.95**       | 0.9           |
| founder-ip       | 0.7        | 0.9        | 0.95         | 0.7            | 0.8            | 0.85          |
| visual-concept   | 0.85       | 0.6        | 0.8          | 0.5            | 0.8            | 0.8           |

读法：Writing 重风格迭代（style\_dep + iteration\_dep 高）；Naming 重发散+判断；Brand Strategy 重上下文+判断（creativity 反而中等——策略的创造力受约束驱动）。Runtime 据此自动决定发散量/评审强度/案例参考量。

***

## 产物结构（Creative Skill Package）

```
<skill-name>/
├── SKILL.md              # 入口契约：路由 + Creative Workflow 概览 + 质量维度声明
├── references/
│   ├── style.md          # Style Grammar + Fingerprint（实测值 + fingerprint_provenance）
│   ├── principles.md     # 原则 + rationale + 适用条件
│   ├── heuristics.md     # 信号→倾向→纠正
│   ├── anti-patterns.md  # 检测信号 + 纠正方向
│   ├── policy.md         # Creative Policy：取舍/决策规则/例外/一票否决（v3.1，有 policy 时）
│   ├── runtime.md        # 判断回路规范（Judge决策→Critique→Revision + LEARN）
│   ├── strategy.md       # 创意策略链（Problem→Tension→Insight→Territory→Angle，可选）
│   └── constraints.md    # 四分类约束（hard/soft/contextual/creative）
├── examples/
│   ├── positive.md       # 含 explanation
│   ├── negative.md       # 含 explanation（强烈建议）
│   └── contrastive.md    # A/B 对比 + before/after（最高价值）
├── templates/
│   └── output.md         # 输出契约模板（format/sections/platform rules）
├── tests/
│   ├── golden-set.md     # 评估基准：期望特征与方向，非标准答案（≥3 条，人读）
│   ├── benchmark-cases.json  # 机器可读 Golden Set（v3.1，benchmark_runner 消费，含 fingerprint 断言）
│   └── adversarial.md    # 对抗用例：模糊修正请求 → 期望的 fingerprint 局部调整
└── honest-boundaries.md  # 诚实边界（confidence 低时强制声明材料不足）
```

**SKILL.md 只是 Runtime 的入口契约**——真正的创作行为（发散→判断→修订）发生在 runtime.md 定义的判断回路里。

📍 判断回路的运行时规范：[creative-runtime.md](creative-runtime.md)

***

## IR 字段 runtime_role 映射表（v3.1 缺省值）

字段齐全主义的解药：每个 IR 字段标注运行时角色——只做 documentation 不参与任何运行时决策的字段，Pass 5 O10 有权瘦身。IR 未显式声明 `runtime_roles` 时用此缺省映射：

| 字段 | runtime_role | 消费者 |
|------|-------------|--------|
| intent | routing, judgment | UNDERSTAND（意图路由）、JUDGE（success_criteria→dimensions） |
| context | generation, judgment | CONTEXTUALIZE/BRIEF、Consistency 检查 |
| knowledge | generation, judgment | BRIEF 注入领域事实 |
| style | generation, judgment, evaluation | DIVERGE 生成引导、Style Drift 检测、C5 style_fidelity |
| principles | judgment, revision | JUDGE Observe、Critique Why |
| heuristics | judgment | JUDGE 信号触发 |
| constraints | routing, judgment | FILTER 硬约束、constraint_violation penalty |
| examples | generation | DIVERGE 参考锚点 |
| anti_patterns | judgment, revision | 检测信号 penalty、Critique 数据源 |
| creative_strategy | generation | STRATEGIZE/DIVERGE 发散轴 |
| generation | generation | DIVERGE 边际收益参数 |
| policy | judgment | JUDGE 决策层（一票否决/tradeoffs/decision_rules） |
| judgment | judgment | JUDGE 兜底评分 + pairwise |
| revision | revision | CRITIQUE→REVISE→COMPARE 协议 |
| memory | judgment, evaluation | DIVERGE 降权、Failure Memory 对照 |
| learning | evaluation | LEARN 状态（feedback→vNext 双门） |
| output | routing | FINALIZE 输出契约 |
| runtime_profile | routing | 运行策略强度（发散量/评审强度） |
| provenance | documentation | 审计（不进运行时决策路径） |

***

## Pass C5 — 创意五层评估（v3.1 诚实分层）

| Layer | 检查 | 方法 | 诚实声明 |
| ----- | --- | ---- | -------- |
| **L1 Structural** | 格式/约束/输出契约 | 同 General Layer A，机械可测 | 完全可靠 |
| **L2 Semantic** | 任务是否完成（intent.success\_criteria 逐条） | 逐条核对 | 高可靠 |
| **L3 Creative** | 风格保真度 + AI 腔率 + Novelty + **判断回路有效性（独立评价下的 Revision Gain）** | style\_analyzer 实测指纹对比 + 套路簇检测 + 模拟运行一轮判断回路 | 中可靠（词表启发式 + 独立性受同模型限制） |
| **L4 LLM Preference Proxy** | 成对比较偏好（产物 A vs 旧版/基线） | pairwise 比较 | **这是模型偏好，不是人类偏好**——LLM preference 与 human preference 在广告/命名/人设类任务上经常不一致，只作参考信号 |
| **L5 Human Preference**（可选） | 真人偏好数据 | 真实数据采集层：产物投产后的人工选择/采纳率/编辑距离反馈，回流 learning.feedback\_log | 唯一终审。**不能被 LLM 代替**——采集不到时诚实标注"未经人类偏好验证"，而非用 L4 冒充 |

> v3.0 的 "Human-proxy" 名称说过头了，v3.1 更正为 LLM Preference Proxy 并显式分层。禁止把 L4 结果表述为"人类偏好"。

**Layer 3 的核心指标：**

```
style_fidelity    = 1 - style_distance（generated fingerprint vs target fingerprint，实测基准）
anti_pattern_rate = 命中 anti-pattern 的候选占比
revision_gain     = independent_post_score - initial_score（独立评价，Judge B 信息隔离）
```

`revision_gain ≈ 0` 说明判断回路没真正发挥作用——修订只是重新抽卡，产物应判 CONDITIONAL 并回 C3 检查 critique/revision 配置。**非独立评价下的 revision_gain 不可作为判断回路有效的证据（Evaluator Leakage）。**

**完整指标枚举（9 项，v3.1 拆分 Originality）：**

| # | 指标 | 归属 Layer | 说明 |
|---|------|-----------|------|
| 1 | Task Fit | L2 | intent.success_criteria 逐条达成 |
| 2 | Style Fidelity | L3 | 实测指纹距离 → 保真度 |
| 3 | **Novelty** | L3 | **新颖度，三参照系**（v3.1 修正）：距品类套路簇（"30岁以后才知道…"式结构模板，即使文字不同）+ 距通用 AI 模式（anti_patterns/ai_pattern_risk）+ 距源示例（examples，防高级复述）。三系都近 = 陈词滥调 |
| 4 | **Diversity** | L3 | **发散有效性**（v3.1 从"Originality"更名）：候选间最小距离——同母题换说法 = 0 分。注意：Diversity 高 ≠ Novelty 高（三个彼此不同但都很普通的方案，Diversity 满分、Novelty 零分），二者不可互相冒充 |
| 5 | Specificity | L3 | 具体度（对应 fingerprint.concreteness 方向） |
| 6 | Consistency | L3 | 人设/品牌一致性（context 与产物的矛盾检测） |
| 7 | Anti-pattern Rate | L3 | 反模式命中率 |
| 8 | LLM Preference | L4 | 模型成对偏好（proxy，非人类偏好） |
| 9 | Revision Gain | L3 | 判断回路有效性（独立评价） |

**Novelty 的三参照系（v3.1 定义 / v3.2 可执行）：**

```
Novelty = f( 距 Category Conventions（品类套路簇）
           , 距 AI Common Patterns（通用模板/AI 腔）
           , 距 Source Examples（源示例集） )
```

- 品类套路簇 = 该内容类型的高频结构模板（"作为创业者我想说/今天给大家分享/你是否也有这样的困扰"）——命中即 Novelty 大幅降分，即使候选彼此差异很大
- 候选间最小距离只证明 Diversity，不证明 Novelty——**Candidate Distance ≠ Originality**，这是 v3.0 的定义错误，v3.1 修正
- **v3.2 可执行化**：`scripts/novelty_detector.py` 输出四值——`candidate_novelty`（vs 同批候选）/ `category_novelty`（vs `scripts/category_patterns.json` 套路库，五类可扩展）/ `corpus_novelty`（vs 源语料实测指纹）/ `overall_novelty`。它能抓住"没抄任何一句但整体很套路"；诚实边界：测的是结构套路命中密度，非语义原创性

### Golden Set（评估基准）

创造没有唯一标准答案，Golden Set 存的是**期望特征与期望方向**，不是标准答案：

```yaml
test:
  input: "写一个关于第一次创业失败的开场"
  expected:
    tone: restrained
    perspective: first_person
    abstractness: low
    emotional_explicitness: low
```

产物 skill 包必须含 `tests/golden-set.md`（≥3 条，人读）**和 `tests/benchmark-cases.json`（机器可读同构版，v3.1）**，C5 Layer 2/3 以此为基准逐条核对，benchmark\_runner 消费 JSON 版执行自动对比。

### Benchmark Runner（v3.2 可执行能力层）

Golden Set 是测试定义，Benchmark Runner 把它变成可执行的对比。**这是 North Star Metric 的度量载体**——回答"Creative 编译产物是否比 Legacy prompt / 旧版 skill 更会创作"：

```bash
# 1. 用各版本（原 Prompt / Legacy Skill / Creative v3.0 / Creative v3.1+）跑全部 case，
#    每版本输出到独立目录 results/<label>/{case_id}.md
# 2. 多版本对比（第一个 --variants 为基线）
python3 scripts/benchmark_runner.py \
    --cases <skill>/tests/benchmark-cases.json \
    --variants legacy=results/legacy/ v30=results/v30/ v31=results/v31/ \
    --ir <skill>/creative-ir.json \
    --category xiaohongshu \
    --report benchmark-report.json
# 旧双版本 CLI（--baseline + --candidate）仍兼容
```

- Runner 是构建时分析器，不执行 LLM 调用——只消费各版本已生成的输出，用 style\_analyzer 实测指纹、扫描 anti-pattern 命中、核对 golden 断言（含 qualities/constraints）、计算 category\_novelty（`--category` 提供时，词表来自 `scripts/category_patterns.json`）
- 产出：各版本指标矩阵 + 基线 vs 最新版 delta + **capability\_gain**（North Star：`最新版正向指标均值 - 基线`，不是"最新版自评多少分"）+ per-case 明细
- **Runner 不自动下"显著更好"的结论**——delta 规模与样本量由人判断；LLM/Human Preference（L4/L5）不在 Runner 范围，需另行采集
- 使用时机：① 编译器版本升级的回归测试；② Learning Loop 的 Mutation Gate（learning.upgrade\_gate.benchmark\_required，V6 硬门）；③ 向用户证明编译价值

### Benchmark 四组协议（Justin 实验模板，v3.2）

验证 Compiler 核心机制只需一个 skill（推荐 justin-writing-style，不急于扩展类型）。四组同题对比：

| 组 | 内容 | 说明 |
|----|------|------|
| A | 原 Prompt 裸跑 | 无结构基线 |
| B | Legacy Skill（v3.0 之前的产物/旧 skill） | 有结构无判断回路 |
| C | Creative v3.0 产物 | 判断回路但无 v3.1+ 机制 |
| D | Creative v3.1+/v3.2 产物 | 完整能力层（实测指纹/policy/独立评价） |

控制变量：同一模型、同一组输入、同一上下文、同样输出长度；样本 ≥ 60 cases；Runner 跑 A/B/C/D 四版本矩阵。**重点看 D 是否明显胜 C**——若不明显，依次排查（勿说"还需要更多字段"）：① Style Analyzer 是否提供了新信息 ② Decision Policy 是否参与实际决策 ③ Judge 是否识别专家偏好 ④ Critique 是否有效诊断 ⑤ Revision 是否真改善（独立 gain）⑥ Benchmark 是否测得到差异。人类 Pairwise（A vs B / B vs C / C vs D）另行采集为 L5 数据。

### 对抗测试（Adversarial Creative Test）

用模糊修正请求冲击产物 skill 的风格稳定性——这类请求最容易触发 Style Drift：

```
"再高级一点" / "再有感染力一点" / "更有网感" / "更炸裂"
```

**PASS 标准：** Runtime 将模糊修正解释为 fingerprint 的**局部参数调整**（如 emotional_explicitness +0.1），而非整体重写风格。解释失败 = Style Drift 防御缺失 → C5 判 CONDITIONAL。

### 回归测试（Compiler 自身演进）

编译器升级（v3.0 → v3.1）后，对同一 benchmark-cases.json 重新编译两版产物，跑 Benchmark Runner 对比：

```
style_fidelity / anti_pattern_rate / golden_pass_rate
```

任一指标显著退化 → 本次编译器变更回退。"修了一个能力，毁掉另一个能力"是编译器演进最常见的失败。

**Verdict 规则与 General Track 一致**（≥85 GO / 60-84 CONDITIONAL / <60 NO-GO），但 Layer 3 不达标直接 CONDITIONAL 起步。

***

## 与 General Track 的产物互操作

* Creative Skill Package 与 General Skill Package 结构兼容（SKILL.md + references/ + templates/），可被同一宿主平台加载

* Creative skill 被二次编译（作为 skill\_package 输入合并）时：style/principles/examples 作为知识进入 knowledge\_inventory，judgment/revision 配置作为能力进入 capability\_graph，走 General Track 的合并规则（统一 Context + 能力去重）

