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
  → Pass C5: Evaluate     创意五层评估（L1-L5）+ Benchmark 对比
```

| Pass              | 职责                                                                                  | 核心产出                                                                                                | 详情                                                                     |
| ----------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **C1 Understand** | Resolved Intent（表面请求 vs 真实创作意图）+ Context Model（人/品牌/受众/平台/市场）                       | `intent` + `context` 字段                                                                             | 📍 [creative-extraction.md](creative-extraction.md) §1-2               |
| **C2 Extract**    | 语义分块 + 五提取器：Principle / Style / Example / Anti-pattern / Heuristic（含 Constraint）    | `style`(含 fingerprint) + `principles` + `examples` + `anti_patterns` + `heuristics` + `constraints` | 📍 [creative-extraction.md](creative-extraction.md) §3-7               |
| **C3 Design**     | 判断回路配置（dimensions/weighting/penalties + revision 策略）+ **Creative Policy（tradeoffs/rejection）** + 发散配置 + Runtime Profile + 输出契约 | 完整 Creative IR，过 `validate_creative_ir.py` 门控                                                       | 本文件 §Creative IR 构建 + [creative-runtime.md](creative-runtime.md) §配置映射 |
| **C4 Generate**   | IR → Skill Package：SKILL.md（入口契约）+ runtime workflow + style/principles/policy/examples 分文件 | Creative Skill Package（含 golden-set.json）                                                                      | 本文件 §产物结构                                                              |
| **C5 Evaluate**   | 五层评估：Structural / Semantic / **Creative（风格保真 + AI 腔率 + 独立 Revision Gain + Diversity + Novelty）** / Model Preference / Human Preference（可选） | 评分 + GO/NO-GO + benchmark report（可执行实证）                                                                  | 本文件 §评估                                                                |

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
C2: style.fingerprint ← scripts/style_analyzer.py 实测语料（fingerprint_source="measured"）
    principles ← 原文直引优先，每条必带 source_refs + priority
    examples ← before/after > contrastive > positive > negative
    anti_patterns ← 必带 detection_signals + correction（否则无法进判断回路）
    heuristics ← 承载"太用力了"式模糊经验：信号→倾向→纠正
C3: judgment.dimensions ← 从 intent.success_criteria + principles 派生
    judgment.weighting ← 键与 dimensions 一一对应，和 = 1.0
    policy ← priorities + tradeoffs + rejection（从专家否决记录与取舍行为提取——没有取舍规则的判断回路是评分器不是决策器）
    evaluation ← independent_judge + evaluator_separation + novelty 参照系（品类套路清单）
    revision ← max_rounds 按任务价值定（普通 1-3，高价值 3-5）
    runtime_profile ← 按 meta.type 查 §Runtime Profile 基准表
```

### 关键构建规则

1. **Style Fingerprint 禁止凭印象填** — 数值必须来自 `scripts/style_analyzer.py` 对语料的实测（full 模式由 validate_creative_ir.py 强制 fingerprint_source=measured）。没有语料就降低 confidence 并在诚实边界声明，不许编造。
2. **原则 ≠ 约束** — "标题不能超过20字"是 constraint（硬边界），"先让读者感受到问题，再给答案"是 principle（创作哲学）。混放会导致判断回路把哲学当规则机械执行。
3. **示例必须有 explanation** — 没有解释的示例只是语料。价值排序：专家修改前→修改后 ＞ A/B 对比 ＞ 单纯好例。
4. **编译器推断不能伪装成专家原话** — 每条知识的 source\_refs.origin 必须如实标注。inferred/heuristic 占比过高 → confidence 相应下调。
5. **无反例的创造型 skill 必然模板化** — examples.negative 和 anti\_patterns 至少提供一个，源材料没有就从用户处索取或在诚实边界声明。
6. **Policy 的取舍必须有 rationale（v3.1）** — 无 rationale 的 tradeoff 是偏好黑箱，无法向用户解释为什么放弃 A 选 B。

### Pass C3→C4 Decision Gate

Creative IR 落盘为 JSON 时，执行：

```bash
python3 scripts/validate_creative_ir.py <creative-ir.json>
```

退出码 0 才进 C4。校验覆盖：判断回路必填性（dimensions ≥3 / weighting 一致 / revision 就位）、Style Fingerprint 六项核心指标、溯源闭环（source\_refs.document\_id 必须在 provenance 登记）。未落盘时按 schema 必填字段清单逐项核对。

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
│   ├── style.md          # Style Grammar + Fingerprint（结构化，非形容词堆砌；标注 fingerprint_source）
│   ├── principles.md     # 原则 + rationale + 适用条件
│   ├── heuristics.md     # 信号→倾向→纠正
│   ├── anti-patterns.md  # 检测信号 + 纠正方向
│   ├── policy.md         # Creative Policy：priorities + tradeoffs + decision_rules + exceptions + rejection（v3.1）
│   ├── runtime.md        # 判断回路规范（Judge/Critique/Revision/独立评价器配置）
│   ├── strategy.md       # 创意策略链（Problem→Tension→Insight→Territory→Angle，可选）
│   └── constraints.md    # 四分类约束（hard/soft/contextual/creative）
├── examples/
│   ├── positive.md       # 含 explanation
│   ├── negative.md       # 含 explanation（强烈建议）
│   └── contrastive.md    # A/B 对比 + before/after（最高价值）
├── templates/
│   └── output.md         # 输出契约模板（format/sections/platform rules）
├── tests/
│   ├── golden-set.json   # 机器可执行基准（benchmark_runner.py 输入，≥3 条，建议 ≥20 条）
│   └── adversarial.md    # 对抗用例：模糊修正请求 → 期望的 fingerprint 局部调整
├── runs/                 # benchmark 运行记录（<version>.json，回归对比的数据源）
├── reports/              # benchmark report（版本对比 + 回归判定）
└── honest-boundaries.md  # 诚实边界（confidence 低时强制声明材料不足）
```

**SKILL.md 只是 Runtime 的入口契约**——真正的创作行为（发散→判断→修订）发生在 runtime.md 定义的判断回路里。

📍 判断回路的运行时规范：[creative-runtime.md](creative-runtime.md)

***

## Pass C5 — 创意五层评估

| Layer | 检查 | 方法 |
| ----- | --- | ---- |
| **1 Structural** | 格式/约束/输出契约 | 同 General Layer A，机械可测 |
| **2 Semantic** | 任务是否完成（intent.success\_criteria 逐条） | 逐条核对 |
| **3 Creative** | 风格保真度（Style Distance）+ AI 腔率（anti-pattern 命中率）+ **判断回路有效性（独立口径 Revision Gain）** | Fingerprint 对比 + 模拟运行一轮判断回路 |
| **4 Model Preference** | 成对比较偏好（产物 A vs 旧版/基线） | pairwise 比较——**是模型偏好，不是人类偏好的替代品** |
| **5 Human Preference** | 真实人类反馈（可选数据采集层） | 采纳率/人工 A/B——采到才算数，LLM 偏好不得冒充 |

**诚实性原则（v3.1）：** L4 是 Model Preference 不是 Human-proxy——LLM preference 与 human preference 经常不一致（广告/命名/品牌策略领域尤甚）。L5 默认关闭（`evaluation.preference_ladder.human_feedback.collect=false`），但产物文档不得把 L4 结果表述为"人类偏好"。

**Layer 3 的核心指标：**

```
style_fidelity    = 1 - style_distance（generated fingerprint vs target fingerprint）
anti_pattern_rate = 命中 anti-pattern 的候选占比
revision_gain     = independent_post_score - independent_pre_score（Judge B 独立口径）
```

`revision_gain ≈ 0` 说明判断回路没真正发挥作用——修订只是重新抽卡，产物应判 CONDITIONAL 并回 C3 检查 critique/revision 配置。**自评口径的 gain（Generator/Judge A 自己打分）存在 Evaluator Leakage，C5 不采信**——详见 [creative-runtime.md](creative-runtime.md) §4。

**Layer 3/4/5 完整指标枚举（9 项，v3.1 拆分 Originality 为 Diversity + Novelty）：**

| # | 指标 | 归属 Layer | 说明 |
|---|------|-----------|------|
| 1 | Task Fit | L2 | intent.success_criteria 逐条达成 |
| 2 | Style Fidelity | L3 | 指纹距离 → 保真度 |
| 3 | Diversity | L3 | 候选间最小距离（发散是否真发散，同母题换说法 = 0 分） |
| 4 | Novelty | L3 | **相对参照系**的新颖度：品类套路簇 / 源示例 / 自身输出史。候选间距离只证明 Diversity 不证明 Novelty——三个彼此很不同的方案可能都很普通 |
| 5 | Specificity | L3 | 具体度（对应 fingerprint.concreteness 方向） |
| 6 | Consistency | L3 | 人设/品牌一致性（context 与产物的矛盾检测） |
| 7 | Anti-pattern Rate | L3 | 反模式命中率 |
| 8 | Model Preference | L4 | LLM pairwise 偏好（静态近似） |
| 9 | Revision Gain | L3 | 判断回路有效性（独立评价口径） |

### Golden Set（评估基准）

创造没有唯一标准答案，Golden Set 存的是**期望特征与期望方向**，不是标准答案。v3.1 起落盘为机器可执行的 `tests/golden-set.json`（benchmark\_runner.py 的直接输入）：

```json
{
  "skill_name": "justin-writing-style",
  "target_fingerprint": { "sentence_length": 0.35, "abstraction": 0.2, "concreteness": 0.7 },
  "cases": [
    {
      "id": "c001",
      "input": "写一个关于第一次创业失败的开场",
      "expected": { "tone": "restrained", "perspective": "first_person" },
      "task_fit_criteria": ["前三秒出现具体事实", "无广告腔"],
      "category_conventions": ["30岁以后才知道", "作为一个创业者", "今天我想分享"]
    }
  ]
}
```

- `target_fingerprint`：来自 style\_analyzer.py 实测，style\_fidelity 的比较基准
- `task_fit_criteria`：Task Fit 的逐条核对清单
- `category_conventions`：Novelty 的品类套路参照系（从源材料否决记录与品类常见套路提取）

产物 skill 包必须含 `tests/golden-set.json`（≥3 条，建议 ≥20 条——样本量不足时 benchmark report 会输出置信度警告），C5 Layer 2/3 以此为基准逐条核对。

### 对抗测试（Adversarial Creative Test）

用模糊修正请求冲击产物 skill 的风格稳定性——这类请求最容易触发 Style Drift：

```
"再高级一点" / "再有感染力一点" / "更有网感" / "更炸裂"
```

**PASS 标准：** Runtime 将模糊修正解释为 fingerprint 的**局部参数调整**（如 emotional_explicitness +0.1），而非整体重写风格。解释失败 = Style Drift 防御缺失 → C5 判 CONDITIONAL。

### Benchmark Runner（编译器实证，v3.1）

**North Star Metric：编译出来的 Skill 是否比原来的 Skill 更会创作。** 回归测试不再只是"重编译对比"，而是可执行的基准评测：

```bash
# 1. 各版本 skill 跑完 golden-set 全部 case，产出 runs/<version>.json
#    （运行记录含：候选文本 + 实测 fingerprint + Judge B 独立 pre/post 分 +
#      anti-pattern 命中 + 跨版本 pairwise 胜负）
# 2. 对比
python3 scripts/benchmark_runner.py \
  --golden-set tests/golden-set.json \
  --runs runs/legacy.json runs/creative_v1.json \
  --report reports/benchmark.md
```

Report 输出版本 × 指标矩阵与相对基线增量（task\_fit / style\_fidelity / novelty / anti\_pattern\_rate / revision\_gain / model\_preference）。

**判读标准：**
- 核心指标显著提升且 anti\_pattern\_rate 下降 → Creative Compiler 成立
- 各版本差距 < 0.05 → 架构漂亮但创造能力增量不足，优化方向回 C2/C3（能力提取与判断设计），**不是继续加 IR 字段**
- benchmark\_runner 只采信 `independent_pre/post_score`——自评口径的 revision\_gain 一律拒绝

### 回归测试（Compiler 与 Skill 自身演进）

- **编译器升级（v3.0 → v3.1）：** 对同一 Golden Set 重新编译两版产物，跑 benchmark 对比。任一核心指标显著退化（> 0.05）→ 本次编译器变更回退。"修了一个能力，毁掉另一个能力"是编译器演进最常见的失败。
- **Skill 自身演进（Mutation Loop）：** Skill vNext 生效前必须过 benchmark 回归（`learning.mutation.requires_benchmark`）。📍 完整规则：[creative-learning.md](creative-learning.md)

**Verdict 规则与 General Track 一致**（≥85 GO / 60-84 CONDITIONAL / <60 NO-GO），但 Layer 3 不达标直接 CONDITIONAL 起步。

***

## 与 General Track 的产物互操作

* Creative Skill Package 与 General Skill Package 结构兼容（SKILL.md + references/ + templates/），可被同一宿主平台加载

* Creative skill 被二次编译（作为 skill\_package 输入合并）时：style/principles/examples 作为知识进入 knowledge\_inventory，judgment/revision 配置作为能力进入 capability\_graph，走 General Track 的合并规则（统一 Context + 能力去重）

