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

### O9 — 编译过程去重（v1.2 新增）

> 优化的是**编译过程本身**的 token 消耗，而非产物。

| 检查 | 动作 |
|------|------|
| 多个 Pass 加载了相同的 reference 文件 | 将公共内容提取为单次加载，Pass 间共享 |
| 某个 Pass 的 reference 文件 > 2000 tokens 且仅使用其中 < 50% 的内容 | 精简 reference 文件为当前 Pass 需要的部分 |
| Pass 4 读取的 IR 字段中有 Pass 6 用不到的字段 | 在 Pass 4→6 间传递精简版 IR（仅含必检字段） |

### O10 — IR 瘦身（v1.2 新增）

> IR 是编译器核心数据，但 full compilation 中 IR 会积累大量字段。部分字段仅被单个 Pass 使用一次，不值得保留在完整 IR 中。

| 检查 | 动作 |
|------|------|
| IR 中单次使用（仅被一个 Pass 读取）的字段 | 移除出核心 IR，转为该 Pass 本地变量 |
| `conditional_passes` 中未执行的 block | 从 trace 中移除（仅记录 skip reason），不写入 IR |
| IR 中的示例/知识内容长度 > 500 tokens 且仅用于 Pass 4 的模板填充 | 压缩为摘要引用（"参见 source prompt 原始内容"）

---

## Creative Track 优化约束（v3.0）

Creative Track 产物（Pass C4 产出）执行 O1-O10 时，以下内容是**判断回路的组成部分或示范学习材料**，禁止按通用规则优化：

| 通用规则 | Creative 例外 | 理由 |
|---------|--------------|------|
| O1：示例移入 examples/ 精简主文件 | ✅ 允许移动，但 **explanation 必须随 example 一起走** | 无解释的示例只是语料，不是示范学习材料 |
| O3：内容重叠 > 40% 合并 | positive 与 negative 示例、principles 与 anti_patterns **不算重叠** | 正反例与原则/反模式是刻意对偶结构，合并即破坏 |
| O10：单次使用字段移出 IR | `style.fingerprint`、`style.fingerprint_provenance`、`judgment.weighting`、`policy`（v3.1）、`learning.capability_deltas`（v3.1）保留在 Creative IR 中 | fingerprint/provenance 是 C5 与运行时 Style Drift 的对照基准；policy 是 JUDGE 决策层；capability_deltas 是 vNext 回溯依据——均不可瘦身 |
| O1/O6：runtime.md 精简拆分 | 判断回路最低配置清单（[creative-runtime.md](creative-runtime.md) §7）任一项不可删减合并 | 删减判断回路 = 退化为模板生成器，这是 Creative Track 最贵的失败 |
| O10：documentation 字段瘦身 | 先查 IR `runtime_roles`（或 [creative-compiler.md](creative-compiler.md) §映射表缺省值）：纯 documentation 字段可瘦身，参与 generation/judgment/revision/routing/evaluation 的字段保留 | 字段齐全主义的解药——瘦身依据是运行时消费关系，不是字段大小 |

**新增触发条件（Creative Track 专属）：** 产物 runtime.md 缺判断回路最低配置清单 → 不属于优化范畴，直接回退 C4 重新生成。

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
