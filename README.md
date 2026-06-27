<div align="center">

# Skill Compiler

**Prompt → Skill IR → Optimized Skill Package**

把任意 Prompt 编译成可复用、可维护、可持续演化的 AI Skill

[![Author](https://img.shields.io/badge/Author-qomob.ai-blue)](https://qomob.ai)
[![Version](https://img.shields.io/badge/Version-v1.0.0-green.svg)](https://github.com/qomob/skillforge)
[![Language](https://img.shields.io/badge/Language-%E4%B8%AD%E6%96%87-red.svg)](https://github.com/qomob/skillforge)
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
- **五角色架构审查** — Skill Architect / Knowledge Engineer / Workflow Designer / Prompt Engineer / Software Architect
- **三层渐进加载** — 生成的 Skill 遵循 L1 触发 / L2 路由 / L3 懒加载分层
- **自编译验证** — Skill Compiler 自身的 SKILL.md 经过了自己的 Pass 6 审查，审查记录见 [docs/self-compilation-audit.md](docs/self-compilation-audit.md)

---

## Compiler Pipeline

| Pass | 执行 | 职责 |
|------|------|------|
| **0 Triage** | ✅ 总是 | 判断输入是否值得编译为 Skill |
| **1 Analyze** | ✅ 总是 | 理解 Prompt：目标 / 输入输出 / 边界 / 假设 |
| **2 Extract** | ✅ 总是 | 能力图谱 + 知识清单 + 角色矩阵 |
| **3 Design** | ✅ 总是 | 架构类型 + 模块拆分 + Workflow + 目录结构 |
| **4 Generate** | ✅ 总是 | 基于 IR 生成完整 Skill 文件包 |
| **5 Optimize** | ⚠️ 条件 | Prompt > 500字 / 重复 / multi-agent 时执行 |
| **6 Validate** | ✅ 总是 | 五角色架构审查，输出 GO/NO-GO |
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
│   ├── pass-3-design.md            # Pass 3: 架构设计
│   ├── pass-4-generate.md          # Pass 4: 生成文件包
│   ├── pass-5-optimize.md          # Pass 5: 条件优化
│   ├── pass-6-validate.md          # Pass 6: 五角色审查
│   ├── plugin-discovery.md         # 条件 Pass: 插件识别
│   └── example-generation.md       # 条件 Pass: 示例生成
├── templates/
│   ├── skill-md-template.md        # SKILL.md 输出模板
│   └── ir-schema.md                # Skill IR 中间表示 schema
├── examples/
│   └── example-compilation.md      # 完整编译示例（Python 代码审查）
└── schemas/
    └── trace-schema.json           # 执行 trace 契约
```

---

## 快速开始

给 Skill Compiler 一个 Prompt，它会：

1. **Pass 0** — 判断是否值得编译（一次性问答会直接拒绝）
2. **Pass 1-3** — 分析 → 抽取 → 设计，产出 Skill IR
3. **Pass 4** — 基于 IR 生成完整文件包
4. **Pass 5** — 条件触发优化
5. **Pass 6** — 五角色架构审查
6. 输出 **Compilation Report** + 完整 Skill 包

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

## 加入群聊

<div align="center">
  <img src="https://qomob.ai/xskill.jpg" width="600" alt="XSkill">
</div>

---

## License

[MIT](https://opensource.org/licenses/MIT)
