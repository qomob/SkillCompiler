# Pass 5: Optimize — 编译优化

**加载时机：** 📍 执行到 Pass 5 时加载（条件触发）。
**反模式引用：** AP-02/04/06/07/12 定义见 [anti-patterns.md](anti-patterns.md)

---

## 触发条件

满足任一即执行：
- Source Prompt > 500 字
- Pass 4 生成的文件中有重复知识（>= 3 处相同内容）
- architecture_type = multi-agent
- 用户显式要求

---

## 优化检查清单

### O1 — Prompt 长度优化

| 检查 | 动作 |
|------|------|
| SKILL.md > 300 行 | 拆分：执行逻辑 → agents/，领域知识 → references/，规则 → checklists/ |
| 单个 agent prompt > 1500 tokens | 精简：移除示例到 examples/，移除规则到 references/ |
| 单个 reference > 2000 tokens | 拆分为多个小文件 |

### O2 — Workflow 去重

| 检查 | 动作 |
|------|------|
| 两个步骤做相似的事 | 合并为一个步骤 + 参数化差异 |
| 步骤间传递冗余数据 | 精简 inter-agent 数据契约 |
| 有步骤从不被触发 | 移除死步骤 |

### O3 — Reference 去重

| 检查 | 动作 |
|------|------|
| 同一规则出现在多个文件 | 合并为单一来源（DRY） |
| 两个 reference 文件内容重叠 > 40% | 合并 |
| reference 间有循环引用 | 打破循环，提取公共部分 |

### O4 — 知识耦合检测

| 检查 | 动作 |
|------|------|
| 一个 reference 文件同时被"产出者"和"验证者"读取 | 按信任域拆分 → 见 [anti-patterns.md](anti-patterns.md) **AP-12** |
| 领域知识与执行逻辑混在同一文件 | 分离：知识 → references/，逻辑 → SKILL.md |
| 配置硬编码在 prompt 中 | 参数化 → config/ |

### O5 — 模块化检查

| 检查 | 动作 |
|------|------|
| 单个文件承担 3+ 不相关职责 | 按职责拆分 |
| 修改一个功能需要改 3+ 文件 | 重新划界，高内聚低耦合 |
| God Agent（>= 5 不相关功能） | 拆分为多个 agent → 见 [anti-patterns.md](anti-patterns.md) **AP-07** |

### O6 — 拆分检查

| 检查 | 动作 |
|------|------|
| agent 同时负责产出和验证 | 拆分为 Producer + Verifier → 见 [anti-patterns.md](anti-patterns.md) **AP-04** |
| workflow 无上限循环 | 添加 max_iterations → 见 [anti-patterns.md](anti-patterns.md) **AP-06** |
| 所有文件都在根目录 | 按类型分目录 |

### O7 — 参数化检查

| 检查 | 动作 |
|------|------|
| prompt 中有硬编码的阈值 | → config/ 参数化 |
| prompt 中有硬编码的角色名 | → config/roles.yaml |
| prompt 中有硬编码的输出格式 | → templates/ |

### O8 — 插件化检查

| 检查 | 动作 |
|------|------|
| Skill 涉及搜索/API/数据库 | → references/plugins.md 记录 |
| Skill 涉及外部服务（GitHub/Notion） | → references/plugins.md 记录 |
| Skill 涉及 MCP 工具 | → references/plugins.md 记录 |

---

## 优化执行规则

1. **每次只改一处** — 不批量修改，每次优化后验证不破坏结构
2. **更新 IR** — 每次优化后同步更新 Skill IR，保持一致性
3. **记录变更** — 优化记录写入 Compilation Report 的 `optimization_log`
4. **不过度优化** — 如果某项检查 PASS，不要为了优化而优化

## Output

```json
{
  "optimizations_applied": [
    {
      "check": "O1",
      "issue": "SKILL.md 有 350 行",
      "action": "将领域知识移入 references/domain.md，SKILL.md 降至 180 行",
      "impact": "SKILL.md 行数 -170"
    }
  ],
  "optimizations_skipped": [
    {
      "check": "O8",
      "reason": "Skill 不涉及外部能力"
    }
  ]
}
```
