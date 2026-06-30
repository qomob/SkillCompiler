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

- **多源摄取（v2.0 新增）** — Pass I Ingestion 支持 PDF/视频/网页/图片/文档等任意来源，内联解析指令（pdftotext/ffmpeg+whisper/tesseract/WebFetch），统一标准化为结构化内容 + 来源溯源
- **证据分级（v2.0 新增）** — 每条知识携带 primary/secondary/inferred 证据等级，冲突信息不静默消除而是保留标注
- **诚实边界（v2.0 新增）** — 生成的 skill 强制声明局限性/失败模式/适用前提，Pass 6 验证边界声明存在性
- **并行提取器（v2.0 新增）** — 五个专项提取器（框架/原则/案例/反例/术语）并行扫描长内容，经三重验证筛入知识库
- **压力测试（v2.0 新增）** — Pass 6 Layer C 新增诱饵题检测，构造边界交叉区的诱饵输入验证 description 锐利度
- **Skill 链接图（v2.0 新增）** — 多 skill 产出时生成 INDEX.md 技能地图，标注依赖/互补/冲突关系
- **编译器架构** — 6 个核心 Pass + 1 个条件摄取 Pass + 3 个条件 Pass，编译器自主判断需要执行哪些
- **Skill IR 中间表示** — Pass 1-3 产出 IR，Pass 4 基于 IR 生成文件，Pass 间通过 IR 通信
- **条件执行** — 简单 Prompt 跳过 Optimize，不涉及外部能力时跳过 Plugin Discovery
- **四层评估闭环** — Pass 6 四层评估：结构完整性（A）+ IR 一致性（B）+ 触发质量（C，含压力测试）+ 平台合规（D）
- **编译模式选择** — `quick` / `full` / `audit` 三种模式，在不同 token 成本与编译质量间做权衡
- **平台适配** — 支持 TRAE / Claude / Generic 三类宿主平台，自动按平台规范渲染 frontmatter 与文件结构
- **Token 预算控制** — 设定编译预算上限，超限时自动降级模式
- **三层渐进加载** — 生成的 Skill 遵循 L1 触发 / L2 路由 / L3 懒加载分层
- **自编译验证** — Skill Compiler 用自己的 Pass 6 评估了自己，首轮 85.5 分检出 5 个 issue，修复后自评通过。注意：此为自评结果（产出者即验证者），未经独立第三方验证。审查记录见 [docs/self-compilation-audit.md](docs/self-compilation-audit.md)

---

## Compiler Pipeline

| Pass | 执行 | 职责 |
|------|------|------|
| **I Ingestion** | ⚠️ 条件 | 多源摄取：PDF/视频/网页/图片/文档 → 标准化结构化内容 + 来源溯源（v2.0） |
| **0 Triage** | ✅ 总是 | 判断输入是否值得编译为 Skill + 选择目标平台 + 选择编译模式 + 设定 Token 预算 |
| **1 Analyze** | ✅ 总是 | 理解内容：目标 / 输入输出 / 边界 / 假设 |
| **2 Extract** | ✅ 总是 | 能力图谱 + 知识清单（含证据分级）+ 角色矩阵 |
| **3 Design** | ✅ 总是 | 架构类型 + 模块拆分（含诚实边界）+ Workflow + 目录结构 + 自测用例 + Skill 链接图 |
| **4 Generate** | ✅ 总是 | 基于 IR + 目标平台 profile 生成符合平台规范的完整 Skill 文件包 |
| **5 Optimize** | ⚠️ 条件 | 内容 > 500字 / 重复 / multi-agent 时执行；含 O9 编译去重 + O10 IR 瘦身 |
| **6 Validate** | ✅ 总是 | 四层评估：结构完整性（A）+ IR 一致性（B）+ 触发质量（C，含压力测试）+ 平台合规（D） |
| Plugin Discovery | ❌ 条件 | 涉及外部能力（搜索/GitHub/DB/MCP）时执行 |
| Example Generation | ❌ 条件 | 涉及复杂流程/规则/评分体系时执行 |

---

## 文件结构

```
skill-compiler/
├── SKILL.md                        # 入口 + 路由 manifest（< 300 行规范上限）
├── README.md                       # 本文件
├── profiles/                       # 目标平台规范（v1.2 新增）
│   ├── trae.md                     #   TRAE IDE Skill 规范
│   ├── claude.md                   #   Claude.ai / Claude Code 规范
│   └── generic.md                  #   默认通用规范
├── references/
│   ├── pass-ingestion.md         # Pass I: 多源摄取（PDF/视频/网页/图片/文档解析）（v2.0）
│   ├── pass-1-analyze.md           # Pass 1: 理解内容
│   ├── pass-2-extract.md           # Pass 2: 能力/知识/角色抽取（含证据分级）
│   ├── pass-3-design.md            # Pass 3: 架构设计 + 自测用例 + Skill 链接图
│   ├── pass-4-generate.md          # Pass 4: 生成文件包
│   ├── pass-5-optimize.md          # Pass 5: 条件优化 + O9/O10
│   ├── pass-6-validate.md          # Pass 6: 四层评估（A 结构 / B IR 一致性 / C 触发质量含压力测试 / D 平台合规）
│   ├── evidence-grading.md         # 证据分级体系（primary/secondary/inferred）+ 冲突保留（v2.0）
│   ├── honest-boundaries.md        # 诚实边界规范（局限性/失败模式/适用前提）（v2.0）
│   ├── parallel-extractors.md      # 五并行提取器 + 三重验证（v2.0）
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
│   ├── ir-schema.json              # Skill IR JSON Schema（含 target_platform / compilation_mode）
│   └── trace-schema.json           # 执行 trace 契约（含 cost_summary + Layer D）
└── docs/
    └── self-compilation-audit.md   # 自编译审计记录
```

---

## 快速开始

给 Skill Compiler 一个 Prompt，它会：

1. **Pass 0** — 判断是否值得编译 + 选择目标平台 + 选择编译模式 + 设定 Token 预算
2. **Pass 1-3** — 分析 → 抽取 → 设计，产出 Skill IR（含自测用例）
3. **Pass 4** — 基于 IR + 目标平台 profile 生成平台适配的文件包
4. **Pass 5** — 条件触发优化（含 O9 编译去重 + O10 IR 瘦身）
5. **Pass 6** — 四层评估（A 结构 / B IR 一致性 / C 触发质量 / D 平台合规），输出评分 + GO/NO-GO
6. 输出 **Compilation Report** + 完整 Skill 包（含 Cost Summary）

### Pass 6 评分公式（v1.2）

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

### v2.0.0 — 多源摄取与诚实边界

**核心变更：** 编译器输入从"纯文本 Prompt"扩展到"任意来源"（PDF/视频/网页/图片/文档），并引入证据分级与诚实边界，解决"多源内容如何编译"和"生成的 skill 不知道自己做不到什么"两个盲区。

**新增能力：**

- **Pass I Ingestion（多源摄取）** — 新增前置摄取阶段，内联解析指令（pdftotext / pdfplumber / ffmpeg+whisper / tesseract / pandoc / WebFetch），标准化为结构化内容 + 来源溯源链。纯文本 Prompt 时自动跳过。
- **证据分级体系** — 每条知识携带 `primary` / `secondary` / `inferred` 三级证据等级 + confidence。多源矛盾信息不静默消除，保留标注写入 conflicts.md。
- **诚实边界强制** — 生成的 skill 必须声明局限性 / 失败模式 / 适用前提。Pass 3 规划，Pass 6 Layer A 验证。
- **并行提取器** — 长内容或多源输入时启用五专项提取器（框架/原则/案例/反例/术语）并行扫描 + 三重验证。
- **压力测试（诱饵题）** — Pass 6 Layer C 新增 C4，构造边界交叉区诱饵输入验证 description 锐利度。
- **Skill 链接图** — 多 skill 产出时生成 INDEX.md 技能地图。

**架构变更：**

- IR Schema 新增 `pass_ingestion` 字段；`input_spec.type` 新增 `structured_content` 枚举值
- Trace Schema 的 pass_id 枚举新增 `ingestion`
- Pass 1/2/3/6 均接入 v2.0 能力

**新增文件：** `references/pass-ingestion.md`、`evidence-grading.md`、`honest-boundaries.md`、`parallel-extractors.md`

**方法论致谢：** 本版本的"多源蒸馏"、"证据分级"、"诚实边界"、"并行提取 + 三重验证"等设计思想，受到以下 MIT 协议开源项目的启发（仅吸收方法论，所有实现为原创撰写）：

- [cangjie-skill](https://github.com/kangarooking/cangjie-skill) (MIT) — 多源预处理、并行提取、压力测试
- [nuwa-skill](https://github.com/alchaincyf/nuwa-skill) (MIT) — 诚实边界、证据可追溯
- [immortal-skill](https://github.com/agenmod/immortal-skill) (MIT) — 矛盾保留、证据分级

### v1.2.0 — 平台适配与成本控制

**核心变更：** 引入目标平台适配层和编译成本控制，解决了"编译出的 skill 在哪些平台能跑"和"编译一次要花多少钱"两个架构级盲区。

| 变更 | 说明 |
|------|------|
| **平台适配层** | 新增 `profiles/` 目录（trae/claude/generic），Pass 0 选择平台，Pass 4 按 profile 渲染 frontmatter 与文件结构，Pass 6 Layer D 反向验证 |
| **编译模式** | 新增 `quick` / `full` / `audit` 三种模式，不同 token 开销与质量等级。默认 full |
| **Token 预算** | IR meta 新增 `token_budget` 字段，超预算时自动降级模式 |
| **Pass 6 Layer D** | 新增平台合规检查（D1-D8），验证 frontmatter 格式、description 规范、目录白名单等 |
| **评分公式调整** | 四层评估：structural×0.2 + ir_consistency×0.3 + trigger_precision×0.25 + platform_compliance×0.25 |
| **Pass 5 O9/O10** | 新增编译过程去重（O9）和 IR 瘦身（O10），降低编译环节的 token 消耗 |
| **Trace 补充** | trace-schema.json 新增 `compilation_config` 和 `cost_summary` 字段 |
| **Profile 自定义** | 高级用户可参考 profiles/ 格式编写自定义平台 profile |

**核心洞察：** Skill 编译器的输出应该是对目标平台"开箱即用"的，而不是需要用户手动适配。平台 profile 作为 oracle，从生成到验证形成闭环。

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
