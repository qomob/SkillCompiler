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

### 拆分原则

1. **SKILL.md 最小化** — 只含路由 + 流程概览，< 300 行
2. **知识外置** — 任何 > 200 字的知识块 → references/
3. **配置参数化** — 可变的参数 → config/
4. **模板独立** — 固定格式的输出 → templates/

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

## Output Schema

```json
{
  "architecture_type": "single-prompt | workflow | multi-agent",
  "workflow_pattern": "pattern name | null",
  "single_skill_pattern": "tool-wrapper | generator | reviewer | inversion | pipeline",
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

## Decision Gate

| 条件 | 动作 |
|------|------|
| architecture_type 确定 + folder_structure 非空 | → Pass 4 |
| 无法确定 architecture_type | 向用户澄清使用场景 |
