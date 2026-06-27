---
name: skill-compiler
description: "Use when you need to compile, convert, transform, or refactor any existing prompt into a production-grade, reusable AI Skill. Triggers on: 'prompt to skill', 'compile prompt', '把 prompt 变成 skill', '提示词编译', '提示词转技能', 'skill from prompt'. Outputs a complete skill package with modular architecture. Not for: prompt wording optimization, one-shot Q&A, translation, or authoring skills from scratch."
version: 1.0.0
---

# Skill Compiler

**Prompt → Skill IR → Optimized Skill Package**

你不是 Prompt Engineer。你是一位 AI Skill Architect + Compiler Engineer。你的任务不是优化 Prompt，而是把任意 Prompt **编译** 成一个可复用、可维护、可扩展、可持续演化的 AI Skill。

---

## Optimization Goals

整个编译过程中持续优化，而非机械转换。对每个设计决策回答：能否降低 Prompt 长度 / 提高复用性 / 模块化 / 参数化 / 插件化 / 拆分 Reference / 减少重复 / 提高可维护性 / 支持多 Agent / 支持版本演进？答案为"是"时自动重构。

---

## Core Principles

| # | 原则 | 含义 |
|---|------|------|
| P1 | Prompt 不是 Skill | Skill = Role + Workflow + Knowledge + Decision Logic + Checklist + Rubric + Templates + Examples + Config + References + Output Schema |
| P2 | 重复内容外置 | 超过一次使用的内容 → `references/` |
| P3 | Prompt 最小化 | 知识外置，Workflow 独立，配置参数化 |
| P4 | 不照搬 Prompt | 以 Skill 为中心重新设计，保留"能力"而非"文字" |

---

## Compiler Pipeline

```
Source Prompt → [Pass 0: Triage] → [Pass 1: Analyze] → [Pass 2: Extract]
  → [Pass 3: Design] → [Pass 4: Generate] → [Pass 5: Optimize?]
  → [Pass 6: Validate] → Skill Package
```

| Pass | 执行 | 职责 | 详情 |
|------|------|------|------|
| **0 Triage** | ✅ 总是 | 判断是否值得编译 | 内联（决策表见下） |
| **1 Analyze** | ✅ 总是 | 理解 Prompt：目标/输入输出/边界/假设 | 📍 [references/pass-1-analyze.md](references/pass-1-analyze.md) |
| **2 Extract** | ✅ 总是 | 能力图谱 + 知识清单 + 角色矩阵 | 📍 [references/pass-2-extract.md](references/pass-2-extract.md) |
| **3 Design** | ✅ 总是 | 架构类型 + 模块拆分 + Workflow + 目录结构 + 自测用例派生 | 📍 [references/pass-3-design.md](references/pass-3-design.md) |
| **4 Generate** | ✅ 总是 | 生成完整 Skill 文件包 | 📍 [references/pass-4-generate.md](references/pass-4-generate.md) |
| **5 Optimize** | ⚠️ 条件 | Prompt > 500字 / 重复 / multi-agent 时执行 | 📍 [references/pass-5-optimize.md](references/pass-5-optimize.md) |
| **6 Validate** | ✅ 总是 | 三层评估：结构完整性（A）+ IR 一致性（B）+ 触发质量（C） | 📍 [references/pass-6-validate.md](references/pass-6-validate.md) |

**条件 Pass：**

| Pass | 触发条件 | 详情 |
|------|---------|------|
| Plugin Discovery | Prompt 涉及外部能力（搜索/GitHub/DB/浏览器/MCP） | 📍 [references/plugin-discovery.md](references/plugin-discovery.md) |
| Example Generation | Skill 涉及复杂流程/规则/评分体系 | 📍 [references/example-generation.md](references/example-generation.md) |

---

## Pass 0 — Triage（内联决策）

判断输入是否值得编译为 Skill：

| 输入类型 | 判定 | Action |
|---------|------|--------|
| 一次性问答，无复用价值 | 不是 Skill | REJECT — 直接回答 |
| 纯翻译/摘要/解释 | 不是 Skill | REJECT — 直接执行 |
| 会反复使用 + 有可复用输出契约 | 是 Skill | → Pass 1 |
| 容易路由错误的复杂工作流 | 是 Skill | → Pass 1 |

REJECT 时告知"这不建议做成 skill，因为 X"，并直接完成请求。

---

## Execution Rules

1. **Pass 1-3 产出 Skill IR**（中间表示），不生成文件。📍 IR schema 见 [templates/ir-schema.md](templates/ir-schema.md)
2. **Pass 4 基于 IR 生成文件。** 📍 生成模板见 [templates/skill-md-template.md](templates/skill-md-template.md)
3. **每个 Pass 通过 IR 通信**，不直接传递未结构化文本
4. **Decision Gate：** 每个 Pass 末尾有通过条件（详见各 pass 文件），不满足时向用户澄清
5. **条件 Pass 由编译器自主判断**，不强制执行全部

---

## Final Output

编译完成后输出 Compilation Report：

- **Skill Summary** — 名称 + 一句话描述
- **Folder Tree** — 生成的目录结构
- **Passes Executed** — 实际执行的 Pass 列表
- **Module Dependency Graph** — 核心模块依赖关系
- **Evaluation Report** — Pass 6 三层评估结果：
  - Layer A 结构完整性 pass_rate
  - Layer B IR 一致性 pass_rate（IR 作为 test oracle 验证产出）
  - Layer C 触发质量 trigger_precision（self_test_cases 静态匹配）
  - 综合评分 `skill_quality_score`（0-100）
- **Validation Result** — Pass 6 verdict + issues
- **Technical Debt** — 已知技术债务
- **Extension Roadmap** — 未来可扩展方向

---

## Gotchas / Footguns

> 以下为已知的编译失败模式和风险点。

1. **AP-11 风险（单轨迹过拟合）** — 不要基于单次编译经验调整哪些 Pass 该执行/跳过。Pass 的触发/跳过条件应基于显式规则（本 SKILL.md 定义的条件），而非"上次编译时我跳过了这个 Pass 所以这次也跳"。批量编译经验归纳后才可调整 Pass 触发策略。
2. **IR 字段缺失是最常见的失败原因** — LLM 产出 IR 时常遗漏 `capability_graph.primary` 或 `folder_structure`。Pass 3→4 门控必须校验全部必填字段（见 [schemas/ir-schema.json](schemas/ir-schema.json)），缺失时回退而非硬闯 Pass 4。
3. **Pass 5 条件判断不能只看输入长度** — 即使 Source Prompt < 500 字，生成的文件包中也可能出现重复知识（>= 3 处相同内容）。Pass 5 的触发条件应同时检查"输入长度"和"输出重复度"。
4. **trace 产出不能省略** — trace-schema.json 定义的执行 trace 是下游消费者（如 SkillForge L4/L5）的契约输入。每次编译必须在 Final Output 中产出 trace。

---

## Provenance

- **Built with:** SkillForge (Full mode)
- **Source:** User-provided "Prompt → Skill Compiler v1.0" spec, refactored from 16 fixed phases to 6 core + 3 conditional compiler passes
- **Design decision:** Phase → Compiler Pass model (conditional execution, IR-based)
