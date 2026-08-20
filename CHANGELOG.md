# Changelog

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
