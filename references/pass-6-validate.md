# Pass 6: Validate — 架构审查

**加载时机：** 📍 执行到 Pass 6 时加载。

---

## 五角色审查

统一审查，而非拆成多个独立 review。

---

## Role 1 — Skill Architect（模块边界）

| 检查项 | 问题信号 | 严重度 |
|--------|---------|--------|
| 模块边界清晰 | 一个模块的修改不影响其他模块 | 🟠 High |
| 耦合度 | 模块间是否有不必要的依赖 | 🟠 High |
| 扩展风险 | 新增功能是否需要改动核心架构 | 🟡 Medium |
| 单一职责 | 每个模块只做一件事 | 🟠 High |

## Role 2 — Knowledge Engineer（知识管理）

| 检查项 | 问题信号 | 严重度 |
|--------|---------|--------|
| 知识污染 | 不同来源的知识混在同一文件 | 🟠 High |
| 知识重复 | 同一规则出现在多处 | 🟡 Medium |
| 可维护性 | 知识更新是否只改一处 | 🟠 High |
| 信任域 | 产出者和验证者是否读同一文件 | 🟠 High |

## Role 3 — Workflow Designer（流程设计）

| 检查项 | 问题信号 | 严重度 |
|--------|---------|--------|
| 流程合理 | 步骤顺序是否最优 | 🟡 Medium |
| 可恢复 | 步骤失败后是否能恢复 | 🟠 High |
| 死步骤 | 是否有从不执行的步骤 | 🟡 Medium |
| 循环上限 | 迭代步骤是否有 max_iterations | 🟠 High |

## Role 4 — Prompt Engineer（Prompt 质量）

| 检查项 | 问题信号 | 严重度 |
|--------|---------|--------|
| Prompt 膨胀 | SKILL.md > 300 行 | 🟠 High |
| 触发词 | description 是否含 3+ 触发词 | 🔴 Critical |
| 懒加载 | 是否有 📍 标记 | 🟡 Medium |
| frontmatter 卫生 | 是否只有 name + description | 🟠 High |

## Role 5 — Software Architect（架构债务）

| 检查项 | 问题信号 | 严重度 |
|--------|---------|--------|
| 技术债务 | 是否有明显的短期 hack | 🟡 Medium |
| 版本演进 | 是否支持未来扩展 | 🟡 Medium |
| 过度设计 | 是否有不必要的抽象 | 🟡 Medium |
| 文件组织 | 目录结构是否合理 | 🟡 Medium |

---

## 审查流程

### Step 6.1 — 逐角色扫描

每个角色独立审查，输出 issues 列表。

### Step 6.2 — 去重合并

不同角色可能发现相同问题（如 Skill Architect 和 Prompt Engineer 都发现 SKILL.md 过长）。合并为单条 issue，标注发现角色。

### Step 6.3 — 严重度评定

| 严重度 | 标准 | 处理 |
|--------|------|------|
| 🔴 Critical | Skill 无法工作或无法触发 | 必须修复 |
| 🟠 High | 显著影响质量或可维护性 | 应该修复 |
| 🟡 Medium | 有改进空间 | 建议修复 |
| 🟢 Low | 微小问题 | 记录即可 |

### Step 6.4 — Verdict 判定

| 条件 | Verdict |
|------|---------|
| 0 个 Critical issue | `pass` |
| 有 Critical 但有明确修复方案 | `conditional-pass` |
| 有 Critical 且无法在本轮修复 | `fail` |

---

## Optimization Opportunities

审查中发现的非问题但可改进的点：

| 类型 | 示例 |
|------|------|
| 未来扩展 | "当前是 single-prompt，未来可演进为 workflow" |
| 性能 | "reference 文件可进一步拆分以减少加载" |
| 用户体验 | "可添加更多触发词变体" |

---

## Output Schema

```json
{
  "review_summary": "整体评价（2-3 句）",
  "issues": [
    {
      "id": "ISS-001",
      "severity": "critical | high | medium | low",
      "role": "Skill Architect | Knowledge Engineer | Workflow Designer | Prompt Engineer | Software Architect",
      "title": "问题标题",
      "detail": "具体描述",
      "fix": "修复方案",
      "fix_difficulty": "easy | medium | hard"
    }
  ],
  "optimization_opportunities": [
    {
      "type": "future-expansion | performance | ux",
      "description": "建议描述",
      "priority": "low | medium | high"
    }
  ],
  "verdict": "pass | conditional-pass | fail",
  "verdict_reason": "判定理由"
}
```
