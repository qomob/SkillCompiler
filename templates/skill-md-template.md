# SKILL.md Output Template

**用途：** Pass 4 生成 SKILL.md 时的参考模板。

---

```markdown
---
name: {{skill-name}}
description: "Use when {{触发场景}}. Triggers on: {{trigger1}}, {{trigger2}}, {{trigger3}}. {{核心功能一句话}}"
version: 1.0.0
---

# {{Skill Name}}

{{一句话定位——这个 Skill 做什么}}

## 核心流程

{{3-5 步流程概览，每步一句话，不展开细节}}

1. {{Step 1 概览}}
2. {{Step 2 概览}}
3. {{Step 3 概览}}

{{#if 需要先认识领域对象（inversion / stateful-domain-os 类）}}

## Onboarding 完整度评分

首次使用（无 Context）时先量化完整度，再决定是否直接进入工作流：

| 项目 | 分值 |
|------|------|
| {{关键维度 1（如业态/项目类型）}} | 20 |
| {{关键维度 2}} | 10 |
| {{...}} | ... |

- **≥ {{阈值，建议 70}}**：直接进入工作流
- **< 阈值**：选择题追问，最多 3 轮；缺失项用基准值补全并标注 `[基准填充]`

{{/if}}

{{#if 依赖平台能力（文件 I/O / 脚本执行 / 特定工具）}}

## 平台兼容

- **有文件 I/O（Trae / Codex 等）**：{{默认路径，如 context 自动读写}}
- **无文件 I/O（OpenClaw / Hermes 等）**：{{降级方式，如 Context 用对话粘贴；脚本不可用时按 {{基准}} 人工折算并标注 `[人工评分]`}}

{{/if}}

## 执行步骤

### Step 1 — {{名称}}

📍 加载文件: references/{{file}}.md

{{简要说明这一步做什么}}

**输入：** {{输入描述}}
**输出：** {{输出描述}}

### Step 2 — {{名称}}

📍 加载文件: references/{{file}}.md

{{简要说明}}

**输入：** {{输入}}
**输出：** {{输出}}

## 输出格式

📍 加载文件: templates/{{output-template}}.md

{{或直接描述输出 schema}}

## Gotchas / Footguns

> 上线后根据实际 failure case 填充。

- {{常见陷阱 1}}

---

## Provenance

- **Built with:** Skill Compiler v1.0.0
- **Source:** {{来源 Prompt 概述}}
```

---

## 模板变量

| 变量 | 说明 | 来源 |
|------|------|------|
| `{{skill-name}}` | kebab-case 名称 | Pass 3 IR |
| `{{Skill Name}}` | 显示名称 | Pass 3 IR |
| `{{触发场景}}` | 用户何时需要 | Pass 1 IR |
| `{{triggerN}}` | 触发词 | Pass 1 capability_hints |
| `{{核心功能一句话}}` | 核心功能 | Pass 1 prompt_summary |
| `{{file}}.md` | reference 文件名 | Pass 3 reference_tree |
| `{{output-template}}.md` | 输出模板 | Pass 3 module_decomposition.templates |
| `{{#if ...}}` 条件段 | Onboarding 评分段（Pass 3 Step 3.4c / inversion 类）、平台兼容段（state_management.persistence_mode=dual 或依赖脚本时）按需生成，不适用则整段省略 | Pass 3 IR |

**两个条件段的设计依据：**

- **Onboarding 完整度评分** — 给"先认识领域对象再干活"的 skill 一个"何时停止追问"的硬门槛（量化打分 + 追问轮次上限 + 基准填充标注），替代无限采访。
- **平台兼容** — 生成时按平台 profile 适配（Pass 0/Layer D）之外，还要声明**运行时能力降级路径**（无文件 I/O / 无脚本执行时怎么办），并要求降级产物带诚实标注（`[人工评分]` 等）。这是 honest-boundaries 的一部分：skill 能力因平台而异时不得隐瞒。
