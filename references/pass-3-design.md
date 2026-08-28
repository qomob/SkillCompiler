# Pass 3: Design — Skill 架构设计

**加载时机：** 📍 执行到 Pass 3 时加载。

---

## 设计原则

**先设计系统，再设计 Prompt。绝不反过来。**

原 16-phase 把 Workflow / References / Templates / Rubrics / Checklists / Config 拆成六步。但它们强关联——Workflow 决定需要什么 Checklist，Checklist 决定需要什么 Rubric。合并为一次架构设计。

---

## Step 3.1 — Architecture Type 决策

| 条件 | architecture_type |
|------|------------------|
| 单次 LLM 调用，无状态 | `single-prompt` |
| 多步骤顺序执行，有中间产出 | `workflow` |
| 多角色并行或专业化 | `multi-agent` |

### 决策树

```
Prompt 有多个步骤？
  ├─ No → single-prompt
  └─ Yes → 步骤间有并行或需要不同专业角色？
            ├─ No → workflow
            └─ Yes → multi-agent
```

---

## Step 3.2 — Workflow Pattern 选择

**仅 workflow / multi-agent 执行。** single-prompt 跳过。

| 需求 | Pattern | 核心机制 |
|------|---------|---------|
| 输入类型多样，先判路再执行 | classify-and-act | 分类器路由 |
| 多个独立子任务可并行 | fan-out-synthesize | 扇出+综合 |
| 质量关键，需独立验证 | adversarial-verify | 对抗验证 |
| 需要创意多样性，筛选最优 | generate-filter | 生成+过滤 |
| 多方案成对比较选优 | tournament | 锦标赛 |
| 需要迭代优化直到达标 | loop-until-done | 循环（上限3轮） |
| 强制顺序，不能跳步 | pipeline | 管道+检查点 |

可组合：如 classify-and-act 路由 → 每条路径内部用 pipeline。

---

## Step 3.3 — Single-Skill Pattern 选择

**所有 Skill 必须选一个。** 与 workflow pattern 正交。

| 需要什么？ | Pattern | 核心机制 |
|------------|---------|---------|
| 特定技术栈的专家知识 | tool-wrapper | SKILL.md 指向 references/ |
| 一致的结构化输出 | generator | 模板 + 风格指南 |
| 自动化代码/内容审查 | reviewer | 分离"检查什么"与"怎么查" |
| 需求不明确，需先收集 | inversion | Agent 先采访用户 |
| 复杂的多步骤任务 | pipeline | 强制顺序 + 检查点门控 |
| 跨会话运营领域对象 / skill 包合并产物 | stateful-domain-os | 统一 Context + Router + 按需模块加载 |
| 不确定？ | tool-wrapper | 最通用，可演进 |

---

## Step 3.4 — Module Decomposition

基于 Pass 2 的 knowledge_inventory，决定模块拆分：

| IR 字段 | 去向 | 拆分条件 |
|---------|------|---------|
| rules（> 5 条） | `references/rules.md` | 规则数 > 5 或总字数 > 200 |
| rules（<= 5 条） | 内联 SKILL.md | 规则少且短 |
| templates | `templates/*.md` | 有结构化输出 |
| domain_knowledge | `references/domain-*.md` | 有领域知识 |
| standards | `rubrics/*.md` | 有评分/质量标准 |
| examples | `examples/*.md` | 有示例（或触发 Example Generation pass） |
| honest-boundaries（v2.0） | `references/honest-boundaries.md` | **强制**：有 out_of_scope 或失败模式时必生成 |
| conflicts（v2.0） | `references/conflicts.md` | Pass 2 检测到未裁决冲突时生成 |

### 拆分原则

1. **SKILL.md 最小化** — 只含路由 + 流程概览，< 300 行
2. **知识外置** — 任何 > 200 字的知识块 → references/
3. **配置参数化** — 可变的参数 → config/
4. **模板独立** — 固定格式的输出 → templates/
5. **诚实边界强制（v2.0）** — 每个 skill 必须规划 honest-boundaries 模块，即使初版为骨架。📍 详见 [honest-boundaries.md](honest-boundaries.md)

---

## Step 3.4b — Knowledge Stratification by Change Frequency（v2.2 变更频率分层）

**仅当 skill 含领域知识密集型内容（knowledge_inventory 中 domain_knowledge 条目 ≥ 5，或单条 > 200 字）时执行。** 单 prompt / 无领域知识 skill 跳过。

> **第一性原理：** 知识不是铁板一块。经营框架/核心公式/指标定义可能一两年才调整（稳定层）；策略打法/竞争格局/关键事件/口径规则每季度甚至每月在变（时效层）。把它们塞进同一文件导致两个问题：① 更新时效内容时误改稳定内容；② 文件膨胀让维护者无法定位该改什么。混存储的维护成本随内容量指数级增长。

### 分层判定

对 Pass 2 的 `knowledge_inventory` 中每条 domain_knowledge，按变更频率归类：

| 层 | 判定特征 | 存储去向 |
|----|---------|---------|
| **稳定层（stable）** | 经营框架、核心公式、指标定义、业务模式、不变量。一两年才调整 | `references/domain-{topic}-stable.md`（瘦文件，百行级，打开即全景概要） |
| **时效层（timely）** | 策略打法、竞争格局、运营抓手、关键事件、口径规则。每季度/每月变更 | `references/domain-{topic}-timely.md`（按主题组织，跨实体分段管理） |
| **特化层（override，v2.3.0）** | 同一知识在不同细分场景的取值差异（行业基准因业态而异、平台规则因站点而异） | `references/formats/{variant}.md` 等 override 文件——**只写差异，不复制基准值** |

**override 层规则（通用 base + 特化 override）：**

- base 文件是知识 SSOT，逐值可标置信度；override 文件只声明与 base 的差异项，读取顺序 = override 优先于 base
- 判定信号：知识含"按 X 而定 / X 类场景不同"的分叉结构时，分叉值进 override，主干进 base
- 反模式：把基准值复制进每个 override 文件——base 一改，N 个 override 全部漂移

### 分层原则

1. **写入与读取粒度解耦** — 维护者视角是"一个文件改完所有实体"（写入效率）；LLM 视角是"只看一个实体的段落"（读取/token 效率）。同一物理文件通过分段加载策略同时满足两边
2. **稳定层优先收拢** — 一个实体的稳定知识收拢到一个文件，不分散到多个子目录。LLM 需要连贯上下文做推理，不是碎片化数据包拼装
3. **时效层按主题聚合** — 所有实体的同类时效知识（如"策略"）放一个主题文件，内部按实体分段。更新某类时效知识只开一个文件
4. **分段加载** — 主题文件可能数千行覆盖所有实体，但单次请求只加载目标实体的那一段。token 消耗控制在几百以内

### IR 产出

```json
{
  "knowledge_stratification": {
    "applicable": true,
    "stable_layer": ["references/domain-xxx-stable.md"],
    "timely_layer": ["references/domain-xxx-timely.md"],
    "override_layer": ["references/formats/{variant}.md"],
    "segment_loading": "主题文件按实体段落加载，单次只加载目标段落"
  }
}
```

**不适用时：** `applicable: false`，跳过本步。

---

## Step 3.4c — State Management 设计（v2.3.0，条件执行）

**自动触发条件（按优先级）：**

1. `pass_1_analyze.state_signals` 非空（Pass 1 Step 1.4b 自动检测命中）→ **必须**执行，产物自动带 session-context 协议
2. `single_skill_pattern=stateful-domain-os`（含 skill_package 合并产物）→ 必须执行
3. 编译器独立判断 skill 需跨会话记忆领域对象（信号检测之外的新发现）→ 执行，并回填 `state_signals`

三者皆不满足 → 写 `state_management.applicable=false` 跳过。**判定是自动的，不是可选优化——信号命中就注入。**

> State 是一等设计对象，不是 SKILL.md 里的一句话。有状态 skill 的标配是**三件套**，缺一即 Fail（Pass 6 B13）。

### State 配套三件

| # | 产物 | 职责 |
|---|------|------|
| 1 | **Context schema 定义**（如 `core/context.md`） | 三层结构：L1 Static（静态事实）/ L2 Working（当前任务）/ L3 Learning（验证过的教训）。字段逐一定义类型与更新频率 |
| 2 | **校验脚本**（如 `scripts/validate_context.py`） | 校验 context 文件是否符合 schema。无校验的 schema 只是注释 |
| 3 | **fixtures**（`tests/fixtures/`） | valid + invalid 至少各一，供校验脚本回归 |

### 持久化模式（跨会话状态协议）

| 模式 | 适用平台 | 行为 |
|------|---------|------|
| `file_io` | Trae / Codex 等有文件 I/O | 自动读写 `project/{id}/context.yaml`，用户无感续接 |
| `paste_yaml` | OpenClaw / Hermes 等无文件 I/O | 对话结束输出 Context YAML，用户下次粘贴回来 |
| `dual` | 需跨平台部署 | 两者兼备，SKILL.md 声明降级路径（如"无文件 I/O 时评分脚本不可用，按基准人工折算并标注"） |

**通用规则：** 用户手动粘贴的 Context 始终优先；无 Context 时明确告知状态为 `NEW`，不得假装有记忆。

### 写入纪律（防 Context 膨胀）

只持久化三类：**Stable Fact**（稳定事实）/ **Explicit Decision**（明确决策）/ **Validated Learning**（验证过的教训）。闲聊评价不写。

### IR 产出

```json
{
  "state_management": {
    "applicable": true,
    "context_schema_file": "core/context.md",
    "validator_script": "scripts/validate_context.py",
    "fixtures": ["tests/fixtures/valid_context.yaml", "tests/fixtures/invalid_context.yaml"],
    "persistence_mode": "dual",
    "write_discipline": "Stable Fact / Explicit Decision / Validated Learning"
  }
}
```

---

## Step 3.5 — Workflow Reconstruction

**不要沿用 Prompt 顺序。** 以 Skill 为中心重新设计。

### 每步定义

| 字段 | 说明 |
|------|------|
| purpose | 这一步为什么存在 |
| input | 输入是什么（来自上游或用户） |
| output | 输出是什么（传给下游） |
| decision_gate | 什么条件下继续/停止/重试 |
| exit_criteria | 这一步完成的标志 |
| retry_strategy | 失败时怎么办（最多 3 次） |
| rollback_strategy | 无法完成时怎么办 |

### Workflow 设计原则

- **阶段化** — 每步有明确的进入/退出条件
- **可恢复** — 任何一步失败不丢失上游产出
- **可重试** — 失败后带反馈重试，有上限
- **可扩展** — 新步骤可以插入，不破坏现有流程

### 后置触发 vs 前置全选择（v2.2）

**问题：** 当 workflow 涉及多个方法/路径可选时，前置全选择会让 LLM 在分析前做"全局选择题"——选项越多，用于真正分析的推理资源越少，且方法间边界模糊导致路由错误频发。

**后置触发模式：** 决策点从"分析前选方法"变成"分析中遇到问题再加载"。在分析框架的知识文件里预埋触发标记，模型分析到某个维度、发现特定模式时（如"供给数量上升但单位产出下降"是典型的结构迁移信号），触发标记指示它按需加载对应的方法文件。

**适用条件：** workflow 有 ≥ 5 个可选方法/路径，且方法间关键词有重叠时采用。方法少（< 5）或边界清晰时用标准路由即可。

**token 经济性：** 前置全选择 = N 个方法文件全量预加载；后置触发 = 按信号按需加载 1-2 个。token 占用差距是数量级的。

**设计产出：** 在 workflow_steps 中，被后置触发的方法文件不放在启动加载列表，而是标注 `trigger_signal`（触发该文件的具体信号模式）。

---

## Step 3.6 — Reference Tree 设计

规划 references/ 目录结构：

```
references/
  ├── rules.md          # 规则集合
  ├── domain-xxx.md     # 领域知识
  ├── best-practices.md # 最佳实践
  └── gotchas.md        # 常见陷阱（首次留骨架）
```

### 设计原则

- 按主题分文件，不按 Prompt 顺序
- 每个文件独立可读
- 引用深度 = 1 层（SKILL.md → references/file.md，不嵌套）

---

## Step 3.7 — Checklist / Rubric / Config 设计

### Checklist（检查清单）

根据 architecture_type 生成：

| 清单 | 内容 |
|------|------|
| Architecture Checklist | 模块边界、依赖方向、扩展点 |
| Quality Checklist | 无 TODO、无 placeholder、< 300 行 |
| Skill Checklist | frontmatter 合规、触发词、懒加载标记 |

### Rubric（评分体系）

当 Pass 2 有 standards 时生成。包含：

| 组件 | 用途 |
|------|------|
| Scoring Rubric | 评分维度 + 权重 |
| Risk Matrix | 风险等级矩阵 |
| Priority Matrix | 优先级排序 |
| Maturity Model | 成熟度分级 |

### Config（配置）

找出应该参数化的内容：

```yaml
# config/settings.yaml
skill_name: string
version: string
max_iterations: 3  # 循环上限
output_format: markdown | json
```

---

## Step 3.8 — Folder Structure 规划

基于以上设计，输出目标目录树：

```
skill-name/
  SKILL.md              # 入口 + 路由
  references/           # 外置知识（按需加载）
  workflows/            # 工作流定义（workflow/multi-agent）
  templates/            # 输出模板
  checklists/           # 检查清单
  rubrics/              # 评分体系
  config/               # 参数化配置
  examples/             # 示例
  schemas/              # JSON schema
```

**最小化原则：** 只创建需要的目录。single-prompt skill 不需要 workflows/。

---

## Step 3.9 — Self-Test Cases 派生

**Pass 3 收尾必做。** 从 Pass 1 的 boundary 和 Pass 2 的 capability_graph 派生静态自测用例，供 Pass 6 Layer B/C 消费。

**这是 IR 作为 test oracle 的关键步骤——不派生用例，Pass 6 就无 oracle 可用。**

### 派生规则

| 用例集 | 来源 | 说明 |
|--------|------|------|
| `positive` | `pass_1.boundary.in_scope` × `pass_2.capability_graph.primary` | 应触发 skill 的用户输入（组合场景 × 主能力） |
| `negative` | `pass_1.boundary.out_of_scope` | 不应触发的用户输入（显式排除项） |
| `near_miss` | `pass_2.capability_graph.secondary` − `pass_2.capability_graph.primary` | 语义近邻、容易误触发但不在主职责内的输入 |

### 派生要求

1. **positive 至少 3 条** — 覆盖主能力的典型用户表述
2. **negative 至少 1 条** — 来自 boundary.out_of_scope（若为空，标注 `inferred: "无显式排除项"`）
3. **near_miss 至少 0 条** — 若 secondary 为空则空数组（无近邻误触发风险）
4. **用用户视角表述** — 写用户会怎么问，不写内部能力名（如"帮我审一下这段 Python 代码"而非"调用 code-reviewer skill"）

### 示例

```json
{
  "self_test_cases": {
    "positive": [
      "审查这段 Python 代码的安全问题",
      "检查这个函数有没有 bug",
      "帮我 review 一下这个 PR"
    ],
    "negative": [
      "帮我写一段 Python 代码",
      "翻译这段技术文档"
    ],
    "near_miss": [
      "审查这段 JavaScript 代码"
    ]
  }
}
```

### 派生完成后

`self_test_cases` 写入 IR 的 `pass_3_design.self_test_cases`。Pass 6 Layer B/C 直接读取此字段，无需重新生成用例。

### 结构化升级：程序化断言（v2.3.0，可选）

**workflow/multi-agent 及有路由层的 skill 建议额外产出 `structured_cases`**，生成 `tests/cases.yaml`，把自测用例从描述性字符串升级为自动化执行器可消费的断言：

| 操作符 | 语义 |
|--------|------|
| `equals` | 输出字段等于 value |
| `contains` | 输出字段（字符串/数组）包含 value |
| `in` | 输出字段 ∈ value 数组 |
| `regex` | 输出字段匹配正则 |
| `exists` | 字段存在（含非空） |
| `count_le` | 数组长度 ≤ value |
| `contains_all` | 数组包含 value 数组全部元素 |
| `assert_not` | 反向断言：输出中**不得**出现的短语（防废话模板，如"加强管理"式空话） |

```yaml
# tests/cases.yaml 单条示例
- id: R-01
  input: "最近客流下降怎么办"
  expected_intent: growth_diagnosis
  expected_modules: [growth-engine]
  assertions:
    - { field: intent, equals: growth_diagnosis }
    - { field: module, contains: growth-engine }
  assert_not: ["加强管理", "提升服务"]   # 不得出现的空话短语
```

断言覆盖建议：路由类（intent/module）+ 输出契约类（YAML 协议字段存在性）+ 边界拒绝类（超范围输入被拒）。Pass 6 Layer C C6 验证产物中的 cases.yaml 与 IR 断言语义一致。

---

## Step 3.10 — Skill Interlinking（v2.0 可选）

**仅当一次编译产出多个相关 skill 时执行**（如从一份长文档蒸馏出多个方法论 skill）。单 skill 编译跳过此步。

当输出包含多个 skill 模块时，规划它们之间的关系图谱，生成 `INDEX.md` 作为技能地图：

### 关系类型

| 关系 | 含义 | 示例 |
|------|------|------|
| `depends_on` | A 的执行依赖 B 先完成 | "代码审查" depends_on "静态分析" |
| `complements` | A 与 B 互补，组合使用效果更好 | "PEP8 检查" complements "安全审计" |
| `contradicts` | A 与 B 在某些场景给出冲突建议 | 记录冲突，指向 conflicts.md |
| `alternative` | A 与 B 是同一问题的不同方案 | 标注各自适用场景 |

### INDEX.md 模板

```markdown
# Skill Index — 技能地图

## 包含的 Skills
| Skill | 职责 | 触发场景 |
|-------|------|---------|
| {name} | {一句话} | {when} |

## 关系图
- {SkillA} → depends_on → {SkillB}
- {SkillC} → complements → {SkillD}

## 推荐组合
{哪些 skill 适合串联使用}
```

### 设计原则

- INDEX.md 是**可选输出**，只在多 skill 产出时生成
- 关系图帮助用户理解 skill 间的协作方式，而非孤立使用
- `contradicts` 关系必须指向 `references/conflicts.md` 的具体条目

## Step 3.11 — Meta-Reflection Checkpoint（v2.1）

在设计产出 IR 之前，用以下 3 个维度二次审视设计决策。Quick 模式跳过此步。

📍 完整框架见 [meta-reflection.md](meta-reflection.md)

| 维度 | 自检问题 | 触发条件 |
|------|---------|---------|
| D3 推理 | architecture_type 的决策链是否有跳跃？模块拆分标准是否前后一致？ | 总是 |
| D5 替代解释 | 是否考虑过至少 1 个替代架构并给出诚实的淘汰理由？替代方案的优势是否被如实评估？ | architecture_type 非 single-prompt |
| D6 边界条件 | out_of_scope 条目是否足够具体？当前设计在输入为空/极长/格式退化时是否仍适用？ | 总是 |

**输出：** 自省结果写入 trace。如果发现设计漏洞，在进入 Pass 4 前修正 IR。

---

## Output Schema

```json
{
  "architecture_type": "single-prompt | workflow | multi-agent",
  "workflow_pattern": "pattern name | null",
  "single_skill_pattern": "tool-wrapper | generator | reviewer | inversion | pipeline | stateful-domain-os",
  "state_management": {
    "applicable": false,
    "_note": "v2.3.0: stateful-domain-os 或需跨会话记忆时 applicable=true，须含三件套 + 持久化模式 + 写入纪律"
  },
  "self_test_cases": {
    "positive": ["应触发的用户输入"],
    "negative": ["不应触发的用户输入"],
    "near_miss": ["易误触发的近邻输入"],
    "structured_cases": [{ "id": "R-01", "input": "...", "expected_intent": "...", "assertions": [{ "field": "intent", "op": "equals", "value": "..." }] }]
  },
  "module_decomposition": {
    "core_prompt": "SKILL.md 核心职责描述",
    "workflows": ["workflow 文件列表"],
    "references": ["reference 文件列表 + 内容概述"],
    "checklists": ["checklist 列表"],
    "rubrics": ["rubric 列表"],
    "templates": ["template 列表"],
    "configs": ["config 参数列表"]
  },
  "workflow_steps": [
    {
      "id": "step-1",
      "purpose": "为什么存在",
      "input": "输入",
      "output": "输出",
      "decision_gate": "继续条件",
      "exit_criteria": "完成标志",
      "retry_strategy": "重试策略",
      "rollback_strategy": "回滚策略"
    }
  ],
  "reference_tree": ["references/xxx.md"],
  "folder_structure": "目录树字符串"
}
```

## IR 合并

Pass 3 完成后，将 pass_1_analyze、pass_2_extract、pass_3_design 三个字段合并为完整 Skill IR。合并后必须通过 schema 校验才能进入 Pass 4。

## Decision Gate

| 条件 | 动作 |
|------|------|
| architecture_type 确定 + folder_structure 非空 + IR 通过 schema 校验 | → Pass 4 |
| IR 校验失败（字段缺失/类型错误） | 修复 IR 缺失字段后重新校验 |
| 无法确定 architecture_type | 向用户澄清使用场景 |

### IR 校验

📍 IR schema 定义见 [schemas/ir-schema.json](../schemas/ir-schema.json)

Pass 3→4 门控时，对合并后的 IR 执行以下校验：

| # | 校验项 | FAIL 处理 |
|---|--------|----------|
| 1 | `meta`、`pass_1_analyze`、`pass_2_extract`、`pass_3_design` 四个顶层字段齐全 | 补齐缺失 Pass 的 IR |
| 2 | `pass_2_extract.capability_graph.primary` 非空（≥1 个） | 回退 Pass 2 补充能力图谱 |
| 3 | `pass_3_design.architecture_type` 为 single-prompt / workflow / multi-agent 之一 | 回退 Pass 3 确定架构类型 |
| 4 | `pass_3_design.single_skill_pattern` 已选择 | 回退 Pass 3 选择 single-skill pattern |
| 5 | `pass_3_design.folder_structure` 非空 | 回退 Pass 3 规划目录结构 |
| 6 | `pass_3_design.self_test_cases.positive` ≥ 3 条 | 回退 Pass 3 Step 3.9 补充 positive 用例 |
| 7 | `pass_3_design.self_test_cases.negative` ≥ 1 条（或标注 inferred） | 回退 Pass 3 Step 3.9 补充 negative 用例 |
| 8 | `single_skill_pattern=stateful-domain-os` 时 `state_management.applicable=true` 且三件套字段齐全（schema/validator/fixtures） | 回退 Step 3.4c 补 State 设计 |
| 9 | skill_package 输入时 `single_skill_pattern=stateful-domain-os`（合并产物必须走统一 Context 形态） | 回退 Step 3.3 重新选型 |

全部 PASS → 进入 Pass 4。
