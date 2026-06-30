<div align="center">

# Skill Compiler

**任意来源 → Skill IR → Optimized Skill Package**

把任意来源（文本 Prompt、PDF、视频、网页、图片、文档）编译成可复用、可维护、可持续演化的 AI Skill

[![Author](https://img.shields.io/badge/Author-qomob.ai-blue)](https://qomob.ai)
[![Version](https://img.shields.io/badge/Version-v2.0.0-green.svg)](https://github.com/qomob/SkillCompiler)
[![Language](https://img.shields.io/badge/Language-%E4%B8%AD%E6%96%87-red.svg)](https://github.com/qomob/SkillCompiler)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Built with](https://img.shields.io/badge/Built_with-SkillForge-violet.svg)](https://github.com/qomob/skillforge)

</div>

---

## 这是什么

Skill Compiler 是一个 **Meta Skill（元技能）**——它的输入是任意来源（文本 Prompt、PDF、视频、网页、图片、文档），输出是一个完整的、结构化的 AI Skill 文件包。

它不是"Prompt 优化器"。它是一个 **能力编译器**：保留来源背后的"能力（Capability）"，而非来源本身的文字。

```
Source (Prompt / PDF / Video / URL / Image / Doc)
      │
      ▼
  Ingest → Triage → Analyze → Extract → Design → Generate → Optimize → Validate
      │
      ▼
  Complete Skill Package
```

---

## 为什么用它

| 对比 | 直接用 Prompt | 手写 Skill | **Skill Compiler** |
|------|--------------|-----------|-------------------|
| 复用性 | 一次性，每次重写 | 高，但门槛高 | 高，且开箱即用 |
| 维护成本 | 改一处要改全文 | 需手动同步多处 | 知识外置，模块独立 |
| 质量保障 | 无 | 靠经验 | 四层评估闭环（含压力测试） |
| 多源输入 | 不支持 | 需手动预处理 | PDF/视频/网页/图片/文档自动摄取 |
| 平台适配 | 不适用 | 需手动改格式 | 支持 TRAE / Claude / Generic |
| 诚实边界 | 无 | 容易遗漏 | 强制声明局限性 + 失败模式 |

**适合的场景：**
- 你有一个反复使用的 Prompt，想升级成可维护的 Skill
- 你有 PDF/视频/网页等素材，想提炼成可复用的能力
- 你想批量生成符合特定平台规范的 Skill

**不适合的场景：**
- 一次性问答（直接问就行）
- 纯翻译/摘要（直接做）
- 从零设计全新能力（没有源材料）

---

## 快速开始

给 Skill Compiler 一个源材料（Prompt / 文件 / URL），它会自动走完整编译流程：

```
1. Pass 0  — 判断是否值得编译 + 选平台 + 选模式 + 设预算
2. Pass 1-3 — 分析 → 抽取 → 设计，产出 Skill IR（含自测用例）
3. Pass 4  — 基于 IR + 平台 profile 生成文件包
4. Pass 5  — 条件优化（去重 + IR 瘦身）
5. Pass 6  — 四层评估，输出评分 + GO/NO-GO
```

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
  SKILL.md                  # 入口 + 路由
  references/
    pep8-rules.md           # PEP 8 规则
    bug-patterns.md         # 常见 bug 模式
    security-checks.md      # 安全检查项
  templates/
    review-report.md        # 报告模板
  rubrics/
    severity-rubric.md      # 严重度分级
```

完整编译过程（含每个 Pass 的 IR 产出）见：
- [examples/example-compilation.md](examples/example-compilation.md) — Python 代码审查（normal 架构）
- [examples/example-workflow-compilation.md](examples/example-workflow-compilation.md) — API 文档生成器（workflow 架构）

### 编译模式

| 模式 | Token 开销 | 适用场景 |
|------|-----------|---------|
| `quick` | 低（~3 次调用） | Prompt < 200 字，已熟悉 Skill 结构 |
| `full` | 高（~6+ 次调用） | 复杂 Prompt，需要完整能力提取与验证（默认） |
| `audit` | 中（~2 次调用） | 评估已有 Skill，不生成新文件 |

---

## Compiler Pipeline

| Pass | 执行 | 职责 |
|------|------|------|
| **I Ingestion** | ⚠️ 条件 | 多源摄取：PDF/视频/网页/图片/文档 → 结构化内容 + 来源溯源 |
| **0 Triage** | ✅ 总是 | 判断是否值得编译 + 选平台 + 选模式 + 设 Token 预算 |
| **1 Analyze** | ✅ 总是 | 理解内容：目标 / 输入输出 / 边界 / 假设 |
| **2 Extract** | ✅ 总是 | 能力图谱 + 知识清单（含证据分级）+ 角色矩阵 |
| **3 Design** | ✅ 总是 | 架构类型 + 模块拆分（含诚实边界）+ Workflow + 目录结构 + 自测用例 |
| **4 Generate** | ✅ 总是 | 基于 IR + 目标平台 profile 生成符合平台规范的完整 Skill 文件包 |
| **5 Optimize** | ⚠️ 条件 | 内容 > 500字 / 重复 / multi-agent 时执行 |
| **6 Validate** | ✅ 总是 | 四层评估：结构（A）+ IR 一致性（B）+ 触发质量（C，含压力测试）+ 平台合规（D） |
| Plugin Discovery | ❌ 条件 | 涉及外部能力（搜索/GitHub/DB/MCP）时执行 |
| Example Generation | ❌ 条件 | 涉及复杂流程/规则/评分体系时执行 |

### Pass 6 评分

```
skill_quality_score = structural_pass_rate     × 0.2    (Layer A)
                    + ir_consistency_rate      × 0.3    (Layer B)
                    + trigger_precision        × 0.25   (Layer C)
                    + platform_compliance_rate × 0.25   (Layer D)
```

| 分数 | Verdict |
|------|---------|
| ≥ 85 且 0 Critical | **GO** |
| 60-84 或有 Critical 但可修复 | **CONDITIONAL** |
| < 60 | **NO-GO** |

---

## 核心能力

- **多源摄取** — PDF/视频/网页/图片/文档自动解析（pdftotext/ffmpeg+whisper/tesseract/WebFetch），标准化为结构化内容 + 来源溯源
- **证据分级** — 每条知识携带 primary/secondary/inferred 证据等级，冲突信息保留标注而非静默消除
- **诚实边界** — 生成的 skill 强制声明局限性/失败模式/适用前提
- **并行提取器** — 五个专项提取器（框架/原则/案例/反例/术语）并行扫描长内容，三重验证筛入知识库
- **压力测试** — 构造边界交叉区诱饵输入验证 description 锐利度
- **平台适配** — 支持 TRAE / Claude / Generic，自动按平台规范渲染 frontmatter 与文件结构
- **Token 预算控制** — 设定预算上限，超限时自动降级模式
- **三层渐进加载** — 生成的 Skill 遵循 L1 触发 / L2 路由 / L3 懒加载分层

---

## 文件结构

```
skill-compiler/
├── SKILL.md                        # 入口 + 路由 manifest（< 300 行）
├── README.md                       # 本文件
├── CHANGELOG.md                    # 版本变更日志
├── profiles/                       # 目标平台规范
│   ├── trae.md                     #   TRAE IDE Skill 规范
│   ├── claude.md                   #   Claude.ai / Claude Code 规范
│   └── generic.md                  #   默认通用规范
├── references/                     # 各 Pass 的详细指令（懒加载）
│   ├── pass-ingestion.md           #   Pass I: 多源摄取
│   ├── pass-1-analyze.md           #   Pass 1: 理解内容
│   ├── pass-2-extract.md           #   Pass 2: 能力/知识/角色抽取
│   ├── pass-3-design.md            #   Pass 3: 架构设计 + 自测用例
│   ├── pass-4-generate.md          #   Pass 4: 生成文件包
│   ├── pass-5-optimize.md          #   Pass 5: 条件优化
│   ├── pass-6-validate.md          #   Pass 6: 四层评估
│   ├── evidence-grading.md         #   证据分级体系
│   ├── honest-boundaries.md        #   诚实边界规范
│   ├── parallel-extractors.md      #   并行提取器 + 三重验证
│   ├── anti-patterns.md            #   反模式定义
│   ├── plugin-discovery.md         #   条件 Pass: 插件识别
│   └── example-generation.md       #   条件 Pass: 示例生成
├── templates/
│   ├── skill-md-template.md        #   SKILL.md 输出模板
│   └── ir-schema.md                #   Skill IR 中间表示 schema
├── examples/
│   ├── example-compilation.md      #   完整编译示例（Python 代码审查）
│   └── example-workflow-compilation.md  # Workflow 类型编译示例
├── schemas/
│   ├── ir-schema.json              #   Skill IR JSON Schema
│   └── trace-schema.json           #   执行 trace 契约
└── docs/
    └── self-compilation-audit.md   #   自编译审计记录
```

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

版本演进历史见 [CHANGELOG.md](CHANGELOG.md)。

---

## 加入群聊

<div align="center">
  <img src="https://qomob.ai/xskill.jpg" width="600" alt="XSkill">
</div>

---

## License

[MIT](https://opensource.org/licenses/MIT)
