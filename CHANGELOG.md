# Changelog

## v2.0.0 — 多源摄取与诚实边界

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

---

## v1.2.0 — 平台适配与成本控制

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

---

## v1.1.0 — 评估闭环补全

**核心变更：** Pass 6 从单一结构审查升级为三层评估，解决了"会生不会评"的问题。

| 变更 | 说明 |
|------|------|
| **Pass 6 三层评估** | Layer A 结构（五角色）+ Layer B IR 一致性（B1-B8）+ Layer C 触发质量（C1-C3） |
| **IR 新增 self_test_cases** | Pass 3 Step 3.9 从 boundary + capability_graph 派生三类测试用例（positive/negative/near_miss） |
| **评分公式** | `skill_quality_score = structural×0.3 + ir_consistency×0.4 + trigger_precision×0.3` |
| **trace schema** | 新增 evaluation 块（三层分数 + 综合评分） |
| **自编译验证** | 首轮 85.5 分检出 5 个 issue，修复后 100 分通过 |

**核心洞察：** IR 既是生成的输入，也是验证的 oracle。不需要外部裁判——Pass 1-3 已经写完了"这个 skill 该长什么样"，Pass 6 回头拿 IR 验产出即可闭环。

---

## v1.0.0 — 初始版本

6 核心 Pass + 3 条件 Pass 的编译器架构，Skill IR 中间表示，五角色架构审查。
