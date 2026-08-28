# Skill IR (Intermediate Representation) Schema

**用途：** Pass 1-3 产出的中间表示，是 Pass 4 生成的输入。本文件是人类可读速览。

> **SSOT 声明：** 字段的权威定义在 [schemas/ir-schema.json](../schemas/ir-schema.json)。修改 IR 结构时先改 JSON schema，再同步本文件；两者冲突时以 JSON schema 为准。校验用 `python3 scripts/validate_ir.py <ir.json>`。

---

## IR 结构速览

### meta（必填）

| 字段 | 类型 | 说明 |
|------|------|------|
| compiler_version | string | 当前版本号 |
| source_prompt_hash | string | 输入内容哈希 |
| created_at | ISO8601 | 创建时间 |
| target_platform | `trae \| claude \| generic` | 目标平台（Pass 0 确定） |
| compilation_mode | `quick \| full \| audit` | 编译模式 |
| token_budget | object | `{total_budget, mode_change_at_pct, current_estimate}` |
| platform_profile_applied | boolean | Pass 4 应用 profile 后置 true |

### pass_ingestion（v2.0，仅非纯文本输入时存在）

| 字段 | 类型 | 说明 |
|------|------|------|
| executed | boolean | 是否执行摄取 |
| source_type | enum | `direct_prompt / url / pdf / doc / markdown / image / video / audio / github_repo / skill_package / mixed` |
| extracted_by | string | 实际解析方式 |
| raw_content_hash | string | 内容哈希 |
| structured_content | string | 标准化文本（超 8000 字存摘要 + 外部引用） |
| evidence_grade | enum | 整份内容默认证据等级 `primary / secondary / inferred` |
| provenance | array | `[{source, extractor, confidence}]` 溯源链 |
| extraction_warnings | array | 质量警告（OCR 置信度低、扫描件、字幕缺失等） |

### pass_1_analyze（必填）

| 字段 | 类型 | 说明 |
|------|------|------|
| prompt_summary | string | 一句话概括 |
| prompt_goal | object | `{stated（字面）, actual（真正需要）}` |
| input_spec | object | `{type: string\|structured_content\|file\|api\|mixed, description, inferred}` |
| output_spec | object | `{type: string\|json\|file\|report, description, inferred}` |
| capability_hints | array | 命中的能力关键词 |
| state_signals | array | v2.3.0 状态需求信号（`cross_session/domain_object/profile/review_reconcile/memory/state_dependent`）。非空 → Pass 3 自动设 state_management.applicable=true |
| boundary | object | `{in_scope[], out_of_scope[]}` |
| hidden_assumptions | array | 隐含前提 |
| unknowns | array | 待澄清问题（≤3） |

### pass_2_extract（必填）

| 字段 | 类型 | 说明 |
|------|------|------|
| merge_plan | object | v2.3.0 仅 skill_package 输入时存在：`{source_skills[], dedup_decisions[], boundary_conflicts[], unified_context_schema}` |
| capability_graph | object | `{primary[](≥1), secondary[], graph}` |
| knowledge_inventory | object | 六类知识：`rules / templates / domain_knowledge / examples / standards / best_practices`，每条含 `{content, source, target_file, evidence, confidence}` |
| conflicts | array | v2.0 冲突保留：`{topic, versions[], resolution, note}`，不静默丢弃 |
| role_matrix | object | `{existing[{name, responsibility, capabilities, should_split, split_reason}], to_add[]}` |

examples 的 type enum：`minimal / normal / complex / edge-case / failure / anti-pattern`

### pass_3_design（必填）

| 字段 | 类型 | 说明 |
|------|------|------|
| architecture_type | enum | `single-prompt / workflow / multi-agent` |
| workflow_pattern | string\|null | 仅 workflow/multi-agent |
| single_skill_pattern | enum | `tool-wrapper / generator / reviewer / inversion / pipeline / stateful-domain-os` |
| state_management | object | v2.3.0 三件套：`{applicable, context_schema_file, validator_script, fixtures[], persistence_mode(file_io\|paste_yaml\|dual), write_discipline}` |
| knowledge_stratification | object | v2.2 变更频率分层：`{applicable, stable_layer[], timely_layer[], override_layer[], segment_loading}` |
| self_test_cases | object | `{positive[](≥3), negative[](≥1), near_miss[], structured_cases[]}`；structured_cases（v2.3.0）含程序化断言，生成 tests/cases.yaml |
| module_decomposition | object | `{core_prompt, workflows[], references[], checklists[], rubrics[], templates[], configs[]}` |
| workflow_steps | array | `{id, purpose, input, output, decision_gate, exit_criteria, retry_strategy, rollback_strategy}` |
| reference_tree | array | reference 文件列表 |
| folder_structure | string | 目录树 |

### conditional_passes（可选）

`{plugins: {executed, triggered_by[], plugins_identified[]}, examples: {executed, triggered_by[], examples_generated[]}}`

---

## IR 流转

```
Pass I → 写入 pass_ingestion（仅多源输入）
Pass 0 → 写入 meta.target_platform + meta.compilation_mode + meta.token_budget
Pass 1 → 写入 pass_1_analyze
Pass 2 → 读取 pass_1_analyze，写入 pass_2_extract
Pass 3 → 读取 pass_1 + pass_2，写入 pass_3_design
Pass 4 → 读取全部 IR + 对应平台 profile → 生成文件，设置 meta.platform_profile_applied
Pass 5 → 读取生成结果，更新 IR（优化变更）
Pass 6 → 读取生成结果 + IR，输出五层评估（含 Layer D 平台合规 + Layer E token 经济性）
```

**IR 是唯一数据源。** 所有 Pass 通过 IR 通信，不直接传递未结构化文本。
