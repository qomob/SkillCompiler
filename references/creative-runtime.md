# Creative Runtime — 判断回路规范

**加载时机：** 📍 Pass C3 设计判断回路配置、Pass C4 生成产物中的 runtime.md 时加载。本文件同时是 Creative Skill Package 内 `references/runtime.md` 的规范来源。

**定位：** 判断回路（Judge + Critique + Revision）是创造型 skill 从"会模仿"到"会创作"的分水岭。没有判断回路的"创意 skill"只是带风格提示词的生成器。

---

## §1 运行状态机

创作不是一次函数调用，是有状态的流程：

```
INIT → UNDERSTAND → CONTEXTUALIZE → BRIEF → STRATEGIZE
     → DIVERGE → FILTER → JUDGE ──┬─→ FINALIZE → MEMORY_UPDATE
                                  ↑
                          CRITIQUE → REVISE → COMPARE
```

| 状态 | 职责 | IR 来源 |
|------|------|--------|
| `UNDERSTAND` | 解析用户请求的真实意图（表面请求 vs 真实意图，同 C1 逻辑） | intent |
| `CONTEXTUALIZE` | 召回场景：人/品牌/受众/平台 | context |
| `BRIEF` | 合成 Creative Brief（本次创作的具体约束） | intent + context + constraints |
| `STRATEGIZE` | 选创意方向（Territory/Angle） | creative_strategy |
| `DIVERGE` | 按 territory 发散候选（目标 3 母题；新增母题边际增益低于阈值即停——发散到边际收益下降为止，而非固定数量） | generation.divergence |
| `FILTER` | 硬约束过滤 + 最小距离去重（同母题换说法合并）+ policy.rejection 一票否决 | constraints.hard + diversity + policy.rejection |
| `JUDGE` | 评分 + 成对比较 + **决策裁决**（tradeoffs > priorities > 加权分），产生 keep/revise/reject 建议 | judgment + policy |
| `CRITIQUE` | 对 revise 候选产出结构化批评（What/Why/Where/How） | judgment + anti_patterns |
| `REVISE` | 按批评局部修改，不重写 | revision |
| `COMPARE` | 与前一版对比，计算 Revision Gain，决定继续/停止 | revision.stop_conditions |
| `FINALIZE` | 选最终版 + 整理输出 + 遵守输出契约。**不能重新发散** | output |
| `MEMORY_UPDATE` | 记录决策/否决/用户偏好（Failure Memory） | memory |

**状态映射到 SKILL.md 的 Creative Workflow 章节**——C4 生成产物时按此状态机渲染工作流。

**quick 运行模式**（运行时，区别于编译模式）：UNDERSTAND → DIVERGE → JUDGE → FINALIZE，跳过 CRITIQUE/REVISE/COMPARE。仅限低价值高频任务。

---

## §2 Judge 规范

**Judge 不重新生成内容。它只做：Observe → Score → Compare → Decide → Explain。**

### 评分流程

1. **Observe** — 按 judgment.dimensions 逐维度观察候选，引用具体文本证据（"第 2 段'亏了 47 万'是具体事实"）
2. **Score** — 各维度 0-1 评分，加权求和。权重来自 IR judgment.weighting
3. **Compare** — pairwise 成对比较（见 §3）
4. **Decide** — 决策裁决（见 §2.1）：加权分接近或冲突时，裁决权移交给 policy
5. **Explain** — 输出 strengths / weaknesses / risks + 建议（keep/revise/reject）

### 维度设计规则（C3 阶段）

- dimensions 从 `intent.success_criteria` 与 `principles` 派生，**禁止只设一个笼统 "quality"**，至少 3 个
- 好维度是可观察的："specificity"（具体事实密度）优于 "quality"（什么都测不到）
- weighting 与 dimensions 一一对应，和 = 1.0（validate_creative_ir.py 强制）

### 惩罚规则

anti-pattern 命中 / AI 腔 / 风格漂移的扣分独立于维度评分：

| penalty | 触发 | 建议权重 |
|---------|------|---------|
| `ai_pattern_penalty` | 命中任一 anti_patterns.detection_signals | severity critical 命中 → 直接 reject，不进 Revision |
| `cliche_penalty` | 命中 style.negative_signals 或 evaluation.novelty.category_conventions 套路簇 | 0.2 |
| `constraint_violation` | 违反 hard constraint | 违反 → reject |
| `style_drift_penalty` | Style Distance 超阈值 | 0.3（见 §5） |

`minimum_quality`：低于此分直接 reject，不浪费 Revision 轮次。

**评分只是辅助——Score + Reason + Comparison 三者一起工作，不能把创造完全数学化。** 没有文本证据支撑的分数视为无效评分。

### §2.1 决策裁决（v3.1）—— 创造能力不是 Score Function，是 Decision Policy

加权评分回答"各维度多少分"，不回答"该选哪个"。专家在冲突维度间做的是**取舍**，不是加权平均：

```text
A：原创性 9  相关性 9  品牌一致性 9      加权分 0.90
B：原创性 7  相关性 8  品牌一致性 10     加权分 0.83

加权评分器 → 选 A
创意总监   → 选 B（B 抓住了一个更重要的战略矛盾）
```

裁决顺序（高 → 低）：

1. **policy.rejection 命中** → 无论分数多高直接 reject（战略层否决：generic / derivative / off-brand）
2. **policy.exceptions 命中**（context 匹配）→ 按例外覆盖优先级
3. **policy.tradeoffs 命中**（冲突场景匹配）→ 按 prefer/tolerate_loss 裁决
4. **policy.priorities 排序** → 前项与后项冲突时保护前项
5. **加权分** → 仅在以上全部未命中时作为裁决依据；两候选加权分差 < 0.1 时，决策权必须移交给 1-4（不信任小数点后两位的"精确"）

裁决必须输出理由，引用命中的 tradeoff / priority 条目——**黑箱裁决 = 没有裁决**。

---

## §3 Pairwise Judge（成对比较）

**LLM 的 absolute judgment < pairwise judgment。** 默认开启（`judgment.pairwise_comparison: true`）。

```
A vs B → B > A
A vs C → A > C
B vs C → B > C
     ↓ 传递排序
胜者: B
```

- 全量两两比较 O(n²)，候选 > 5 时只对 FILTER 后的 shortlist（2-3 个）做
- 对标题/命名/slogan 类短创意尤其有效——比较暴露的是相对优势，正是创意决策的本质
- 平局（A=B 两次）→ 两者都进 CRITIQUE，让修订质量裁决

---

## §4 Critique + Revision 规范

### Critique：What / Why / Where / How

**禁止"再写得高级一点"式批评**——无法定位的批评无法指导修订：

```json
{
  "what": "开头过于常规",
  "why": "读者在第一句话无法获得新的信息，触发划走",
  "where": "paragraph-1, sentence-1",
  "how": "改为具体事件切入：把'亏了钱'改成'亏了 47 万'"
}
```

四要素缺一即无效：没有 where 的批评让修订无从下手；没有 why 的批评让 Revision 无法举一反三。

Critique 数据来源优先级：anti_patterns 命中（最具体）＞ heuristics 信号触发 ＞ 维度低分解释 ＞ 原则违背。

### Revision：diagnose → locate → plan → partial fix → re-judge

**禁止无脑重写——那是重新抽卡，不是修订。**

```
Critique（诊断）
  ↓
定位受影响段落（where）— 保护 revision.preserve 列表（如 opening 事实锚点）
  ↓
Revision Plan（改哪些部分、预期改善什么）
  ↓
局部修改 — 只动计划内的部分
  ↓
Changed Parts + Expected Improvement 记录
  ↓
re-judge（回到 JUDGE，重新评分）
```

### Revision Gain 与停止条件（v3.1：独立评价口径）

```
revision_gain = independent_post_score - independent_pre_score
```

**Revision Gain 必须由独立评价器（Judge B）计算，禁止 Generator / Judge A 自评。**

**Evaluator Leakage（自证循环）**——若 Generator、Judge A、Critique、Revision 共用同一模型、同一套标准、同一套 prompt，评价器会偏爱自己的修改：`revision_gain = +1.0` 可能只说明"评价器更喜欢自己改过的答案"，不代表作品真的变好了。独立性的最低保证层级（`evaluation.evaluator_separation`）：

| 层级 | 保证 | 成本 |
|------|------|------|
| `perspective` | 换评审视角/清单（同模型同 prompt 结构） | 低——最低要求 |
| `prompt` | 换 prompt 人设与评分协议 | 中 |
| `model` | 换模型评审 | 高——最强 |

```text
Generator → Judge A（筛选+诊断视角）
                ↓
         Critique → Revision
                ↓
         Judge B（独立评分视角）→ independent_post_score
                ↓
revision_gain = post - pre（pre 也须 Judge B 口径，修订前先盲评一次）
```

- `revision_gain ≈ 0` → Critique/Revision 没真正发挥作用（本次运行质量信号 + 编译期 C5 检查项）
- `revision_gain < 0` → 修订让产物变差，回滚到前一版
- 停止条件（任一满足即停）：达到 `revision.stop_conditions` 之一 / `max_rounds` 用尽 / gain 趋零（连续修订收益递减）
- quick 模式（编译模式）允许关闭独立评价器；full 模式禁止（validate_creative_ir.py 强制）

### 轮次预算

| 任务价值 | max_rounds | 理由 |
|---------|-----------|------|
| 普通内容（日常笔记/帖子） | 1-3 | 边际收益快速递减 |
| 高价值创意（campaign/品牌宣言/naming） | 3-5 | 值得深度迭代 |

**禁止无限循环。** max_rounds 上限 5（schema 强制）。

`diagnose_before_rewrite: false`（跳过 Critique 直接重写）仅允许编译模式为 quick 的 skill。

---

## §5 Style Drift 检测

**风格漂移 = 生成内容悄悄偏离目标风格**（AI 腔入侵、句长均匀化、修辞密度漂移）。单靠维度评分发现不了——漂移是逐渐发生的。

### 检测机制

```
Target Fingerprint（IR style.fingerprint，编译期从语料测得）
     vs
Generated Fingerprint（对每次生成内容计算同构向量）
     ↓
Style Distance（逐维差值加权和）
     ↓
超阈值 → style_drift_penalty + 触发 style correction
```

### 响应规则（重要）

**漂移触发 style correction，不是重新生成：**

1. 定位漂移维度（如 `sentence_variance` 掉了 → 句长变得均匀了）
2. 生成具体纠正指令（"把第 3 段拆成两个短句，让节奏参差回来"）
3. 进入 Revision 流程局部修正

只有 Style Distance 严重超标（如 > 2× 阈值）且 correction 无效时才丢弃重生成——重生成丢失的是已达标维度的分数，代价高于局部纠正。

### 阈值设定

- 无用户数据时默认 0.15（Fingerprint 归一化距离）
- `ai_pattern_risk` 基线高的目标风格，阈值适当放宽（目标本身接近模板化，过严会误杀）

---

## §6 Memory 与 Failure Memory

### 四层记忆（第一阶段只实现 Skill 级）

| 层 | 保留策略 | 内容 |
|----|---------|------|
| Session | 单次创作 | 本次发散的候选、被否决想法 |
| Skill | 跨会话（IR memory.retention=skill） | Failure Memory + 用户偏好 |
| Project / Global | 后续阶段 | 品牌级规则 / 全局规范 |

### Failure Memory（负知识）

被否决的创意 + 否决理由，逐渐形成越来越懂"不要做什么"的 skill：

```json
{
  "idea": "用'月入十万'做钩子",
  "reasons": ["与克制人设冲突", "触发 too-commercial 防御"],
  "failure_type": "too-commercial"
}
```

DIVERGE 阶段读取 Failure Memory：命中历史失败模式的候选直接降权，JUDGE 阶段对照检查。

### Preference 解析（用户反馈 → 规则）

用户说"这稿子太 AI 了"，不是记录这句话，而是解析为可执行偏好：

```
feedback（"太AI了"）
  ↓ symptom（genericPhraseTolerance 被突破）
  ↓ inferred preference（句长均匀度容忍 ↓、抽象词容忍 ↓）
  ↓ future adjustment（increase-concreteness / increase-rhythm-variance）
```

解析后的偏好写入 memory.capture.user_preferences，下次 JUDGE 的惩罚规则自动收紧。**禁止只存原文不解析**——那是聊天记录，不是记忆。

---

## §7 判断回路的最低配置

一个没有判断回路的"创意 skill"，无论风格描述多精确，都只是模板生成器。C4 生成产物时，runtime.md 必须包含：

- [ ] 至少 3 个评分维度 + 对应权重（源自 success_criteria/principles）
- [ ] pairwise 比较开关（默认开）
- [ ] Critique 四要素格式（What/Why/Where/How）
- [ ] Revision 流程（diagnose→locate→plan→partial fix→re-judge）+ preserve 列表
- [ ] max_rounds 上限 + 停止条件
- [ ] **独立评价器配置（v3.1）**：Judge B 与 Generator/Judge A 的分离层级（perspective/prompt/model）+ revision_gain 独立口径
- [ ] **决策裁决顺序（v3.1）**：rejection > exceptions > tradeoffs > priorities > 加权分；分差 < 0.1 时裁决权移交 policy
- [ ] Style Drift 检测 + correction 优先于重生成
- [ ] anti-pattern 命中 → penalty（critical → reject）
- [ ] Finalize 不重新发散

缺任何一项，C5 Layer 3 判 CONDITIONAL 并回 Pass C3。

---

## §8 运行时对象：Candidate

创意在 Runtime 内不只是文本——**创意本身 + 为什么这么做，必须同时存在**（否则 Judge 无法解释评分、Critique 无从定位、Style Drift 无对照基准）。

```
Candidate
├── id                    # 候选标识
├── content               # 创意文本
├── territory / angle     # 来自哪个母题/角度（DIVERGE 产出时写入）
├── rationale             # 为什么这么做（STRATEGIZE 产出时写入）
├── score                 # JUDGE 评分（维度分 + 总分）
├── decision              # 决策裁决记录（命中哪条 rejection/tradeoff/priority，v3.1）
├── judgment              # JudgmentResult（scores/strengths/weaknesses/recommendation）
├── style_fingerprint     # 本候选的实测指纹（Style Drift 检测的对照物）
├── independent_scores    # Judge B 盲评（pre/post）——Revision Gain 的唯一合法来源（v3.1）
└── revision_history      # 修订记录（critique 摘要 + preserve/fix 清单 + re-judge 分数）
```

**强制规则：**

1. JUDGE/Critique/Revision 的所有输入输出都以 Candidate 为单位流转，禁止退化成裸文本传递——裸文本丢失 rationale 后，Compare 阶段无法计算 Revision Gain 的归因
2. `revision_history` 每轮追加（不覆盖），它是 Finalize 向用户解释"为什么选这版"的依据
3. FILTER 阶段去重时，被合并的候选保留其 rationale 进胜者的合并说明——发散痕迹是可审计的
4. `decision` 必填于 FINALIZE 胜者——引用命中的 policy 条目作为选择理由，与加权分并列展示（v3.1）

---

## §9 从 Memory 到 Learning（v3.1）

MEMORY_UPDATE 记录反馈，**记录不等于学习**。`learning.enabled=true` 时，MEMORY_UPDATE 的下游接 Skill Mutation Loop（能力演进闭环）：

```
MEMORY_UPDATE（反馈记录）
  → Pattern（≥3 次同类反馈）
  → Capability Delta → Candidate Skill vNext
  → Benchmark 回归（benchmark_runner.py）
  → Human Approval → Skill 版本升级
```

完整规则（单例不改规则 / fingerprint 不许 mutation 修改 / 收紧容易放松难 / 禁止静默升级）：📍 [creative-learning.md](creative-learning.md)
