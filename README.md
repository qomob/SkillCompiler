<div align="center">

# Skill Compiler

**Prompt → Skill IR → Optimized Skill Package**

把任意 Prompt 编译成可复用、可维护、可持续演化的 AI Skill

[![Author](https://img.shields.io/badge/Author-qomob.ai-blue)](https://qomob.ai)
[![Version](https://img.shields.io/badge/Version-v1.1.0-green.svg)](https://github.com/qomob/SkillCompiler)
[![Language](https://img.shields.io/badge/Language-%E4%B8%AD%E6%96%87-red.svg)](https://github.com/qomob/SkillCompiler)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Built with](https://img.shields.io/badge/Built_with-SkillForge-violet.svg)](https://github.com/qomob/skillforge)

</div>

---

## 这是什么

Skill Compiler 是一个 **Meta Skill（元技能）**——它的输入是任意 Prompt，输出是一个完整的、结构化的 AI Skill 文件包。

它不是"Prompt 优化器"。它是一个 **Prompt 编译器**：保留 Prompt 背后的"能力（Capability）"，而非 Prompt 本身的文字。

```
Source Prompt
      │
      ▼
  Analyze → Extract → Design → Generate → Optimize → Validate
      │
      ▼
  Complete Skill Package
```

---

## 核心特性

- **编译器架构** — 6 个核心 Pass + 3 个条件 Pass，编译器自主判断需要执行哪些
- **Skill IR 中间表示** — Pass 1-3 产出 IR，Pass 4 基于 IR 生成文件，Pass 间通过 IR 通信
- **条件执行** — 简单 Prompt 跳过 Optimize，不涉及外部能力时跳过 Plugin Discovery
- **三层评估闭环（v1.1 新增）** — Pass 6 从单一结构审查升级为三层评估：
  - **Layer A 结构完整性** — 五角色架构审查（Skill Architect / Knowledge Engineer / Workflow Designer / Prompt Engineer / Software Architect）
  - **Layer B IR 一致性** — IR 作为 test oracle，逐字段验证生成文件是否忠实于 IR 契约（B1-B8 共 8 项）
  - **Layer C 触发质量** — Pass 3 从 boundary + capability_graph 派生 self_test_cases，静态匹配 description 计算触发精度，零运行时依赖
- **三层渐进加载** — 生成的 Skill 遵循 L1 触发 / L2 路由 / L3 懒加载分层
- **自编译验证** — Skill Compiler 用自己的 Pass 6 评估了自己，首轮 85.5 分检出 5 个 issue，修复后 100 分通过。审查记录见 [docs/self-compilation-audit.md](docs/self-compilation-audit.md)

---

## Compiler Pipeline

| Pass | 执行 | 职责 |
|------|------|------|
| **0 Triage** | ✅ 总是 | 判断输入是否值得编译为 Skill |
| **1 Analyze** | ✅ 总是 | 理解 Prompt：目标 / 输入输出 / 边界 / 假设 |
| **2 Extract** | ✅ 总是 | 能力图谱 + 知识清单 + 角色矩阵 |
| **3 Design** | ✅ 总是 | 架构类型 + 模块拆分 + Workflow + 目录结构 + 自测用例派生 |
| **4 Generate** | ✅ 总是 | 基于 IR 生成完整 Skill 文件包 |
| **5 Optimize** | ⚠️ 条件 | Prompt > 500字 / 重复 / multi-agent 时执行 |
| **6 Validate** | ✅ 总是 | 三层评估：结构完整性（A）+ IR 一致性（B）+ 触发质量（C） |
| Plugin Discovery | ❌ 条件 | 涉及外部能力（搜索/GitHub/DB/MCP）时执行 |
| Example Generation | ❌ 条件 | 涉及复杂流程/规则/评分体系时执行 |

---

## 文件结构

```
skill-compiler/
├── SKILL.md                        # 入口 + 路由 manifest（< 150 行）
├── README.md                       # 本文件
├── references/
│   ├── pass-1-analyze.md           # Pass 1: 理解 Prompt
│   ├── pass-2-extract.md           # Pass 2: 能力/知识/角色抽取
│   ├── pass-3-design.md            # Pass 3: 架构设计 + 自测用例派生
│   ├── pass-4-generate.md          # Pass 4: 生成文件包
│   ├── pass-5-optimize.md          # Pass 5: 条件优化
│   ├── pass-6-validate.md          # Pass 6: 三层评估（A 结构 / B IR 一致性 / C 触发质量）
│   ├── anti-patterns.md            # 反模式定义（AP-02/04/06/07/12）
│   ├── plugin-discovery.md         # 条件 Pass: 插件识别
│   └── example-generation.md       # 条件 Pass: 示例生成
├── templates/
│   ├── skill-md-template.md        # SKILL.md 输出模板
│   └── ir-schema.md                # Skill IR 中间表示 schema
├── examples/
│   ├── example-compilation.md      # 完整编译示例（Python 代码审查）
│   └── example-workflow-compilation.md  # Workflow 类型编译示例
├── schemas/
│   ├── ir-schema.json              # Skill IR JSON Schema（含 self_test_cases）
│   └── trace-schema.json           # 执行 trace 契约（含 evaluation 块）
└── docs/
    └── self-compilation-audit.md   # 自编译审计记录
```

---

## 快速开始

给 Skill Compiler 一个 Prompt，它会：

1. **Pass 0** — 判断是否值得编译（一次性问答会直接拒绝）
2. **Pass 1-3** — 分析 → 抽取 → 设计，产出 Skill IR（含自测用例）
3. **Pass 4** — 基于 IR 生成完整文件包
4. **Pass 5** — 条件触发优化
5. **Pass 6** — 三层评估（A 结构 / B IR 一致性 / C 触发质量），输出评分 + GO/NO-GO
6. 输出 **Compilation Report** + 完整 Skill 包

### Pass 6 评分公式

```
skill_quality_score = structural_pass_rate × 0.3
                    + ir_consistency_rate  × 0.4    ← 权重最高，IR 契约验证
                    + trigger_precision    × 0.3
```

| 分数 | Verdict |
|------|---------|
| ≥ 85 且 0 Critical | **GO** |
| 60-84 或有 Critical 但可修复 | **CONDITIONAL** |
| < 60 | **NO-GO** |

### 示例输入

```
你是一个 Python 代码审查专家。用户会给你一段 Python 代码，你需要：
1. 检查代码风格（PEP 8）
2. 检查常见 bug
3. 检查安全问题
4. 给出改进建议
5. 按严重程度分级：Critical / Warning / Info
```

### 示例输出

```
code-reviewer/
  SKILL.md                  # 80 行路由
  references/
    pep8-rules.md           # PEP 8 规则
    bug-patterns.md         # 常见 bug 模式
    security-checks.md      # 安全检查项
  templates/
    review-report.md        # 报告模板
  rubrics/
    severity-rubric.md      # 严重度分级
```

详见 [examples/example-compilation.md](examples/example-compilation.md)。

---

## 设计原则

| 原则 | 含义 |
|------|------|
| Prompt 不是 Skill | Skill = Role + Workflow + Knowledge + Decision Logic + Checklist + Rubric + Templates + Examples + Config + References + Output Schema |
| 重复内容外置 | 超过一次使用的内容 → `references/` |
| Prompt 最小化 | 知识外置，Workflow 独立，配置参数化 |
| 不照搬 Prompt | 以 Skill 为中心重新设计，保留"能力"而非"文字" |

---

## 与 SkillForge 的关系

Skill Compiler 由 [SkillForge](https://github.com/qomob/skillforge) Full 模式构建，通过了完整的 5 层验证（Triage → Create → Validate → Audit → Deploy Decision），Compliance Score 100%，Gaming Gate PASS。

---

## Changelog

### v1.1.0 — 评估闭环补全

**核心变更：** Pass 6 从单一结构审查升级为三层评估，解决了"会生不会评"的问题。

| 变更 | 说明 |
|------|------|
| **Pass 6 三层评估** | Layer A 结构（五角色）+ Layer B IR 一致性（B1-B8）+ Layer C 触发质量（C1-C3） |
| **IR 新增 self_test_cases** | Pass 3 Step 3.9 从 boundary + capability_graph 派生三类测试用例（positive/negative/near_miss） |
| **评分公式** | `skill_quality_score = structural×0.3 + ir_consistency×0.4 + trigger_precision×0.3` |
| **trace schema** | 新增 evaluation 块（三层分数 + 综合评分） |
| **自编译验证** | 首轮 85.5 分检出 5 个 issue，修复后 100 分通过 |

**核心洞察：** IR 既是生成的输入，也是验证的 oracle。不需要外部裁判——Pass 1-3 已经写完了"这个 skill 该长什么样"，Pass 6 回头拿 IR 验产出即可闭环。

### v1.0.0 — 初始版本

6 核心 Pass + 3 条件 Pass 的编译器架构，Skill IR 中间表示，五角色架构审查。

---

## 加入群聊

<div align="center">
  <img src="https://qomob.ai/xskill.jpg" width="600" alt="XSkill">
</div>

---

## License

[MIT](https://opensource.org/licenses/MIT)
