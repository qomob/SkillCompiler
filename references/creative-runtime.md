# Creative Runtime — 判断回路规范

**加载时机：** 📍 Pass C3 设计判断回路配置、Pass C4 生成产物中的 runtime.md 时加载。本文件同时是 Creative Skill Package 内 `references/runtime.md` 的规范来源。

**定位：** 判断回路（Judge + Critique + Revision）是创造型 skill 从"会模仿"到"会创作"的分水岭。没有判断回路的"创意 skill"只是带风格提示词的生成器。

**v3.1 三处升级：** ① Judge 从"评分器"升级为"决策器"（policy 层，§2）；② Revision Gain 从自证升级为独立评价（§4）；③ 闭环延伸到 LEARN——Memory 记住发生了什么，Learning 把反馈变成能力变化（§9）。

---

## §1 运行状态机

创作不是一次函数调用，是有状态的流程：

```
INIT → UNDERSTAND → CONTEXTUALIZE → BRIEF → STRATEGIZE
     → DIVERGE → FILTER → JUDGE ──┬─→ FINALIZE → MEMORY_UPDATE ─→ LEARN*
                                  ↑                              （条件：达到升级门槛）
                          CRITIQUE → REVISE → COMPARE
```

| 状态 | 职责 | IR 来源 |
|------|------|--------|
| `UNDERSTAND` | 解析用户请求的真实意图（表面请求 vs 真实意图，同 C1 逻辑） | intent |
| `CONTEXTUALIZE` | 召回场景：人/品牌/受众/平台 | context |
| `BRIEF` | 合成 Creative Brief（本次创作的具体约束） | intent + context + constraints |
| `STRATEGIZE` | 选创意方向（Territory/Angle） | creative_strategy |
| `DIVERGE` | 边际收益发散：按 territory 发散候选，**新增母题的最佳候选提升 < stop_when_marginal_gain_below 即停**，不硬凑数量（v3.1） | generation.divergence |
| `FILTER` | 硬约束过滤 + 最小距离去重（同母题换说法合并） | constraints.hard + diversity |
| `JUDGE` | **决策 + 评分**：先查 policy（tradeoffs/decision_rules/一票否决），无命中才回退加权分 + 成对比较 | judgment + policy |
| `CRITIQUE` | 对 revise 候选产出结构化批评（What/Why/Where/How） | judgment + anti_patterns |
| `REVISE` | 按批评局部修改，不重写 | revision |
| `COMPARE` | 与前一版对比，**由独立评价视角计算 Revision Gain**，决定继续/停止（v3.1） | revision.stop_conditions |
| `FINALIZE` | 选最终版 + 整理输出 + 遵守输出契约。**不能重新发散** | output |
| `MEMORY_UPDATE` | 记录决策/否决/用户偏好（Failure Memory） | memory |
| `LEARN` | 条件触发：解析后反馈积累达到阈值 → 产出 vNext 升级提案（不自动落盘，见 §9） | learning |

**状态映射到 SKILL.md 的 Creative Workflow 章节**——C4 生成产物时按此状态机渲染工作流。

**DIVERGE 的边际收益规则（v3.1，取代 territory_count≥2 硬性发散）：**

```
发散第 N 个母题 → 产出候选 → 快速评估
边际收益 = 该母题最佳候选分 - 已有全局最佳候选分
边际收益 < stop_when_marginal_gain_below（默认 0.15）→ 停止发散
```

- `min_territories`（下限，默认 1）：naming/advertising 等高发散类型建议 2；品牌定位/个人表达可为 1——**一个真正强的方向，胜过五个被迫制造出来的方向**
- `target_territories`（目标，默认 3）：达到后评估边际收益，不为凑数继续
- 假发散（同母题换说法）不产生边际收益，被此规则自然拦截——这比固定数量更符合创造规律

**Creative Search Tree（v3.2）：** Runtime 内部以树而非平铺列表组织发散——比 "Generate 10" 更接近真正的创意过程，也让边际收益可归因到具体 territory：

```
Brief
├── Territory A ── Idea A1 / A2 / A3      （最佳候选分 0.72）
├── Territory B ── Idea B1 / B2 / B3      （最佳候选分 0.81，边际收益 +0.09）
└── Territory C ── Idea C1 / C2            （最佳候选分 0.83，边际收益 +0.02 < 0.15 → 停）
```

Candidate 对象的 `territory` 字段记录其树位置；FILTER 合并/去重与 LEARN 归因都沿树回溯。

**quick 运行模式**（运行时，区别于编译模式）：UNDERSTAND → DIVERGE → JUDGE → FINALIZE，跳过 CRITIQUE/REVISE/COMPARE。仅限低价值高频任务。

---

## §2 Judge 规范

**Judge 不重新生成内容。它只做：Observe → Score → Compare → Explain。**

**创造能力不是 Score Function，是 Decision Policy（v3.1）。** 加权评分是 tiebreaker 而非决策者——把专家判断简化成加权评分函数，会在关键取舍上系统性出错：

```
A：原创性 9  相关性 9  品牌一致性 9     → 加权分更高
B：原创性 7  相关性 8  品牌一致性 10    → 创意总监会选 B
                                          因为 B 抓住了更重要的战略矛盾
```

### 决策流程（policy 优先，评分为兜底）

```
Observe（逐维度观察候选，引用具体文本证据）
  ↓
① 一票否决检查：policy.rejection_reasons / anti_patterns critical / hard constraint 命中 → 直接 reject
② 决策规则检查：policy.decision_rules 条件命中 → 按规则行动（可覆盖总分排序）
③ 冲突裁决：候选间存在维度冲突且 policy.tradeoffs 命中该冲突场景 → 保 prefer 维度，容忍 tolerate_loss
④ 无 policy 命中 → 加权分排序 + pairwise 比较（原 v3.0 流程）
  ↓
Explain — 输出 strengths / weaknesses / risks + 建议（keep/revise/reject）+ **决策依据（走了哪条 policy / 为什么总分高的没选）**
```

**tradeoffs 示例（Creative Policy 层，C3 产出）：**

```json
{
  "when": "originality_vs_clarity@campaign_concept",
  "prefer": "originality",
  "tolerate_loss": "clarity",
  "rationale": "没有记忆点的清楚，等于没有传播价值"
}
```

- Judge 的 Explain 必须声明决策路径——"B 抓住了战略矛盾，依据 tradeoff T2 优先于 A 的总分优势"。不声明依据的决策等于黑箱抽卡
- advertising/branding/naming 类必须提供 policy（validate_creative_ir.py #10）；其他类型建议提供——冲突场景是专家判断力密度最高的地方

### 评分流程（④ 的兜底路径）

1. **Observe** — 按 judgment.dimensions 逐维度观察候选，引用具体文本证据（"第 2 段'亏了 47 万'是具体事实"）
2. **Score** — 各维度 0-1 评分，加权求和。权重来自 IR judgment.weighting
3. **Compare** — pairwise 成对比较（见 §3）
4. **Explain** — 输出 strengths / weaknesses / risks + 建议（keep/revise/reject）

### 维度设计规则（C3 阶段）

- dimensions 从 `intent.success_criteria` 与 `principles` 派生，**禁止只设一个笼统 "quality"**，至少 3 个
- 好维度是可观察的："specificity"（具体事实密度）优于 "quality"（什么都测不到）——validate_creative_ir.py #5 将 quality/good/better 类空洞维度判 FAIL（结构正确 ≠ 有能力）
- weighting 与 dimensions 一一对应，和 = 1.0（validate_creative_ir.py 强制）；**完全均匀的权重 = 没做判断**（#6 WARN，除非以 tradeoffs 显式声明取舍）

### 惩罚规则

anti-pattern 命中 / AI 腔 / 风格漂移的扣分独立于维度评分：

| penalty | 触发 | 建议权重 |
|---------|------|---------|
| `ai_pattern_penalty` | 命中任一 anti_patterns.detection_signals | severity critical 命中 → 直接 reject，不进 Revision |
| `cliche_penalty` | 命中 style.negative_signals | 0.2 |
| `constraint_violation` | 违反 hard constraint | 违反 → reject |
| `style_drift_penalty` | Style Distance 超阈值 | 0.3（见 §5） |

`minimum_quality`：低于此分直接 reject，不浪费 Revision 轮次。

**评分只是辅助——Score + Reason + Comparison 三者一起工作，不能把创造完全数学化。** 没有文本证据支撑的分数视为无效评分。

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

### Revision Gain 与独立评价（v3.1）

**自证循环警告（Evaluator Leakage）：** Generator、Judge、Critique、Revision 若用同一套标准评自己改的东西，Judge 会天然偏爱自己的修改——`revision_gain = +1.0` 可能只说明"评价器更喜欢自己修改后的答案"，不代表作品真的变好了。

**修订版评价协议：**

```
Generator 产出 initial
  → Judge A 评分（initial_score，沿用 judgment 配置）
  → Critique（What/Why/Where/How）
  → Revision（局部修改）
  → Judge B 独立 re-judge —— 评价视角与修订方解耦：
       · 不展示 Critique 摘要与 Expected Improvement（防止"确认预期"污染）
       · 按同一 dimensions 独立 Observe → Score，不带修订说明
  → revision_gain = independent_post_score - initial_score
```

- **独立性的最低要求是信息隔离**：Judge B 只看修订后的文本，不看"改了哪里/预期改善什么"。同模型不同视角可接受（工程现实），同视角同上下文不可接受
- `revision_gain ≈ 0`（在独立评价下）→ Critique/Revision 真的没起作用（本次运行质量信号 + 编译期 C5 检查项）
- `revision_gain < 0` → 修订让产物变差，回滚到前一版
- 停止条件（任一满足即停）：达到 `revision.stop_conditions` 之一 / `max_rounds` 用尽 / gain 趋零（连续修订收益递减）

### Revision Efficiency 与边际收益收敛（v3.2）

改一次有成本（轮次预算 + 丢失已达标维度的风险）。只看 gain 不看 cost 会把轮数烧在递减收益上：

```
Revision Efficiency = Revision Gain / Revision Cost（每轮 cost 记 1）

Round 1:  +0.8 / 1.0   → 继续
Round 2:  +0.2 / 1.0   → 继续
Round 3:  +0.05 / 1.0  → 本轮 gain < marginal_gain_threshold（默认 0.15）→ 停止
```

- `revision.marginal_gain_threshold`（schema v3.2）比单纯 max_rounds 更符合收益递减规律：**本轮提升 < 阈值即停**，未用完的轮数预算不硬烧
- 两级收敛条件并存：marginal_gain（收益维度）+ max_rounds（成本维度），先触发者生效

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

**前提（v3.1）：目标 Fingerprint 必须是实测值。** 编译期由 `scripts/style_analyzer.py` 从语料测得（携带 fingerprint_provenance 溯源）；运行时对生成内容计算同构向量（同一工具的 `analyze_text + normalize` 逻辑）。拿生成内容对比一个拍脑袋的基准，漂移检测全程失效。

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

- [ ] 至少 3 个评分维度 + 对应权重（源自 success_criteria/principles，禁空洞维度如 quality/good）
- [ ] **决策层：一票否决 + tradeoffs 冲突裁决（存在 policy 时）+ 决策依据声明**（v3.1）
- [ ] pairwise 比较开关（默认开）
- [ ] Critique 四要素格式（What/Why/Where/How）
- [ ] Revision 流程（diagnose→locate→plan→partial fix→re-judge）+ preserve 列表
- [ ] **re-judge 信息隔离：Judge B 不看 Critique 摘要与预期改善说明**（v3.1，V3 检查项——full 模式 rejudge_isolation=false 校验器 FAIL）
- [ ] max_rounds 上限 + **边际收益停止**（marginal_gain_threshold 或 stop_conditions，V4 检查项）
- [ ] Style Drift 检测 + correction 优先于重生成（目标 fingerprint 须为实测值）
- [ ] anti-pattern 命中 → penalty（critical → reject）
- [ ] Finalize 不重新发散
- [ ] 发散为边际收益制（min/target/stop_when_marginal_gain_below），不硬凑母题数（v3.1）

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
├── judgment              # JudgmentResult（scores/strengths/weaknesses/recommendation）
├── style_fingerprint     # 本候选的实测指纹（Style Drift 检测的对照物）
└── revision_history      # 修订记录（critique 摘要 + preserve/fix 清单 + re-judge 分数）
```

**强制规则：**

1. JUDGE/Critique/Revision 的所有输入输出都以 Candidate 为单位流转，禁止退化成裸文本传递——裸文本丢失 rationale 后，Compare 阶段无法计算 Revision Gain 的归因
2. `revision_history` 每轮追加（不覆盖），它是 Finalize 向用户解释"为什么选这版"的依据
3. FILTER 阶段去重时，被合并的候选保留其 rationale 进胜者的合并说明——发散痕迹是可审计的

---

## §9 Learning Loop：从 Memory 到 Capability Evolution（v3.1）

**Memory ≠ Learning。** Memory 记住发生了什么（Failure Memory / 用户偏好）；Learning 把反馈变成**能力变化**——skill 从"静态文件"变成"会进化的能力"。

```
真实使用
  ↓
Feedback（采纳/否决/"太AI了"式模糊反馈）
  ↓ 解析（§6 Preference 解析；禁止只存原文）
Pattern（同类反馈 ≥ min_feedback_count，默认 3 条 → 不是孤例）
  ↓
Preference / Rule Update（惩罚收紧、权重调整、anti-pattern 新增）
  ↓
Capability Delta（target_ref: from → to + evidence[]——无证据的能力变化禁止落盘）
  ↓
Candidate Skill vNext（升级提案，含全部 delta 清单）
  ↓
Benchmark Gate：scripts/benchmark_runner.py 对比 vNext vs 当前版，核心指标无退化
  ↓
Human Approval Gate：人工批准（LLM 自评偏好 ≠ 人的验收）
  ↓
Skill vNext 落盘（version +1，capability_deltas 归档，可回溯"为什么改"）
```

**三条硬规则：**

1. **未过双门不落盘**——benchmark 无退化 + 人工批准，二者缺一，vNext 停留在提案状态。"修了一个偏好，毁掉整体风格"是学习回路最常见的失败
2. **每个 delta 带证据**——capability_deltas.evidence[] 指向具体反馈记录/基准报告。拍脑袋的"优化"没有资格进入 vNext
3. **回归可回退**——vNext 落盘后任何指标异常，按 capability_deltas 逐条回滚，而不是重新编译

产物落点：learning 配置写入 Creative IR `learning` 字段；运行中的 feedback_log / capability_deltas 存于 skill 包的 memory 文件；LEARN 状态只在门槛达成时触发（高频触发 = 每次都重编译 = 无稳定基线，benchmark 对比失效）。

**Learning 对象结构（v3.2 对齐 schema）：**

- `capability_deltas`（Skill Evolution 最小单位）：`target`（style/principle/heuristic/decision_policy/anti_pattern/judgment/generation）+ `operation`（add/remove/increase/decrease/replace）+ `magnitude` + `rationale` + `evidence[]`（空证据校验器 FAIL）
- `mutation_proposals`（提案打包）：`version_from → version_to` + `changes[]`（delta 引用清单）+ `reason` + `status` 状态机（proposed → benchmark_passed → approved | rejected）
- `upgrade_gate`：benchmark_required（V6 硬门，false 校验器 FAIL）+ human_approval_required + min_feedback_count + mutation_threshold（同类反馈占比阈值，默认 0.3——单次反馈即改 skill 是过拟合）

---

## §10 Runtime Debug Trace（v3.2）

Runtime 的每步决策必须可回放调试——"输出不好"时能定位坏在链路哪一环，而不是笼统重跑。产物 runtime.md 应声明按此链记录 trace（写入 skill 的 memory 文件）：

```
Intent → Context → Creative Brief → Strategy
  → Territories（搜索树：每母题候选 + 边际收益）
  → Candidates（含 fingerprint）
  → Diversity（候选间距离）→ Novelty（三参照系，scripts/novelty_detector.py）
  → Decision Policy（命中的 tradeoff/rule/否决 + 决策依据声明）
  → Judge（维度分 + pairwise 结果）
  → Critique（What/Why/Where/How）
  → Revision（preserve/fix 清单 + 每轮独立 gain + marginal_gain 判断）
  → Independent Evaluation（Judge B 分数 + 隔离声明）
  → Final（选择依据）
  → Learning Signal（本次运行产生的反馈/否决记录）
```

排查顺序（"产物不好"时的定位链）：Style 基准是否实测 → Policy 是否参与决策 → Judge 是否识别专家偏好 → Critique 是否有效诊断 → Revision 是否真改善（独立 gain）→ Benchmark 是否测得到差异。**禁止跳过定位直接堆轮次或重抽卡。**
