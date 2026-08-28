# Creative Extraction — Pass C1/C2 创造能力抽取

**加载时机：** 📍 执行到 Pass C1/C2 时加载。

覆盖：Resolved Intent、Context Model、语义分块、五提取器、Style Fingerprint 构建、Example Mining、证据溯源。

---

## §1 Pass C1 — Resolved Intent（意图解析）

### 表面请求 ≠ 真实创作意图

用户说"写标题"，实际任务可能是"提高点击 + 建立人设 + 避免广告感"。C1 必须产出 resolved intent：

```
表面请求: "帮我写 10 个小红书标题"
     ↓ 为什么（追问或从源材料推断）
真实意图: "用标题筛选出想辞职创业的人，同时让老粉觉得我还是那个人"
     ↓
primary_goal: 精准筛选目标受众并保持人设一致性
success_criteria: ["目标人群 3 秒内自我对号", "老粉不觉得变味", "无标题党感"]
```

### 解析规则

1. **primary_goal 必须是"为什么"层面的答案**，不是"做什么"的复述
2. **success_criteria 是 C3 judgment.dimensions 的直接来源**——写得越可判断，判断回路越有效。"要有感染力"不可判断；"前三秒出现具体事实"可判断
3. 源材料（访谈/旧 skill）里专家的抱怨（"我不要那种感觉"）是真实意图的最强证据，标注 explicit
4. 无法解析真实意图时，在 IR 中标注并降 confidence，不猜测填充

---

## §2 Pass C1 — Context Model（场景解析）

**同一主题在不同场景下完全不同**：创业导师 vs 餐饮老板 vs 品牌官方账号写"失败"，是三种内容。

### 六维场景模型

| 维度 | 提取来源 | 典型问题 |
|------|---------|---------|
| `person` | 自我介绍、访谈、旧 skill 人设章节 | 他是谁？经历过什么？信什么？ |
| `brand` | 品牌资料、定位文档 | 品牌在哪个位置说话？ |
| `audience` | 受众分析、评论区、用户反馈 | 读者想要什么？怕什么？会拿什么理由拒绝？ |
| `platform` | 平台规范、爆款结构分析 | 平台用户行为决定内容结构（前3秒/前两行） |
| `market` | 竞品分析 | 同类内容都长什么样？（决定差异化方向） |
| `cultural_context` | 文化语境 | 当前受众的集体情绪（对"人设包装"反感） |

### 规则

- 源材料没有的维度留空，**不编造**。audience.objection（用户拒绝理由）缺失时在诚实边界声明——没有 objection 模型的文案 skill 会无视受众的心理防御
- person.beliefs（信念）比 person.identity（身份）更值钱：身份决定"写什么"，信念决定"怎么写"

---

## §3 语义分块（Creative Semantic Chunking）

**传统按 token 切段对创造资料无效。** 按 1000 token 切会把一条原则劈成两半，把 before/after 对拆散。

### 按语义类型分块

| Chunk 类型 | 识别信号 | 去向 |
|-----------|---------|------|
| `[PRINCIPLE]` | "我从来都是先…再…"、"一定要"、"不要直接…" | principles |
| `[EXAMPLE]` | 完整作品文本（好/坏/改前/改后） | examples |
| `[STYLE]` | 大段连续语料（本人的实际作品） | style 分析语料 |
| `[CASE]` | 带上下文的创作故事（为什么这么改） | heuristics / principles.rationale |
| `[RULE]` | 字数/格式/法务硬性要求 | constraints.hard |
| `[STORY]` | 经历叙述（失败/转折） | context.person.experience |
| `[REJECTION]` | 否决记录（"这个不行，太用力了"） | anti_patterns / failure memory 的金矿 |

### 分块规则

1. **before/after 对必须保持成对**——拆散等于丢失最高价值数据（直接揭示 Expert Judgment）
2. **否决记录单独成块**，不并入 example——"被否决的方案 + 否决理由"是判断回路的训练核心
3. 转写/OCR 来源的块继承 Ingestion 置信度（evidence secondary），影响 C2 的 origin 标注

---

## §4 Pass C2 — 五提取器

### 4.1 Principle Extractor（原则提取）

**Principle ≠ 规则。** 判据：违反它时产物是"不好"，还是"错误"？前者是原则，后者是约束。

```
"标题不能超过20字"                    → constraints.hard
"先让读者感受到问题，再给答案"          → principles
"小红书正文 ≤ 1000 字"                → constraints.hard
"不证明自己优秀，证明别人都一样"         → principles（甚至是 constraints.creative）
```

每条原则必填：

| 字段 | 要求 |
|------|------|
| `statement` | 可执行的创作哲学（不是口号） |
| `rationale` | **为什么**——专家能力最有价值的部分藏在"为什么"而非"怎么写"。源材料没有就标 inferred 并降 confidence |
| `applies_when` | 适用条件。同一原则在不同场景可以有例外 |
| `priority` | critical/high/medium/low（冲突时裁决顺序） |
| `source_refs` | 溯源（见 §7） |

### 4.2 Style Extractor（风格提取）

**禁止形容词堆砌**（"高级/克制/有文学感"），必须结构化为 Style Grammar + Fingerprint。

提取流程（v3.1：Linguistic/Structural/Semantic/Pattern 四层分析由 `scripts/style_analyzer.py` 可执行承载）：

```
Corpus（本人实际作品，非本人谈创作的文字）
  ↓ python3 scripts/style_analyzer.py corpus/*.md --json fingerprint.json
  ↓ Linguistic Analysis    句长分布/词频/标点/重复/问句（raw_measurements 可人工复核）
  ↓ Structural Analysis    段落长度/开头方式/推进结构/收尾方式/留白
  ↓ Semantic Analysis      抽象词 vs 具体名词比例/情绪词/CTA/总结句
  ↓ Pattern Detection      隐喻/类比/夸张/第一人称比例
  ↓
Style Grammar（结构化描述，C2 撰写）
+ Style Fingerprint（实测 12 维数值向量 + fingerprint_provenance 溯源，分析器产出）
```

**Style Fingerprint 构建（12 维，见 schema）：**

1. **v3.1：数值必须来自实测**——运行 style\_analyzer，禁止手填。产出的 `fingerprint_provenance`（tool/method/corpus\_size/measured\_at）随 fingerprint 一起写入 IR；full 模式缺失 provenance 会被 validate\_creative\_ir.py WARN（#9）
2. **v3.2：裸数字不可验证，逐维证据对象**——分析器同时产出 `style.measurements`（每维 value + sample\_size + confidence + measurement 方法名）与 `style.style_confidence`（corpus\_size / feature\_coverage / overall\_confidence）。`0.81` 没有意义；`0.81, sample=1240, confidence=0.93, measurement=concrete-noun-ratio` 才能被验证，也才能支撑 Style Drift / Benchmark / Regression。full 模式缺 measurements → 校验器 FAIL（V1）
3. **Weighted Style Distance（v3.2）**：`Σ(|Δfeature| × confidence) / Σ(confidence)`——样本不足的维度自动降权，不会让低置信特征主导漂移判定；无 measurements 时退化为等权
4. **词表测量是启发式，不是语义理解**——metaphor/emotional 维度基于显式标记词，会低估不用标记词的隐喻/克制表达（此类零命中维度 confidence 上限 0.4）；分析器输出自带 method 声明，须如实进 IR（不洗白为"精确测量"）
5. **刻意的参差是风格信号**：`sentence_variance` 高不是缺陷。均匀句长是 AI 腔信号——目标风格句长越均匀，`ai_pattern_risk` 基线越高
6. 语料不足（分析器判定 corpus\_sufficient=false，即 <3 篇或 <1500 字）：只填有把握的维度，其余留空 + 降 confidence；style\_confidence.overall\_confidence < 0.6 时 Style Drift 阈值放宽 + 建议人工复核
7. `ai_pattern_risk` 决定 Judge 的 AI-penalty 起点严度：目标风格本身越接近模板化表达，惩罚越严
8. 运行时 Style Drift 检测与编译期用**同一测量逻辑**（style\_analyzer 的 analyze\_text + normalize），保证目标指纹与生成指纹同构可比

### 4.3 Example Miner（示例挖掘）

从资料中自动寻找价值排序（高→低）：

```
专家修改前 → 专家修改后     （直接揭示 Expert Judgment，最高价值）
A 不好 / B 更好 / 为什么    （contrastive，示范学习材料）
被否决的方案 + 否决理由      （negative + 失败知识）
单纯好例                    （语料价值，判断价值低）
```

挖掘规则：

1. 修改痕迹识别信号："改一下"/"删掉"/"这版好多了"/文档批注/版本对比
2. 每个示例必填 `explanation`（为什么好/为什么坏）——没有解释的示例只是语料
3. `linked_principles` 把示例与原则互相锚定：判断回路评估时按此索引相关原则

### 4.4 Anti-pattern Miner（反模式挖掘）

大量 AI 内容失败不是因为不知道怎么做好，而是**太容易走向模板化**。每个 anti-pattern 必填：

- `detection_signals`：可识别的文本信号（"今天给大家分享"、"你是否也有这样的困扰"）——没有信号的 anti-pattern 无法进入判断回路
- `correction`：纠正方向——只报问题不给方向的 anti-pattern 让 Revision 无从下手
- `severity`：critical 级别的命中应直接触发 reject 候选

挖掘来源优先级：专家否决记录（explicit）＞ 好坏对比中的坏例模式（inferred）＞ 通用 AI 腔清单（heuristic，最后手段）。

### 4.5 Heuristic Extractor（启发式提取）

承载专家的**模糊经验**——"这个标题太用力了"无法编译成硬规则，编译成"信号→倾向→纠正"：

```json
{
  "id": "H1",
  "signals": ["大量最高级形容词", "绝对化承诺", "没有事实支撑的自我赞美"],
  "tendency": "negative",
  "strength": 0.8,
  "correction": "将结论改写成具体事实或真实经历",
  "rationale": "用力过猛与克制人设冲突，触发受众的推销防御"
}
```

规则：`strength` 反映专家表达的确定度（"我从来受不了"= 高，"有时候好像"= 低）；correction 是方向不是处方。

---

## §5 Creative Strategy（创意策略链，条件提取）

仅 advertising/branding/campaign/IP 类任务执行：

```
Problem（要解决的核心问题）
  → Tension（张力：受众想听真话，但博主怕说真话掉粉）
  → Insight（洞察：示弱是创业者内容里最稀缺的供给）
  → Territories（创意母题：truth / anti_category — Divergence 阶段的发散轴）
  → Angles（切入角）
  → preferred_direction（专家偏好方向）
```

`territories` 提供发散轴，喂给 judgment 的发散配置（creative-extraction §6）：发散按边际收益停止（`stop_when_marginal_gain_below`），不强制母题数量——高发散类型（naming/advertising）调高 `min_territories`/`target_territories`，强方向单一的品牌定位可为 1。

---

## §6 发散配置（Generation Config）

解决"AI 所谓的 10 个创意其实只是一个创意换 10 种说法"。v3.1 起发散为**边际收益制**——固定数量会制造假发散（"一个真正强的方向，胜过五个被迫制造出来的方向"）：

| 字段 | 规则 |
|------|------|
| `divergence.min_territories` | 母题数下限（默认 1）。naming/advertising 等高发散类型建议 2；品牌定位/个人表达可为 1 |
| `divergence.target_territories` | 母题数目标（默认 3）。达到后评估边际收益，不为凑数继续 |
| `divergence.stop_when_marginal_gain_below` | 边际收益阈值（默认 0.15）：新增母题的最佳候选分数提升低于此值 → 停止。同母题换说法不产生边际收益，被自然拦截 |
| `diversity.minimum_distance` | 候选间最小差异度（用 Fingerprint 距离近似），低于此值合并/删除——这是 **Diversity** 校验；注意 Diversity ≠ Novelty（见 creative-compiler.md §C5 三参照系） |
| `selection.shortlist_size` | 进入 Critique/Revision 的候选数，一般 2-3（全量修订成本失控） |

---

## §7 证据溯源（origin 四级）

每条提取的知识携带 `source_refs[].origin`：

| origin | 含义 | 典型场景 |
|--------|------|---------|
| `explicit` | 原文直引（专家原话/作品原文） | 访谈文本、作品语料 |
| `inferred` | 编译器从上下文推断 | 跨段落归纳的模式 |
| `heuristic` | 启发式归纳 | 多个案例的共同模式 |
| `generated` | 模型生成补充 | 源材料缺口处的合理推断 |

**核心原则：Compiler 推断出来的东西不能伪装成专家原话。**

1. `explicit` 必须带 `source_text` 摘录；`inferred`/`generated` 的 source_text 留空
2. origin 分布影响 `meta.confidence`：explicit 占比高 → confidence 高；generated 占比高 → confidence 低 + 诚实边界声明
3. `source_refs.document_id` 必须在 `provenance.source_documents` 中登记（validate_creative_ir.py 强制校验）
4. 冲突保留：同一主题的矛盾原则（如"要简洁" vs "要有细节"）不强行统一——保留两条 + `applies_when` 区分场景，交由 priority 裁决
