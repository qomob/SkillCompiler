# Changelog

## v3.2.1 — 生产部署整备：可执行层实测回归 + 契约漂移清零（2026-08-28）

**v3.2.0 落地后的部署前整备：对全部 5 个脚本做 fixtures 端到端实测（此前仅 validate_creative_ir 有测试记录），修复实测暴露的 2 处脚本缺陷；清零 v3.1/v3.2 升级后残留在 README/SKILL/reference 的 8 处旧口径（协议一致性回归）。无 schema 变更、无新文件、无架构变更。**

### Fixed: scripts/benchmark_runner.py `--variants` 与文档契约不符（实测发现）
- 文档与 CHANGELOG 声明 `--variants label=dir` 可重复，实际实现为 `nargs=2`：既不按 `=` 切分标签，也无法在一次调用中传入两个版本——四组对比协议（评审 §47/§54 的核心功能）实际不可运行。
- 修复为 `label=dir` 解析：支持 `--variants legacy=dir v31=dir`（同 flag 多 token）与 `--variants legacy=dir --variants v31=dir`（重复 flag）两种写法；纯目录输入从容错派生标签；`--baseline/--candidate` 旧 CLI 保持兼容。已用双 case × 双版本 fixtures 实测：四项指标矩阵、capability_gain（North Star）、per-case golden 断言（fingerprint 方向断言 / qualities / constraints）全部正常产出。

### Fixed: scripts/novelty_detector.py 多文件语料聚合偏差（实测发现）
- corpus_novelty 的多文件聚合为顺序对半平均 `(prev+next)/2`：3 篇语料时权重为 1/4、1/4、1/2（实测 mean 22.5 vs 正确 17.3），后读文件权重翻倍，corpus_novelty 随语料文件顺序漂移。
- 改为与 style_analyzer 一致的均匀平均（sum/n）。单文件行为不变。

### Fixed: 契约漂移清零（v3.1/v3.2 升级未同步到的 8 处旧口径）
- `SKILL.md`：编译模式表 2 处 `C5(全部四层)` → `C5(全部五层)`；Final Output "Pass C5 四层评估" → 五层（指标枚举同步补 novelty/diversity/llm_preference_proxy）。
- `README.md`：对比表/快速开始/管线表 3 处 "四层评估 / Human-proxy / 8 项指标" → "五层诚实评估 / LLM Preference Proxy / 9 项指标"。
- `references/creative-compiler.md`：管线图 "创意四层评估" → 五层；产物结构树 `runtime.md` 后误接 `strategy.md` 的树形字符修正。
- `references/creative-runtime.md`：2 处 `evidence_refs` → `evidence[]`（对齐 schema/校验器真实字段名）。
- `references/creative-extraction.md`：§5 残留 v3.0 的 "≥2 个 territory 强制跨方向发散" → 边际收益发散表述（territory_count≥2 已于 v3.1 废除）。
- `references/pass-6-validate.md`：Step 6.4b 与 Output Schema 2 处 `E1-E5` → `E1-E6`（E6 于 v2.3.0 引入但清单漏更）。
- `SKILL.md` footer 硬编码 `v3.1.0` → 与 frontmatter 版本对齐；`evals/trigger_cases.json` version 字段 3.0.0 → 3.2.1。

### Engineering: 工程卫生
- `.gitignore` 补 `__pycache__/`、`*.pyc`（scripts/ 下已存在被跟踪风险的 .pyc，已清理）。
- 全库 JSON（3 schema + category_patterns + trigger_cases）解析校验通过；全库 markdown 相对链接全量扫描无死链；description 698 字符（< ZCode 规范 1024 上限）、SKILL.md body 265 行（< 500 行渐进披露标准）。

### 验证记录（本版实测）
- style_analyzer：3 篇中文语料 → 12 维 fingerprint + measurements 逐维证据 + style_confidence + provenance ✓；`--compare` confidence 加权距离（双份 measurements 自动切换 weighted 模式）✓。
- validate_creative_ir：合法 advertising 型 IR（含 policy 全结构/learning 全结构）→ PASS(0)；V1 缺 measurements / V2 branding 空 tradeoffs / V3 rejudge_isolation=false / V6 benchmark_required=false 全部按预期 FAIL；#5 空洞维度 FAIL、#6 均匀权重 WARN ✓；quick 豁免与文件错误 exit 2 ✓。
- novelty_detector：四值输出 + 品类套路命中明细 ✓（修复后多文件语料均匀聚合）。
- benchmark_runner：双版本矩阵 + capability_gain 0.54（legacy 0% golden / 50% anti-pattern 命中 vs v31 100% / 0%，方向与构造一致）✓。
- validate_ir：非法 IR 8 错误 FAIL(1)、文件缺失 exit 2 ✓。

## v3.2.0 — Capability-Driven 完全体：证据层与收敛机制（2026-08-28）

**基于第二轮外部评审（"Creative Compiler v3.1 — Capability-Driven Edition"方案，51 节直接修改清单 + V1-V6 Capability Validation）。该评审与 v3.1.0 大量重叠（policy/learning/边际收益发散/Novelty 拆分/独立评价/benchmark runner 均已落地），本轮只补齐 8 处超出 v3.1.0 的精确增量。核心原则不变：不加新架构、不加新 reference 文件，只让已有机制产生可验证的行为。**

### Added: 逐维测量证据 style.measurements + style_confidence（评审 §14-17）
- `schemas/creative-ir-schema.json`：`style.measurements`（每维 value + sample_size + confidence + measurement 方法名）+ `style.style_confidence`（corpus_size / feature_coverage / overall_confidence）。采用评审推荐的"轻量 fingerprint 保留 + measurements 分离"方案——Runtime 消费 number，Analyzer 保留完整证据。
- `style_analyzer.py` v1.1.0：输出 measurements（12 维证据对象，词表零命中维度 confidence 上限 0.4——无法区分"真没有"与"不用标记词"）+ style_confidence。
- **Weighted Style Distance**：`Σ(|Δfeature| × confidence) / Σ(confidence)`——样本不足的维度自动降权，不主导漂移判定；`--compare` 在双方均有 measurements 时自动切换加权模式（无则退化等权）。

### Added: Novelty Detector + 品类套路库（评审 §19-21）
- `scripts/category_patterns.json`：五类（xiaohongshu/advertising/branding/founder-ip/naming）hooks/structures/claims/endings 套路簇，可扩展。
- `scripts/novelty_detector.py`：三参照系四值输出——candidate_novelty（vs 同批候选）/ category_novelty（vs 品类套路簇命中密度）/ corpus_novelty（vs 源语料实测指纹）/ overall_novelty（加权 0.3/0.5/0.2，缺分量重归一）。抓住"没抄任何一句但整体很套路"；诚实边界：测结构套路命中密度，非语义原创。

### Changed: policy 结构精确化（评审 §5-10）
- `priorities`：字符串数组 → 对象数组（dimension + priority 数值 0-1 + rationale）——priority 表冲突裁决优先级，不是评分权重。
- `tradeoffs.when`：字符串 → 对象（dimension_a × dimension_b + context），字符串形式兼容；新增 `tolerance`（可容忍受损幅度，超出回到全局优先级）。
- `decision_rules.action`：自由文本 → 枚举（keep/revise/reject/explore_more）+ `priority` 规则强度。
- 新增 `risk_tolerance`（novelty/ambiguity 的 level/value 风险分级）——Naming/Campaign 与日常文章不应同一风险水平。

### Added: Revision Efficiency 与边际收益收敛（评审 §25-26）
- schema：`revision.marginal_gain_threshold`（默认 0.15）+ `revision.rejudge_isolation`（V3 检查项，full 模式 false → FAIL）。
- [creative-runtime.md](references/creative-runtime.md)：Revision Efficiency = gain/cost 收敛示例（+0.8 → +0.2 → +0.05 停）；两级收敛（marginal_gain 收益维度 + max_rounds 成本维度）先触发者生效。

### Changed: capability_deltas 原子化 + mutation_proposals 状态机（评审 §31-35/38-39）
- `learning.capability_deltas` 升级为评审结构：target 枚举（style/principle/heuristic/decision_policy/anti_pattern/judgment/generation）+ operation 枚举（add/remove/increase/decrease/replace）+ magnitude + rationale + evidence[]（空证据 FAIL）。
- 新增 `learning.mutation_proposals`：version_from/to + changes[]（delta 引用）+ reason + status 状态机（proposed → benchmark_passed → approved | rejected）。
- `upgrade_gate` 新增 `mutation_threshold`（同类反馈占比阈值，默认 0.3——单次反馈即改 skill 是过拟合）。

### Changed: benchmark_runner v1.1.0 多版本 + capability_gain（评审 §45-49）
- `--variants label=dir` 可重复（A 原Prompt / B Legacy / C v3.0 / D v3.2 四组同题对比矩阵），旧 `--baseline/--candidate` CLI 兼容。
- 新增 `capability_gain` 汇总（North Star：最新版正向指标均值 - 基线，不是自评分）+ `--category` 集成 category_novelty。
- case expected 增强：`qualities`（应含特征）/ `constraints`（禁用词）断言。
- [creative-compiler.md](references/creative-compiler.md) 新增 Benchmark 四组协议（Justin 实验模板）：控制变量 + ≥60 cases + 重点看 D 是否胜 C + 六步排查链（勿说"还需要更多字段"）。

### Added: V1-V6 Capability Validation 对照（评审 §40-43）
- validate_creative_ir.py：V1 full 模式缺 style.measurements → **FAIL**（从 v3.1 WARN 升级，裸数字不可验证）；V2 三类高决策型缺 policy **或空 tradeoffs** → FAIL（从 WARN 升级）；V3 rejudge_isolation=false（full）→ FAIL；V4 修订无收敛条件 → WARN；V6 upgrade_gate.benchmark_required=false → FAIL。
- 新结构校验：measurements（value/measurement 必填）/ style_confidence / policy 对象化结构 / risk_tolerance / marginal_gain_threshold / mutation_proposals / capability_deltas。
- [creative-compiler.md](references/creative-compiler.md) 新增 V1-V6 对照表。

### Added: Runtime Debug Trace + Creative Search Tree（评审 §28/44）
- [creative-runtime.md](references/creative-runtime.md) 新增 §10 Debug Trace：15 步可回放决策链 + "产物不好"六步定位链（禁止跳过定位直接堆轮次/重抽卡）。
- §1 DIVERGE 补 Creative Search Tree（Brief → Territory → Idea 树结构，边际收益按 territory 归因，Candidate.territory 记录树位置）。

### Changed: 契约同步
- `SKILL.md` v3.2.0：Capability-Driven 完全体声明、Execution Rule 3 更新为 V1-V6、Gotchas #22-23（裸数字 fingerprint / 无 Regression Gate 的学习回路）。
- `schemas/trace-schema.json`：creative_evaluation 新增 novelty_detail（三分量明细）。
- `references/creative-compiler.md`：Creative Skill 最终定义 + 五层分工表（IR/Policy/Runtime/Evaluator/Learning）+ `Extraction × Representation × Decision × Execution × Evaluation × Learning` 公式；Novelty 三参照系标注可执行工具。
- `references/creative-extraction.md`：measurements 结构与 Weighted Style Distance 说明。
- `README.md`：v3.2 徽章 + 五项新能力 + scripts 文件结构。

### 设计取舍
- fingerprint 采用"轻量 number + measurements 分离"（评审推荐的第二种）：Runtime 热路径只读 number，证据层按需加载——避免每次 Style Drift 检查都解析证据对象。
- V1/V2 从 WARN 升级为 FAIL（full 模式）：评审明确"结构合法但 CAPABILITY FAIL"；quick 模式保留 WARN（快速通道不硬卡证据，但必须知情）。
- candidate/corpus novelty 不进 benchmark_runner（每版每 case 只有一个输出，无同批候选可比），由 novelty_detector.py 独立承接；runner 只集成 category_novelty（可静态计算）。
- 不落地 Capability Graph（评审 §36 自述"长期建议"）与 Justin 60-case 实数据（需真实语料与四版产物，属用户侧实验）——记录为下一阶段。

## v3.1.0 — Benchmark Edition：可执行能力层（2026-08-28）

**基于外部深度评审（结论：v3.0 是"架构成立、能力闭环尚未实证"的 Creative Compilation Framework，设计完成度 8 分 ≠ 创造能力提升 8 分）的五项 P0 能力升级。方向：停止 Specification Inflation（不再堆 IR 字段/reference），切换到 Benchmark-driven Implementation。North Star Metric："这个 Compiler 编译出来的 Skill，到底是不是比原来的 Skill 更会创作？"**

### Added: scripts/style_analyzer.py（P0-1 Style Analyzer）
- 语料 → 原始测量（句长分布 mean/median/variance/cv、具体/抽象比、第一人称、情绪/隐喻/叙事/商业标记、问句率、3-gram 重复率、短段率、AI 腔命中）→ 归一化 12 维 Fingerprint + fingerprint_provenance 溯源。
- 把 style.fingerprint 从 Schema-level claim 变成 Executable measurement——v3.0 规定了"不能拍脑袋"但没有提供"怎么不拍脑袋"的工具，此为最重技术债的清偿。
- `--compare fp_a.json fp_b.json` 直接输出 Style Distance / Style Fidelity（C5 与运行时 Style Drift 复用）。
- 诚实边界：词表匹配是启发式测量非语义理解（隐喻/情绪维度会低估不用标记词的表达），输出自带 method 声明；语料 <3 篇或 <1500 字输出 corpus_sufficient=false。

### Added: scripts/benchmark_runner.py（P0-4 Benchmark Runner）
- 回答 North Star：同一批 benchmark case，Legacy 方式与 Creative 编译产物各生成一次输出，Runner 对比两版输出（实测指纹保真 / anti-pattern 命中率 / golden 断言通过率）+ delta + per-case 明细。
- 构建时分析器定位：不执行 LLM 调用、不运行被测 skill，只消费已生成的输出（cases JSON + 两版输出目录 + Creative IR 作 oracle）。
- 不自动下"显著更好"结论——delta 规模与样本量由人判断；LLM/Human Preference（L4/L5）不在 Runner 范围。使用时机：编译器回归测试 / Learning Loop 升级门 / 向用户证明编译价值。

### Added: Creative Policy 决策层（P0-2）
- `schemas/creative-ir-schema.json` 新增 `policy` 顶层字段：priorities / tradeoffs（when+prefer+tolerate_loss+rationale）/ decision_rules / exceptions / rejection_reasons。
- 架构三分：Creative IR（描述能力）→ Creative Policy（描述冲突时怎么选）→ Creative Runtime（执行决策）。judgment 从"评分器"升级为"专家决策器"——创造能力不是 Score Function，是 Decision Policy；加权评分降级为 tiebreaker。
- [creative-runtime.md](references/creative-runtime.md) §2 重写：决策流程（一票否决 → decision_rules → tradeoffs 裁决 → 加权分兜底），Judge Explain 必须声明决策依据。

### Changed: Revision Gain 独立评价（P0-3，修复自证循环）
- Evaluator Leakage：Generator/Judge/Critique/Revision 同视角时，Judge 偏爱自己的修改，gain 恒正但作品未必变好。
- 修订版评价协议：Judge A（initial）→ Critique → Revision → Judge B 独立 re-judge（信息隔离：不看 Critique 摘要与 Expected Improvement）→ `revision_gain = independent_post_score - initial_score`。非独立评价的 gain 不可作为判断回路有效的证据。

### Added: Skill Learning Loop（P0-5，Memory ≠ Learning）
- `creative-ir-schema.json` 新增 `learning` 字段：feedback_log（必须 parsed）/ capability_deltas（必须 evidence_refs）/ upgrade_gate（benchmark_required + human_approval_required + min_feedback_count）。
- [creative-runtime.md](references/creative-runtime.md) 新增 §9：feedback → 解析 → pattern（≥3 条非孤例）→ preference/rule update → capability delta → vNext 提案 → benchmark + 人工批准双门 → 落盘。未过双门不落盘；每个 delta 带证据；回归按 delta 逐条回滚。状态机新增 LEARN（条件触发）。

### Changed: Originality 定义修正 → Novelty / Diversity 拆分
- v3.0 "Originality = 候选间最小距离"是定义错误（Candidate Distance ≠ Originality）：三个彼此不同但都很平庸的方案，该指标满分但毫无新颖性。
- 拆为：**Diversity**（发散有效性，候选间最小距离）+ **Novelty**（三参照系：距品类套路簇 + 距 AI 通用模式 + 距源示例）。C5 指标 8 项 → 9 项。

### Changed: 评价体系诚实化（Human-proxy → 分层）
- C5 四层 → 五层：L1 Structural / L2 Semantic / L3 Creative / L4 **LLM Preference Proxy**（模型偏好非人类偏好，禁止表述为"人类偏好"）/ L5 **Human Preference**（可选真人采集层，唯一终审，不能被 LLM 代替）。
- 每层附诚实声明（可靠度）。trace-schema 新增 novelty/diversity/llm_preference_proxy/human_preference 指标。

### Changed: 发散从固定数量 → 边际收益制
- territory_count≥2 强制发散会产生假发散（"一个真正强的方向，胜过五个被迫制造出来的方向"）。
- 新字段：min_territories（默认 1）/ target_territories（默认 3）/ stop_when_marginal_gain_below（默认 0.15）。同母题换说法不产生边际收益，被规则自然拦截。

### Added: Capability Validator（结构 Validator → 能力 Validator）
- [validate_creative_ir.py](scripts/validate_creative_ir.py) 新增 Capability 检查：#5 空洞维度（quality/good/better 类）→ FAIL；#6 权重完全均匀且无 tradeoffs → WARN（均匀分配 = 没做判断）；#7 空洞原则（"内容要精彩"式）→ WARN；#8 detection_signals 全部不可操作 → WARN；#9 full 模式缺 fingerprint_provenance → WARN（非实测指纹）；#10 advertising/branding/naming 缺 policy → WARN。
- 新字段结构校验：policy / learning / runtime_roles / fingerprint_provenance / divergence 边际收益三字段（target ≥ min、territory_count ≥ min、阈值 0-1）。

### Added: runtime_role 标注（字段齐全主义解药）
- schema 新增可选 `runtime_roles`（generation/judgment/revision/routing/evaluation/documentation 六角色）；[creative-compiler.md](references/creative-compiler.md) 提供 19 个顶层字段的缺省映射表；Pass 5 O10 瘦身依据改为"运行时消费关系"而非字段大小。

### Changed: 契约同步
- `SKILL.md` v3.1.0：v3.1 能力层声明 + North Star、C5 五层口径、知识资源表更新、Execution Rule 3 补 Capability 检查、Gotchas #18-21（自证循环 / 假基准指纹 / 均匀权重+Diversity≠Novelty / LLM Preference≠Human Preference）。
- `references/creative-compiler.md`：完整闭环图（Understand→Model→Create→Judge→Revise→Evaluate→Learn）、North Star 声明、IR 构建顺序补 policy/实测指纹/learning/runtime_roles、产物结构加 references/policy.md 与 tests/benchmark-cases.json、Golden Set 双格式、Benchmark Runner 协议、回归测试接 Runner。
- `references/creative-extraction.md`：Fingerprint 构建流程改为 style_analyzer 实测（含启发式局限如实进 IR）、发散配置表改边际收益制。
- `references/pass-5-optimize.md`：O10 保护项加 fingerprint_provenance/policy/capability_deltas；新增 runtime_roles 驱动的 documentation 字段瘦身规则。
- `schemas/trace-schema.json`：creative_evaluation 指标扩展。
- `README.md`：v3.1 徽章、判断回路图（决策器/边际收益/LEARN）、核心能力 7 项新增、评分口径。

### 设计取舍
- 不新增任何 reference 文件（评审警告 Specification Inflation）：Learning Loop 并入 creative-runtime.md §9，Benchmark 协议并入 creative-compiler.md，新增的只有两个可执行脚本。
- Runner 不下"显著更好"结论、Judge B 允许同模型不同视角（工程现实）但必须信息隔离、policy 对三类高决策型 WARN 而非 FAIL（creative-writing 等类型可无冲突裁决场景）——可执行性与诚实性优先于机械严格。
- 遗留（记录为下一阶段）：品类套路簇库（Novelty 第一参照系目前依赖 anti_patterns 词表近似）；benchmark 全流程端到端实测（需真实两版产物样本）；L5 Human Preference 数据采集协议。

## v3.0.0 — 双编译架构：General Compiler + Creative Compiler (2026-08-28)

**基于三份设计文档（Creative Skill Compiler v1/v2.0、Skill Compiler v2.0）的深度理解，将单一编译管线升级为双编译架构。核心主张：真正决定一个创造型 Skill 能不能从"会模仿"进化到"真的会创作"的，是它有没有自己的判断回路（Creative IR + Judge + Critique/Revision）——因此判断回路进入 Creative IR 必填字段，而非可选增强。**

### Added: 编译目标分类路由（Pass 0 Step 0.1b）
- Pass 0 在"是否值得编译"判定后新增编译目标分类：procedural/knowledge/analytical → General Track（Pass 1-6），creative（写作/文案/广告/脚本/品牌/Naming/IP/hybrid 九类细分）→ Creative Track（Pass C1-C5）。
- 判定依据按优先级：① 产出是否需要判断力；② 风格是否是产物的一部分；③ 源材料是否有专家否决记录；④ 混合时看主体（宁可 hybrid 判 creative，不可反向——creative 任务走 General Track 会得到"能写但不会判断"的模板化 skill）。
- Gotcha #13：Creative 误路由是最贵的失败。

### Added: Creative IR JSON Schema（核心交付物）
- `schemas/creative-ir-schema.json`：与 General IR (ir-schema.json) 平行的中间表示。18 个顶层字段：meta（含 confidence 编译置信度）/ intent（Resolved Intent）/ context（六维场景）/ style（Style Grammar + **12 维 Style Fingerprint**）/ principles（原则≠约束，必带 rationale+priority+source_refs）/ heuristics（信号→倾向→纠正）/ constraints（四分类）/ examples（positive/negative/contrastive/before_after）/ anti_patterns（必带 detection_signals+correction）/ creative_strategy（Problem→Tension→Insight→Territory→Angle）/ generation（强制 Idea Diversity：territory_count≥2）/ **judgment + revision（判断回路，必填）** / memory（Failure Memory）/ output / runtime_profile（六维依赖度）/ provenance。
- 溯源定义 sourceReference.origin 四级枚举（explicit/inferred/heuristic/generated）——Compiler 推断不可伪装成专家原话。

### Added: scripts/validate_creative_ir.py（Pass C3→C4 门控）
- 纯 stdlib，与 validate_ir.py 同风格。覆盖 schema 必填约束 + 判断回路业务规则：#1 weighting 键与 dimensions 一一对应且和=1.0（±0.05）；#2 diagnose_before_rewrite=false 仅允许 quick 模式；#3 source_refs.document_id 必须在 provenance 登记；#4 WARN 级（不阻塞）：confidence<0.6 材料不足、示例缺 explanation。
- 已实测（fixture 于测试后清理）：合法 IR→PASS(0)；非法 IR→FAIL 3 错误(1)，覆盖业务规则 #1/#2/#3（权重键不对应 / full 模式禁用 diagnose_before_rewrite / source_refs 未溯源）；文件错误→exit 2；quick 模式豁免与 WARN 机制均验证生效。
- 修正：schema 顶层 required 补入 `output`（输出契约）——与校验器口径对齐。输出契约是运行时 FINALIZE 状态与产物 output.md 的依赖，任何创作型 skill 必须具备；此前 schema 遗漏导致"合法 IR 过不了校验器"的假阴性。

### Added: Creative Track 三份 reference
- `references/creative-compiler.md`：双编译总纲——路由规则 + C1-C5 管线 + Creative IR 构建规则（Fingerprint 禁止凭印象填/原则≠约束/示例必带 explanation）+ Runtime Profile 基准表（八类创意类型）+ 产物结构 + Pass C5 创意四层评估（style_fidelity / anti_pattern_rate / revision_gain）。
- `references/creative-extraction.md`：Pass C1/C2 规范——Resolved Intent（表面请求 vs 真实创作意图）+ 六维 Context + 语义分块（before/after 不拆散、否决记录单独成块）+ 五提取器（Principle/Style/Example/Anti-pattern/Heuristic，含 Principle≠Constraint 判据）+ Style Fingerprint 构建算法 + origin 四级溯源。
- `references/creative-runtime.md`：判断回路规范——运行状态机（INIT→…→MEMORY_UPDATE，13 态）+ Judge 规范（Observe→Score→Compare→Explain，不重新生成）+ Pairwise 比较 + Critique 四要素（What/Why/Where/How）+ Revision 流程（diagnose→locate→plan→partial fix→re-judge，禁止无脑重写）+ Revision Gain + Style Drift 检测（correction 优先于重生成）+ Failure Memory / Preference 解析 + 判断回路最低配置清单（8 项，缺一 C5 判 CONDITIONAL）。

### Changed
- `SKILL.md` 升级 v3.0.0：双编译架构声明 + 管线图双轨道 + Step 0.1b 内联路由表 + C1-C5 Pass 表 + 编译模式表增加 Creative Track 列 + Execution Rule 3（Creative IR 门控）+ Gotchas #13-17 + 知识资源表新增三项 creative 资源 + frontmatter 触发词新增 creative 入口（'创作型 skill 编译'、'把写作风格/创意方法编译成 skill'、'creative skill compiler'）。
- `schemas/trace-schema.json`：compilation_config 新增 compilation_track（general/creative）与 target_type；pass_id 枚举新增 c1-understand/c2-extract/c3-design/c4-generate/c5-evaluate；evaluation 新增 creative_evaluation（style_fidelity/anti_pattern_rate/revision_gain/judgment_loop_complete）。
- `evals/trigger_cases.json`：版本 3.0.0，新增 P04 创作型编译 positive case（访谈+范文→创作型 skill），trigger_actions 补两个 creative 触发词。
- `README.md`：标题/徽章/简介更新为双编译口径，管线表新增 C1-C5，核心能力新增双编译/Creative IR/Style Fingerprint/origin 溯源四项，文件结构补 schemas/scripts/references 新文件。

### Changed: 共享 reference 的 Creative Track 感知改造
> 兑现 SKILL.md "Creative Track 共享机制" 声明——此前 5 个共享 reference 文件（pass-ingestion / pass-5-optimize / evidence-grading / honest-boundaries / meta-reflection）内零 creative 引用，执行 Creative 编译时加载它们只会拿到 General-only 指引。
- `references/pass-ingestion.md`：新增 Creative Track 补充规则——before/after 对相邻保全、否决记录单独成 SEG、多人对话保留说话人归属（风格归属错误 = Style Fingerprint 污染）。
- `references/pass-5-optimize.md`：新增 Creative Track 优化约束——explanation 随 example 移动、正反例不算重叠、style.fingerprint 与 judgment.weighting 不参与 O10 瘦身、判断回路最低配置清单不可删减（缺清单回退 C4 而非优化）。
- `references/evidence-grading.md`：新增 origin 四级与 evidence 三级的映射表——evidence 度量载体保真度，origin 度量知识来源方式；generated 级别 General Track 禁用；风格主张冲突保留并标注时间。
- `references/honest-boundaries.md`：新增创作专属边界声明——材料不足（confidence<0.6）/ 风格保真边界（统计拟合非复刻）/ 判断回路边界（评分辅助非真理）/ 风格演化声明；反模式新增"风格全能声明"与"隐藏生成内容"。
- `references/meta-reflection.md`：检查点放置表新增 C1/C2/C3 三行 + Creative Track 自检问题（Resolved Intent 是否"为什么"层面、Fingerprint 是否实测、weighting 均匀分配 = 没做判断）。

### 设计取舍
- 判断回路为必填而非可选：这是本次升级的核心决策——"会模仿"与"会创作"的分水岭不在于风格描述多精确，而在于 skill 能否自我判断与修订。
- Style Drift 检测响应为 style correction 而非重新生成：重生成丢失已达标维度分数，代价高于局部纠正。
- Creative Track 复用而非重建：Ingestion/证据分级/诚实边界/元反思/Token 预算/平台 profile/Pass 5 全部共享，仅判断回路相关部分新建。

### Added: 对照源文档的差距补齐（第二轮审计）
> 重新对照三份设计文档全量审计后发现 6 处未落地机制，本轮补齐：
- `references/creative-runtime.md` 新增 §8 运行时对象 Candidate（v2.0 文档 #21）：创意 + rationale + 评分 + 指纹 + 修订史同时流转，禁止裸文本传递——裸文本丢失 rationale 后 Revision Gain 无法归因。
- `schemas/creative-ir-schema.json` 新增 `knowledge` 顶层字段（可选，v2.0 文档 #5.1）：领域知识（平台规则/行业术语/法规红线），与 principles（风格判断）/ style（表达方式）三分；每条 domain_fact 必带 source_refs。validate_creative_ir.py 同步校验（含溯源登记），并前置 doc_ids 初始化修复其引用顺序。
- `references/creative-compiler.md` Pass C5 扩展（v1 文档 #37-40）：8 项指标完整枚举（Task Fit/Style Fidelity/Originality/Specificity/Consistency/Anti-pattern Rate/Human Preference/Revision Gain）+ Golden Set（期望特征与方向，非标准答案，产物必含 tests/golden-set.md ≥3 条）+ 对抗测试（"再高级一点"式模糊请求 → fingerprint 局部调整而非整体重写）+ 回归测试（编译器版本间 Golden Set 重编译对比，防能力退化）；产物结构补 tests/ 目录（golden-set.md + adversarial.md）。
- `README.md` 全量重写：判断回路独立成节（状态机 + Judge/Critique/Revision/Candidate/Style Drift/Memory 六要素）、Creative Track 示例输入输出、路由判定依据、8 指标与 Golden Set 能力项、设计原则新增"编译能力不编译文字/证据可溯源/宁可 hybrid 判 creative"三条。

## v2.3.1 — 契约一致性修复 + IR 校验脚本 (2026-08-21)

**SkillForge Audit（L3 静态校验 + L4 审计）发现的核心问题修复：v2.0→v2.3 增量更新未同步到下游契约文件，以及 Pass 3→4 IR 门控为纯 prompt 层约束（AP-13）。**

### Fixed: 跨文件契约漂移（S11 一致性）
- `SKILL.md` Pass 0 模式表：`full`/`audit` 的 Pass 6 描述从"全部三层/四层"更正为"全部五层"。
- `references/pass-6-validate.md`：执行步骤中残留的"五角色"→"六角色"（Role 6 Compaction Resilience）、"B1-B8"→"B1-B14"、"四层评估/四层去重"→"五层"；Output Schema 的 role 枚举补 Compaction Resilience、issues[].layer 枚举补 E。
- `schemas/trace-schema.json`：evaluation 描述补 Layer E；新增 `layer_e_token_economy` 字段；`skill_quality_score` 公式从旧四层权重（0.2/0.3/0.25/0.25）更正为五层权重（0.15/0.25/0.20/0.20/0.20）。
- `schemas/ir-schema.json`：补 `pass_3_design.knowledge_stratification` 定义（Pass 3 Step 3.4b 产出、Layer E E3 消费，此前 schema 未声明）。
- `references/pass-ingestion.md` Step I.1 来源识别表补 `skill_package`（v2.3.0 合并编译入口此前断链）。
- `references/anti-patterns.md`："完整 13 反模式库"→"17"（SkillForge 实际数量）。
- `templates/ir-schema.md` 全量同步 v2.0-v2.3 字段（pass_ingestion / state_signals / merge_plan / state_management / knowledge_stratification / structured_cases / stateful-domain-os / examples 六类枚举），并声明 SSOT 归属 `schemas/ir-schema.json`，防止双源再漂移。

### Added: scripts/validate_ir.py（AP-13 修复）
- Pass 3→4 Decision Gate 的 harness 层强制校验：纯 stdlib，覆盖 schema 必填字段 + IR 校验表 9 条（含 stateful-domain-os 三件套门控、skill_package→stateful-domain-os 门控）。退出码 0/1/2。
- `SKILL.md` Execution Rule 2 引用该脚本；IR 落盘时强制执行，未落盘时按 schema 必填清单人工核对。

### Added: evals/trigger_cases.json（化解 S2.7 WARN）
- 3 positive（英文编译 / 中文"把 prompt 变成 skill" / skill 合并）+ 3 near-miss negative（提示词措辞优化、评估已有 skill、从零创作 skill 架构），100% near-miss 覆盖 AP-10 风险——本 skill 与 skillforge/prompt-engineering 强近邻，description 含 'prompt'/'skill'/'提示词' 高频词，naive 匹配易误触发。

### Changed
- frontmatter description 压缩至 479 字符（原 518 超出自身 TRAE profile ≤500 上限），并新增近邻排斥声明 "or auditing existing skills"（与 SkillForge 的评估场景划界，S1.8/AP-10）。
- `references/pass-4-generate.md`：Step 4.9 修复循环加"最多 3 轮"上限（AP-06）；Step 4.0 标题层级从 Step 4.1 内嵌提升为独立步骤。
- `references/pass-2-extract.md` Step 2.4、`references/pass-3-design.md` Step 3.11 标题层级修正（###→##）；`profiles/claude.md` 英文句中文化。
- SKILL.md 末尾新增品牌信息（由擎漫网络 | Qomob.AI旗下白泽 SkillCompiler提供支持）。
- **品牌信息进入生成链路**：`templates/skill-md-template.md` Provenance 后新增品牌行（所有编译产物自动携带）；`references/pass-4-generate.md` Body 结构同步加品牌 footer，Self-Check 新增第 10 项强制校验产物含品牌行。同时模板 `Built with: Skill Compiler v1.0.0` 硬编码版本改为 `{{compiler_version}}` 变量（取 `meta.compiler_version`），消除版本漂移。
- **品牌行带版本号（与 skillforge v5.26.0 口径统一）**：品牌行升级为 `> 由擎漫网络 | Qomob.AI旗下白泽 SkillCompiler v{{compiler_version}}提供支持`，与 skillforge 交付物 footer 形态（`品牌方 | 公司旗下 产品 v版本 提供支持`）对齐，可跨 skill 家族统一识别。同步 4 处：模板品牌行、pass-4 Body footer、Self-Check 第 10 项匹配文本、skill-compiler 自身 SKILL.md 末尾（v2.3.1）。

### 已知未修复（记录为技术债务）
- `references/pass-3-design.md` 512 行，微超 500 行参考线；如后续再增长，建议将 Step 3.4b/3.4c 拆分为独立 reference。
- `references/anti-patterns.md` 与 `pass-ingestion.md` 含指向 `../../skillforge/` 的跨 skill 链接，单独分发时会断裂。

## v2.3.0 — Skill Merge 编译 + State 一等公民 + 结构化断言 (2026-08-20)

**基于毕业生 skill（jiaozi v1.1.0）回流分析的三项能力扩展：① 新编译场景——N 个已有 skill 包合并编译为统一 Context 的单一 skill；② State 进入 IR 一等公民（P1 原则 + State 配套三件 + 持久化模式）；③ 自测用例升级为程序化断言。**

### Added: Skill Merge 编译场景
- `pass_ingestion.source_type` 新增 `skill_package`；SKILL.md 条件 Pass 表新增 Skill Merge。
- `references/pass-2-extract.md` 新增 Step 2.2b：合并场景判断（共享领域对象字段 >40% 才合并，仅主题相近建议 INDEX.md 链接图替代）+ 能力去重（dedup_decisions 逐条记录，不静默合并）+ 边界冲突裁决（boundary_conflicts）+ 统一 Context 设计（unified_context_schema）+ 溯源表（模块 ← 来源 skill ← 内化能力）。
- Decision Gate 新增：无统一 Context 的合并是拼接，回退。
- Gotcha #11：skill 合并不等于文件拼接。

### Added: State 进入 IR（一等公民）
- Core Principle P1 的 Skill 组成清单新增 **State**。
- `schemas/ir-schema.json`：`single_skill_pattern` enum 新增 `stateful-domain-os`；新增 `pass_3_design.state_management`（context_schema_file / validator_script / fixtures / persistence_mode / write_discipline）。
- `references/pass-3-design.md` 新增 Step 3.4c State Management 设计：**State 配套三件**（schema 定义 + 校验脚本 + fixtures，缺一即 Fail）+ 持久化模式（file_io / paste_yaml / dual，含跨会话状态协议：粘贴优先、无 Context 报 NEW 不假装有记忆）+ 写入纪律。
- IR 校验新增 #8（stateful-domain-os 须三件套齐全）、#9（skill_package 产物必须选 stateful-domain-os）。

### Added: 结构化自测断言（structured_cases）
- `self_test_cases` 新增可选 `structured_cases`（id/input/expected_intent/assertions），生成 `tests/cases.yaml` 供自动化执行器消费。
- 断言操作符：equals / contains / in / regex / exists / count_le / contains_all + `assert_not` 反向断言（防废话模板）。
- Pass 6 Layer C 新增 C6（行为断言一致性）。

### Added: 知识分层第三维度 — override 层
- Step 3.4b 分层表新增**特化层（override）**：场景分叉值进 override 文件，只写差异不复制基准值；读取顺序 override 优先于 base。
- `knowledge_stratification` 新增 `override_layer`；Pass 6 Layer E 新增 E6（override 不复制 base）。

### Added: 模板条件段 — Onboarding 评分 + 平台兼容
- `templates/skill-md-template.md` 新增两个条件段：Onboarding 完整度评分（量化打分 + 追问轮次上限 + `[基准填充]` 标注，替代无限采访）；平台兼容（运行时能力降级路径 + `[人工评分]` 诚实标注，属 honest-boundaries 的一部分）。

### Changed: Pass 6 检查项扩展
- Layer B 新增 B13（State 三件套存在且 fixtures 跑通）、B14（merge_plan 契约一致）。
- SKILL.md frontmatter description 触发词新增 "skill 合并"、"合并 skill"。

### Added: 自动检测 + 自动注入（新 skill 自带 session-context 协议）
- `references/pass-1-analyze.md` 新增 Step 1.4b **State Requirement Signal Detection**：命中状态信号（cross_session / domain_object / profile / review_reconcile / memory / state_dependent）→ IR `state_signals` 非空。信号判据表含中英识别线索；边界不清默认不判定，记入 unknowns 澄清。
- `schemas/ir-schema.json`：`pass_1_analyze` 新增 `state_signals` 字段。
- `references/pass-3-design.md` Step 3.4c 触发条件改为**自动判定**：state_signals 非空 → 必须执行（信号命中就注入，不是可选优化）。
- `references/pass-4-generate.md` 新增 Step 4.2b **State 三件套生成模板**：core/context.md 三层骨架 + validate_context.py 校验脚本骨架 + valid/invalid fixtures + SKILL.md 跨会话状态章节（file_io / paste_yaml / dual + 粘贴优先 / NEW 不装记忆 / 降级标注）。Step 4.9 Self-Check 新增第 9 项确认三件套齐全。

### Boundary Compliance
- 无新核心 Pass（Skill Merge 是 Pass 2 内的条件 Step，信号检测是 Pass 1 内 Step），无核心 Pass 删除，架构不变。
- 改动范围：SKILL.md + 5 references（pass-1/pass-2/pass-3/pass-4/pass-6）+ ir-schema.json + skill-md-template.md + CHANGELOG.md。

---

## v2.2.0 — Layer E Token 经济性评估 + 知识分层原则 + 白泽命名 (2026-07-25)

**Pass 6 Validate 从四层评估升级为五层评估（新增 Layer E 产物 token 经济性）；Core Principle P2 从"重复内容外置"升级为"知识按变更频率分层"；Skill 中文名命名为「白泽」。零 IR schema 变更，Layer E 是 Pass 6 内部扩展。**

### Added: Layer E — 产物 Token 经济性评估 (Pass 6 第五层)
- `references/pass-6-validate.md` 从四层（A 结构 / B IR 一致性 / C 触发质量 / D 平台合规）升级为五层，新增 Layer E — Token Economy。
- Layer E 评估运行时 context 效率四个维度：路由信息密度、加载策略（按需 vs 全量）、分段粒度、触发精度（避免误加载）。
- 评分纳入 `skill_quality_score` 权重（structural×0.2 + ir_consistency×0.3 + trigger_precision×0.25 + platform_compliance×0.25 调整为含 token_economy 的五因子公式）。
- **动机：** 此前只评估生成时质量，不评估运行时 token 开销。宿主平台 compaction 后 context 占用直接影响 skill 可用性，Layer E 让编译出的 skill 在运行时 context 效率可控。

### Changed: Core Principle P2 — 知识按变更频率分层
- `SKILL.md` Core Principles P2 从"重复内容外置"升级为"知识按变更频率分层"。
- 区分**稳定层**（原理/规则，低频变更）与**时效层**（数据/案例/价格，高频变更），分离到不同 reference 文件，支持独立 compaction 与增量更新。
- `references/pass-3-design.md` 设计阶段新增 token 经济性维度考量（决定知识如何切分到 reference）。
- `references/example-generation.md` 示例生成补充 token 经济性考量。
- **动机：** 稳定层与时效层混放会导致 compaction 时整体丢失或全量重载。分层后稳定层可常驻，时效层按需加载，降低运行时 token 消耗。

### Added: 中文名「白泽」
- `SKILL.md` / `README.md` 标题加注中文别名「白泽」并补充命名寓意。
- 白泽，神话中通晓万物之理的神兽，契合本 Skill 编译万物为 Skill 的能力。
- 保留英文原名 `skill-compiler` 与 frontmatter `name` 不变。

### Engineering: 工程清理
- 新增 `.gitignore`（忽略 `.DS_Store` / `*.zip` / IDE / Node 临时文件）。
- 从仓库移除已入库的 `.DS_Store`（本地文件保留）。

### Boundary Compliance
- 无新 Pass、无 IR schema 变更（Layer E 是 Pass 6 内部扩展，A/B/C/D 评估逻辑不变）。
- 改动范围：1 SKILL.md + 3 references（pass-3-design / pass-6-validate / example-generation）+ README.md + .gitignore。

---

## v2.1.0 — Compaction Resilience + Conflict Health + Platform Compaction Awareness (2026-07-08)

**基于对 skill-authoring (Ronifue) 的第一性原理评估与对抗式审查，落地 3 项改进。Pass 6 Layer A 新增 Compaction Resilience 检查；冲突条目增加状态机与健康度检查；平台 Profile 新增 Compaction 行为字段。零架构变更。**

### Added: Compaction Resilience (Pass 6 Layer A)
- `references/pass-6-validate.md` Layer A 新增 Role 6 — Compaction Resilience。
- 检查项：路由信息前置（compaction 后 routing table 仍完整）、关键引用可达（Always Read 等声明保留）、无长依赖链。
- PASS 标准：截断后 routing 信息完整度 ≥ 80%。
- **动机：** Harness 的 compaction 机制会截断 SKILL.md body，导致 routing 信息丢失。此前无检查项覆盖此场景。

### Added: Conflict Status Machine & Health Check
- `references/evidence-grading.md` 冲突条目增加字段：`id` / `status`（open → resolved / wontfix / deprecated）/ `resolution` / `resolved_by` / `resolved_at`。
- 冲突状态机：open → resolved（prefer_higher_evidence / prefer_newer / merged / user_override）/ wontfix / deprecated。
- Pass 6 Layer B 新增 B12 冲突健康度检查：status=open 占比 < 30%；不存在"连续 3 次编译仍为 open"的冲突。
- **动机：** 此前冲突只保留不解决，长期积累会变成垃圾场。状态机提供解决路径，健康度检查防止冲突无限堆积。

### Added: Platform Compaction Behavior
- `profiles/trae.md` / `claude.md` / `generic.md` 新增 Compaction 行为表（strategy / body_limit_lines / preserves / loses）。
- TRAE: preserve_frontmatter, ~150 行。Claude: summarize, ~100 行。Generic: unknown, ~80 行（最保守）。
- **动机：** 不同 harness 的 compaction 行为不同，编译器需要知道这些差异才能生成 routing 信息前置的 skill。

### Added: Meta-Reflection Reference（元反思推演框架）
- 新增 `references/meta-reflection.md` — 8 维度推演自检框架（192 行）。
- Pass 1/2/3/6 引用元反思检查点，在分析/提取/设计/验证阶段执行推演自检。
- **动机：** 此前 Pass 间是单向流水线，缺乏跨 Pass 的反思环节。元反思让编译器在关键节点回看假设是否成立、推理是否完整。

### Changed: Evidence Grading L1-L4 对齐
- `references/evidence-grading.md` 更新 L1-L4 信源分级规则，对齐 OPC（One-Pass Compiler）规范。
- profiles/ 三平台（claude/generic/trae）同步更新 evidence grading 相关字段。

### Boundary Compliance
- 无新 Pass、无新 IR schema 变更（冲突字段是 evidence-grading 的扩展，不是 IR 结构变更）。
- 改动范围: 1 个 pass-6 文件 + 1 个 evidence-grading 文件 + 1 个 meta-reflection 文件 + 3 个 profile 文件 + 3 个 pass 文件（pass-1/2/3）+ README.md + CHANGELOG.md。

---

## v2.0.0 — 多源摄取与诚实边界

**核心变更：** 编译器输入从"纯文本 Prompt"扩展到"任意来源"（PDF/视频/网页/图片/文档），并引入证据分级与诚实边界，解决"多源内容如何编译"和"生成的 skill 不知道自己做不到什么"两个盲区。

**新增能力：**

- **Pass I Ingestion（多源摄取）** — 新增前置摄取阶段，内联解析指令（pdftotext / pdfplumber / ffmpeg+whisper / tesseract / pandoc / WebFetch），标准化为结构化内容 + 来源溯源链。纯文本 Prompt 时自动跳过。
- **证据分级体系** — 每条知识携带 `primary` / `secondary` / `inferred` 三级证据等级 + confidence。多源矛盾信息不静默消除，保留标注写入 conflicts.md。
- **诚实边界强制** — 生成的 skill 必须声明局限性 / 失败模式 / 适用前提。Pass 3 规划，Pass 6 Layer A 验证。
- **并行提取器** — 长内容或多源输入时启用五专项提取器（框架/原则/案例/反例/术语）并行扫描 + 三重验证。
- **压力测试（诱饵题）** — Pass 6 Layer C 新增 C4，构造边界交叉区诱饵输入验证 description 锐利度。
- **Skill 链接图** — 多 skill 产出时生成 INDEX.md 技能地图。

**架构变更：**

- IR Schema 新增 `pass_ingestion` 字段；`input_spec.type` 新增 `structured_content` 枚举值
- Trace Schema 的 pass_id 枚举新增 `ingestion`
- Pass 1/2/3/6 均接入 v2.0 能力

**新增文件：** `references/pass-ingestion.md`、`evidence-grading.md`、`honest-boundaries.md`、`parallel-extractors.md`

**方法论致谢：** 本版本的"多源蒸馏"、"证据分级"、"诚实边界"、"并行提取 + 三重验证"等设计思想，受到以下 MIT 协议开源项目的启发（仅吸收方法论，所有实现为原创撰写）：

- [cangjie-skill](https://github.com/kangarooking/cangjie-skill) (MIT) — 多源预处理、并行提取、压力测试
- [nuwa-skill](https://github.com/alchaincyf/nuwa-skill) (MIT) — 诚实边界、证据可追溯
- [immortal-skill](https://github.com/agenmod/immortal-skill) (MIT) — 矛盾保留、证据分级

---

## v1.2.0 — 平台适配与成本控制

**核心变更：** 引入目标平台适配层和编译成本控制，解决了"编译出的 skill 在哪些平台能跑"和"编译一次要花多少钱"两个架构级盲区。

| 变更 | 说明 |
|------|------|
| **平台适配层** | 新增 `profiles/` 目录（trae/claude/generic），Pass 0 选择平台，Pass 4 按 profile 渲染 frontmatter 与文件结构，Pass 6 Layer D 反向验证 |
| **编译模式** | 新增 `quick` / `full` / `audit` 三种模式，不同 token 开销与质量等级。默认 full |
| **Token 预算** | IR meta 新增 `token_budget` 字段，超预算时自动降级模式 |
| **Pass 6 Layer D** | 新增平台合规检查（D1-D8），验证 frontmatter 格式、description 规范、目录白名单等 |
| **评分公式调整** | 四层评估：structural×0.2 + ir_consistency×0.3 + trigger_precision×0.25 + platform_compliance×0.25 |
| **Pass 5 O9/O10** | 新增编译过程去重（O9）和 IR 瘦身（O10），降低编译环节的 token 消耗 |
| **Trace 补充** | trace-schema.json 新增 `compilation_config` 和 `cost_summary` 字段 |
| **Profile 自定义** | 高级用户可参考 profiles/ 格式编写自定义平台 profile |

**核心洞察：** Skill 编译器的输出应该是对目标平台"开箱即用"的，而不是需要用户手动适配。平台 profile 作为 oracle，从生成到验证形成闭环。

---

## v1.1.0 — 评估闭环补全

**核心变更：** Pass 6 从单一结构审查升级为三层评估，解决了"会生不会评"的问题。

| 变更 | 说明 |
|------|------|
| **Pass 6 三层评估** | Layer A 结构（五角色）+ Layer B IR 一致性（B1-B8）+ Layer C 触发质量（C1-C3） |
| **IR 新增 self_test_cases** | Pass 3 Step 3.9 从 boundary + capability_graph 派生三类测试用例（positive/negative/near_miss） |
| **评分公式** | `skill_quality_score = structural×0.3 + ir_consistency×0.4 + trigger_precision×0.3` |
| **trace schema** | 新增 evaluation 块（三层分数 + 综合评分） |
| **自编译验证** | 首轮 85.5 分检出 5 个 issue，修复后 100 分通过 |

**核心洞察：** IR 既是生成的输入，也是验证的 oracle。不需要外部裁判——Pass 1-3 已经写完了"这个 skill 该长什么样"，Pass 6 回头拿 IR 验产出即可闭环。

---

## v1.0.0 — 初始版本

6 核心 Pass + 3 条件 Pass 的编译器架构，Skill IR 中间表示，五角色架构审查。
