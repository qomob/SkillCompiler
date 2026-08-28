<div align="center">

# Skill Compiler | 白泽

**任意来源 → Skill IR → Optimized Skill Package（双编译：General + Creative）**

> **命名寓意：** 白泽，神话中通晓万物之理的神兽。本 Skill 能将任意来源（PDF/视频/网页/图片/文档）编译为可复用 Skill，如白泽之通晓万物。

把任意来源（文本 Prompt、PDF、视频、网页、图片、文档）编译成可复用、可维护、可持续演化的 AI Skill。v3.0 起支持双编译架构：流程/知识类走 General Track，创作类（写作风格/文案/广告/脚本/品牌/Naming/IP）走 Creative Track——**编译的不是 Prompt，是 Creative Capability**（含判断回路 Judge + Critique + Revision）。v3.1 补上可执行能力层：Style Fingerprint 强制实测（style_analyzer.py）、Creative Policy 决策模型、独立评价器、Benchmark Runner 版本对比实证、Skill Mutation Loop 能力演化闭环。

[![Author](https://img.shields.io/badge/Author-qomob.ai-blue)](https://qomob.ai)
[![Version](https://img.shields.io/badge/Version-v3.1.0-green.svg)](https://github.com/qomob/SkillCompiler)
[![Language](https://img.shields.io/badge/Language-%E4%B8%AD%E6%96%87-red.svg)](https://github.com/qomob/SkillCompiler)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Built with](https://img.shields.io/badge/Built_with-SkillForge-violet.svg)](https://github.com/qomob/skillforge)

</div>

---

## 这是什么

Skill Compiler 是一个 **Meta Skill（元技能）**——它的输入是任意来源（文本 Prompt、PDF、视频、网页、图片、文档），输出是一个完整的、结构化的 AI Skill 文件包。

它不是"Prompt 优化器"。它是一个 **能力编译器**：保留来源背后的"能力（Capability）"，而非来源本身的文字。

```
Source (Prompt / PDF / Video / URL / Image / Doc)
      │
      ▼
  Ingest → Triage（编译目标分类路由 Step 0.1b）
      ├─ procedural / knowledge / analytical → General Track:
      │    Analyze → Extract → Design → Generate → Optimize? → Validate
      └─ creative（写作/文案/广告/脚本/品牌/Naming/IP/hybrid）→ Creative Track:
           Understand → Extract → Design（判断回路）→ Generate → Optimize? → Evaluate
      │
      ▼
  Complete Skill Package
```

### 核心主张：判断回路是"会模仿"与"会创作"的分水岭

专家和普通人的差距，不在于会不会写，而在于：**能判断哪个方案更好、知道哪里不对、以及怎么改**。因此 Creative Track 编译的是判断力本身：

```
General Skill  = 知道（Know）
Creative Skill = 知道 + 会判断（Judge）+ 会否决（Reject）+ 会改进（Improve）
```

Creative IR 将 `judgment + revision` 设为**必填字段**——缺判断回路的"创意 skill"只是带风格提示词的生成器，会在 C3→C4 门控被直接拦截。

---

## 为什么用它

| 对比 | 直接用 Prompt | 手写 Skill | **Skill Compiler** |
|------|--------------|-----------|-------------------|
| 复用性 | 一次性，每次重写 | 高，但门槛高 | 高，且开箱即用 |
| 维护成本 | 改一处要改全文 | 需手动同步多处 | 知识外置，模块独立 |
| 质量保障 | 无 | 靠经验 | General 五层评估闭环；Creative 五层评估（L1-L5：风格保真 / AI 腔率 / 独立 Revision Gain / Novelty / 偏好）+ Benchmark 版本对比实证 |
| 判断能力 | 无 | 无 | Creative Track 内置判断回路（Judge + Critique + Revision + Revision Gain 追踪） |
| 风格还原 | 形容词堆砌 | 靠语感 | 12 维 Style Fingerprint + 运行时漂移检测（correction 优先于重生成） |
| 多源输入 | 不支持 | 需手动预处理 | PDF/视频/网页/图片/文档自动摄取（创作源材料保全：修改痕迹/否决记录/说话人归属） |
| 平台适配 | 不适用 | 需手动改格式 | 支持 TRAE / Claude / Generic |
| 诚实边界 | 无 | 容易遗漏 | 强制声明局限性 + 失败模式 + 材料不足 + 风格保真边界 |

**适合的场景：**
- 你有一个反复使用的 Prompt，想升级成可维护的 Skill
- 你有 PDF/视频/网页等素材，想提炼成可复用的能力
- 你有某位创作者的访谈/范文/修改痕迹，想编译成**带判断回路的创作型 Skill**（不只是模仿文风）
- 你想批量生成符合特定平台规范的 Skill

**不适合的场景：**
- 一次性问答（直接问就行）
- 纯翻译/摘要（直接做）
- 从零设计全新能力（没有源材料）

---

## 快速开始

给 Skill Compiler 一个源材料（Prompt / 文件 / URL），它会自动走完整编译流程：

```
1. Pass 0  — 判断是否值得编译 + 编译目标分类路由（General/Creative）+ 选平台 + 选模式 + 设预算
2. General Track: Pass 1-3 分析 → 抽取 → 设计，产出 Skill IR（含自测用例）
   Creative Track: Pass C1-C3 意图/场景 → 五提取器（含 Style Fingerprint）→ 判断回路设计，产出 Creative IR
3. Pass 4 / C4 — 基于 IR + 平台 profile 生成文件包
   （Creative 产物含判断回路 runtime + golden set + 对抗用例）
4. Pass 5  — 条件优化（去重 + IR 瘦身；判断回路与示范材料受保护，不可被优化删减）
5. Pass 6 / C5 — 五层评估 / 创意五层评估（L1-L5 + Golden Set + 对抗测试 + Benchmark 对比），输出评分 + GO/NO-GO
```

### 示例输入（Creative Track）

```
材料：
1. 某创作者 12 篇小红书范文（含 3 组初稿→修改稿对照）
2. 两小时访谈转写（含大量"这个不行/太用力了"式的否决记录）

目标：编译成一个创作型 skill，要能写还要能判断像不像他
```

### 示例输出（Creative Skill Package）

```
justin-writing-style/
  SKILL.md              # 入口契约：路由 + Creative Workflow + 质量维度声明
  references/
    style.md            # Style Grammar + 12 维 Fingerprint（结构化，非形容词堆砌）
    principles.md       # 原则 + rationale + 溯源（origin: explicit/inferred/heuristic/generated）
    anti-patterns.md    # 从否决记录提取的检测信号 + 纠正方向
    runtime.md          # 判断回路：Judge 维度/权重 → Critique 四要素 → Revision（含停机条件）
  examples/
    before-after.md     # 修改痕迹对照 + 为什么改（最高价值示例）
  tests/
    golden-set.md       # 期望特征与方向（非标准答案）
    adversarial.md      # "再高级一点"式模糊请求 → 期望的 fingerprint 局部调整
  honest-boundaries.md  # 材料不足/风格保真边界/判断回路边界声明
```

General Track 示例（Python 代码审查 / API 文档生成器）见：
- [examples/example-compilation.md](examples/example-compilation.md)
- [examples/example-workflow-compilation.md](examples/example-workflow-compilation.md)

### 编译模式

| 模式 | Token 开销 | 适用场景 |
|------|-----------|---------|
| `quick` | 低（~3 次调用） | Prompt < 200 字，已熟悉 Skill 结构 |
| `full` | 高（~6+ 次调用） | 复杂 Prompt，需要完整能力提取与验证（默认） |
| `audit` | 中（~2 次调用） | 评估已有 Skill，不生成新文件 |

---

## Compiler Pipeline

| Pass | 执行 | 职责 |
|------|------|------|
| **I Ingestion** | ⚠️ 条件 | 多源摄取：PDF/视频/网页/图片/文档 → 结构化内容 + 来源溯源（两轨道共享；Creative 源材料保全：修改痕迹配对/否决记录单独成块/说话人归属） |
| **0 Triage** | ✅ 总是 | 判断是否值得编译 + **编译目标分类路由（Step 0.1b：General / Creative Track）** + 选平台 + 选模式 + 设 Token 预算 |
| **1 Analyze** | ✅ 总是 | 理解内容：目标 / 输入输出 / 边界 / 假设 + 状态需求信号检测（Step 1.4b，命中 → state_signals） |
| **2 Extract** | ✅ 总是 | 能力图谱 + 知识清单（含证据分级）+ 角色矩阵 |
| **3 Design** | ✅ 总是 | 架构类型 + 模块拆分（含诚实边界）+ Workflow + 目录结构 + 自测用例 |
| **4 Generate** | ✅ 总是 | 基于 IR + 目标平台 profile 生成符合平台规范的完整 Skill 文件包 |
| **5 Optimize** | ⚠️ 条件 | 内容 > 500字 / 重复 / multi-agent 时执行（Creative 产物受保护项：判断回路配置/explanation/正反对偶示例/Fingerprint） |
| **6 Validate** | ✅ 总是 | 五层评估：结构（A，含 Compaction Resilience）+ IR 一致性（B）+ 触发质量（C，含压力测试）+ 平台合规（D）+ Token 经济性（E） |
| **C1 Understand** | ✅ 总是* | Resolved Intent（表面请求 vs 真实创作意图）+ 六维 Context Model（人/品牌/受众/平台/市场/文化） |
| **C2 Extract** | ✅ 总是* | 语义分块 + 五提取器：Principle / Style（含 12 维 Fingerprint）/ Example / Anti-pattern / Heuristic + 领域知识（knowledge） |
| **C3 Design** | ✅ 总是* | 判断回路设计（Judge dimensions/weighting + Revision 策略）+ **Creative Policy（tradeoffs/exceptions/rejection）** + 边际增益发散配置 + Runtime Profile → 产出 Creative IR（[schema](schemas/creative-ir-schema.json)） |
| **C4 Generate** | ✅ 总是* | Creative IR → Creative Skill Package（入口契约 + 判断回路 runtime + golden set + 对抗用例 + 诚实边界） |
| **C5 Evaluate** | ✅ 总是* | 创意五层评估：L1 Structural / L2 Semantic / L3 Creative（风格保真 + AI 腔率 + 独立 Revision Gain + Novelty）/ L4 Model Preference / L5 Human Preference（可选采集），Golden Set 基准 + 对抗测试 + **Benchmark Runner 版本对比** |
| Skill Merge | ❌ 条件 | 输入为 N 个已有 skill 包：能力去重 + 边界冲突裁决 + 统一 Context，产物为 stateful-domain-os（v2.3.0） |
| Plugin Discovery | ❌ 条件 | 涉及外部能力（搜索/GitHub/DB/MCP）时执行 |
| Example Generation | ❌ 条件 | 涉及复杂流程/规则/评分体系时执行 |

*\* C1-C5 仅在 Step 0.1b 路由到 Creative Track 时执行。*

### 路由判定依据（Step 0.1b）

按优先级：① 产出是否需要判断力（输出有"好坏之分"且标准模糊 → creative）；② 风格是否是产物的一部分；③ 源材料是否有专家否决记录；④ 混合时看主体——**宁可 hybrid 判 creative，不可反向**（creative 任务走 General Track 会得到"能写但不会判断"的模板化 skill，这是最贵的失败）。

### 评分与 Verdict

```
General: skill_quality_score = Layer A×0.15 + Layer B×0.25 + Layer C×0.20 + Layer D×0.20 + Layer E×0.20
Creative: 五层评估（L1-L5），L3（Creative）不达标直接 CONDITIONAL 起步
```

| 分数 | Verdict |
|------|---------|
| ≥ 85 且 0 Critical | **GO** |
| 60-84 或有 Critical 但可修复 | **CONDITIONAL** |
| < 60 | **NO-GO** |

### 判断回路（Creative Runtime）

```
INIT → UNDERSTAND → CONTEXTUALIZE → BRIEF → STRATEGIZE
     → DIVERGE（目标 3 母题，边际增益低于阈值即停）→ FILTER（硬约束 + 最小距离去重 + rejection 一票否决）
     → JUDGE ──┬─→ FINALIZE → MEMORY_UPDATE
               ↑
       CRITIQUE → REVISE → COMPARE（独立 Revision Gain）
```

- **Judge** 只做 Observe→Score→Compare→**Decide**→Explain，不重新生成；默认开启 pairwise 比较（LLM 的绝对判断弱于成对判断）；**决策裁决**（v3.1）：rejection > exceptions > tradeoffs > priorities > 加权分——创造能力不是 Score Function，是 Decision Policy
- **Critique** 四要素：What（问题）/ Why（违反哪条原则）/ Where（定位）/ How（怎么改）
- **Revision** 强制诊断式局部修改（diagnose→locate→plan→partial fix→re-judge），禁止无脑重写；`Revision Gain ≈ 0` = 判断回路失效。**v3.1：gain 必须由独立评价器（Judge B）计算**——Generator/Judge A 自评的 gain 是 Evaluator Leakage（评价器偏爱自己的修改）
- **Candidate 对象**：创意 + rationale + 评分 + 指纹 + 修订史同时流转，禁止裸文本传递
- **Style Drift**：候选实测指纹 vs 目标指纹，超阈值时 correction 优先于重生成
- **Memory**：四层记忆 + Failure Memory（负知识）+ Preference 解析（"太AI了" → 可执行偏好规则）

---

## 核心能力

- **多源摄取** — PDF/视频/网页/图片/文档自动解析（pdftotext/ffmpeg+whisper/tesseract/WebFetch），标准化为结构化内容 + 来源溯源
- **证据分级** — 每条知识携带 primary/secondary/inferred 证据等级，冲突信息保留标注而非静默消除
- **诚实边界** — 生成的 skill 强制声明局限性/失败模式/适用前提；Creative 追加材料不足/风格保真/判断回路/风格演化四项声明
- **并行提取器** — 五个专项提取器并行扫描长内容，三重验证筛入知识库
- **压力测试** — 构造边界交叉区诱饵输入验证 description 锐利度
- **平台适配** — 支持 TRAE / Claude / Generic，自动按平台规范渲染 frontmatter 与文件结构
- **压缩截断韧性** — 检查生成的 skill 在 harness compaction 后 routing 信息是否仍完整
- **Token 预算控制** — 设定预算上限，超限时自动降级模式
- **三层渐进加载** — 生成的 Skill 遵循 L1 触发 / L2 路由 / L3 懒加载分层
- **Skill 合并编译** — 输入 N 个已有 skill 包 → 能力去重 + 边界冲突裁决 + 统一 Context（v2.3.0）
- **State 一等公民 / session-context 自动注入** — 状态信号检测命中 → 自动生成 State 三件套（v2.3.0）
- **结构化行为断言** — 自测用例升级为程序化断言，生成 tests/cases.yaml（v2.3.0）
- **元反思审计** — 编译器在关键决策后执行 8 维度自省（含 Creative 检查点：Fingerprint 是否实测 / weighting 是否均匀分配 = 没做判断）
- **双编译架构（v3.0）** — Pass 0 编译目标分类路由：流程/知识类走 General Track，创作类走 Creative Track（Pass C1-C5），共享机制（Ingestion/证据分级/诚实边界/元反思/Pass 5）全程贯穿
- **Creative IR + 判断回路（v3.0）** — 创作类编译产出 Creative IR（[schemas/creative-ir-schema.json](schemas/creative-ir-schema.json)，18+ 字段含 knowledge 领域知识），judgment + revision 为必填字段；C3→C4 门控由 [scripts/validate_creative_ir.py](scripts/validate_creative_ir.py) 强制校验（权重和=1.0、溯源登记、quick 模式豁免规则）
- **Style Fingerprint（v3.0）** — 创作者风格压缩为 12 维可比较数值向量，禁止凭印象填写；运行时 Style Drift 检测，correction 优先于重生成
- **origin 四级证据溯源（v3.0）** — explicit/inferred/heuristic/generated，Compiler 推断不伪装成专家原话
- **Golden Set + 对抗测试 + 回归测试（v3.0）** — 期望特征与方向（非标准答案）作为评估基准；"再高级一点"式模糊请求冲击风格稳定性；编译器版本间产物对比防能力退化
- **Style Analyzer（v3.1）** — [scripts/style_analyzer.py](scripts/style_analyzer.py) 把语料实测为 12 维 Style Fingerprint（raw measurements → normalization），full 模式 fingerprint_source 强制为 measured——Fingerprint 从 schema 声明变成可执行测量
- **Creative Policy 决策模型（v3.1）** — Creative IR 新增 `policy` 必填字段（priorities/tradeoffs/decision_rules/exceptions/rejection）：Judge 从加权评分器升级为创意决策器，冲突时按取舍规则裁决而非机械打分
- **独立评价器（v3.1）** — `evaluation.independent_judge`（full 模式禁止关闭）+ Novelty 参照系（category conventions / source examples / own output history）——区分 Diversity（候选间距离）与 Novelty（相对参照系的原创性）
- **Benchmark Runner（v3.1）** — [scripts/benchmark_runner.py](scripts/benchmark_runner.py) 自动对比多版本 skill（Legacy vs Creative v1/v2...），输出 task_fit / style_fidelity / anti_pattern_rate / novelty / revision_gain / preference 指标与增量报告
- **Skill Mutation Loop（v3.1）** — [references/creative-learning.md](references/creative-learning.md)：Feedback → Pattern（≥3 次同类）→ Capability Delta → Candidate vNext → Benchmark 回归 → Human Approval——skill 从静态文件进化为可演化能力

---

## 文件结构

```
skill-compiler/
├── SKILL.md                        # 入口 + 路由 manifest（< 300 行）
├── README.md                       # 本文件
├── CHANGELOG.md                    # 版本变更日志
├── profiles/                       # 目标平台规范
│   ├── trae.md                     #   TRAE IDE Skill 规范
│   ├── claude.md                   #   Claude.ai / Claude Code 规范
│   └── generic.md                  #   默认通用规范
├── references/                     # 各 Pass 的详细指令（懒加载）
│   ├── pass-ingestion.md           #   Pass I: 多源摄取（含 Creative 源材料保全规则）
│   ├── pass-1-analyze.md           #   Pass 1: 理解内容
│   ├── pass-2-extract.md           #   Pass 2: 能力/知识/角色抽取
│   ├── pass-3-design.md            #   Pass 3: 架构设计 + 自测用例
│   ├── pass-4-generate.md          #   Pass 4: 生成文件包
│   ├── pass-5-optimize.md          #   Pass 5: 条件优化（含 Creative 优化禁区）
│   ├── pass-6-validate.md          #   Pass 6: 五层评估
│   ├── evidence-grading.md         #   证据分级体系（含 origin 四级映射）
│   ├── honest-boundaries.md        #   诚实边界规范（含创作专属声明）
│   ├── parallel-extractors.md      #   并行提取器 + 三重验证
│   ├── anti-patterns.md            #   反模式定义
│   ├── plugin-discovery.md         #   条件 Pass: 插件识别
│   ├── example-generation.md       #   条件 Pass: 示例生成
│   ├── meta-reflection.md          #   8 维度编译自省框架（含 Creative 检查点）
│   ├── creative-compiler.md        #   v3.0: Creative Track 总纲（路由+管线+IR+产物+C5 五层评估+Golden Set+对抗/回归测试+Benchmark）
│   ├── creative-extraction.md      #   v3.0: Pass C1/C2 意图/场景/五提取器/Style Fingerprint（style_analyzer 实测）/origin 溯源
│   ├── creative-runtime.md         #   v3.0: 判断回路规范（状态机+决策裁决+独立 Revision Gain+Style Drift+Memory）
│   └── creative-learning.md        #   v3.1: Skill Mutation Loop（Feedback→Pattern→vNext→Benchmark→Human Approval）
├── templates/
│   ├── skill-md-template.md        #   SKILL.md 输出模板
│   └── ir-schema.md                #   Skill IR 中间表示 schema
├── examples/
│   ├── example-compilation.md      #   完整编译示例（Python 代码审查）
│   └── example-workflow-compilation.md  # Workflow 类型编译示例
├── schemas/
│   ├── ir-schema.json              #   Skill IR JSON Schema（General Track）
│   ├── creative-ir-schema.json     #   Creative IR JSON Schema（Creative Track，v3.0）
│   └── trace-schema.json           #   执行 trace 契约（含 creative_evaluation 指标）
├── scripts/
│   ├── validate_ir.py              #   Pass 3→4 IR 门控校验
│   ├── validate_creative_ir.py     #   Pass C3→C4 Creative IR 门控校验（v3.0，v3.1 增 policy/evaluation/measured fingerprint 规则）
│   ├── style_analyzer.py           #   v3.1: 语料 → 12 维 Style Fingerprint 实测（raw measurements + normalization）
│   └── benchmark_runner.py         #   v3.1: 多版本 skill 基准对比（golden-set.json + runs/*.json → benchmark report）
├── evals/
│   └── trigger_cases.json          #   触发词静态测试用例（含 creative 入口）
└── docs/
    └── self-compilation-audit.md   #   自编译审计记录
```

---

## 设计原则

| 原则 | 含义 |
|------|------|
| Prompt 不是 Skill | Skill = Role + Workflow + Knowledge + State + Decision Logic + Checklist + Rubric + Templates + Examples + Config + References + Output Schema |
| 编译能力，不编译文字 | 保留"能力"而非"文字"；Creative Track 编译的是判断力（Judge + Critique + Revision），不是风格提示词 |
| 知识按变更频率分层 | 重复内容外置 → `references/`；稳定层与时效层分离 |
| 证据可溯源 | 每条知识带证据等级/origin 标注，冲突保留不洗白，推断不伪装成原话 |
| 宁可 hybrid 判 creative | creative 任务误走 General Track = "能写但不会判断"的模板化 skill（最贵失败） |
| 元反思审计 | 关键决策后 8 维度自省 |

---

## 与 SkillForge 的关系

Skill Compiler 由 [SkillForge](https://github.com/qomob/skillforge) Full 模式构建，通过了完整的 5 层验证（Triage → Create → Validate → Audit → Deploy Decision），Compliance Score 100%，Gaming Gate PASS。

版本演进历史见 [CHANGELOG.md](CHANGELOG.md)。

---

## 加入群聊

<div align="center">
  <img src="https://qomob.ai/xskill.jpg" width="600" alt="XSkill">
</div>

---

## License

[MIT](https://opensource.org/licenses/MIT)
