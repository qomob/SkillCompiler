# Skill IR (Intermediate Representation) Schema

**用途：** Pass 1-3 产出的中间表示，是 Pass 4 生成的输入。

---

## 完整 IR 结构

```json
{
  "meta": {
    "compiler_version": "1.0.0",
    "source_prompt_hash": "string",
    "created_at": "ISO8601"
  },

  "pass_1_analyze": {
    "prompt_summary": "string",
    "prompt_goal": {
      "stated": "string",
      "actual": "string"
    },
    "input_spec": {
      "type": "string | file | api | mixed",
      "description": "string",
      "inferred": false
    },
    "output_spec": {
      "type": "string | json | file | report",
      "description": "string",
      "inferred": false
    },
    "capability_hints": ["string"],
    "boundary": {
      "in_scope": ["string"],
      "out_of_scope": ["string"]
    },
    "hidden_assumptions": ["string"],
    "unknowns": ["string"]
  },

  "pass_2_extract": {
    "capability_graph": {
      "primary": ["string"],
      "secondary": ["string"],
      "graph": {}
    },
    "knowledge_inventory": {
      "rules": [
        {
          "content": "string",
          "source": "from source prompt | inferred",
          "target_file": "string"
        }
      ],
      "templates": [
        {
          "name": "string",
          "structure": "string",
          "target_file": "string"
        }
      ],
      "domain_knowledge": [
        {
          "content": "string",
          "domain": "string",
          "target_file": "string"
        }
      ],
      "examples": [
        {
          "type": "minimal | normal | complex",
          "content": "string",
          "target_file": "string"
        }
      ],
      "standards": [
        {
          "type": "scoring | quality | acceptance",
          "content": "string",
          "target_file": "string"
        }
      ],
      "best_practices": [
        {
          "content": "string",
          "target_file": "string"
        }
      ]
    },
    "role_matrix": {
      "existing": [
        {
          "name": "string",
          "responsibility": "string",
          "capabilities": ["string"],
          "should_split": false,
          "split_reason": "string"
        }
      ],
      "to_add": [
        {
          "name": "string",
          "reason": "string",
          "responsibility": "string"
        }
      ]
    }
  },

  "pass_3_design": {
    "architecture_type": "single-prompt | workflow | multi-agent",
    "workflow_pattern": "string | null",
    "single_skill_pattern": "tool-wrapper | generator | reviewer | inversion | pipeline",
    "module_decomposition": {
      "core_prompt": "string",
      "workflows": ["string"],
      "references": ["string"],
      "checklists": ["string"],
      "rubrics": ["string"],
      "templates": ["string"],
      "configs": ["string"]
    },
    "workflow_steps": [
      {
        "id": "string",
        "purpose": "string",
        "input": "string",
        "output": "string",
        "decision_gate": "string",
        "exit_criteria": "string",
        "retry_strategy": "string",
        "rollback_strategy": "string"
      }
    ],
    "reference_tree": ["string"],
    "folder_structure": "string"
  },

  "conditional_passes": {
    "plugins": {
      "executed": false,
      "triggered_by": ["string"],
      "plugins_identified": []
    },
    "examples": {
      "executed": false,
      "triggered_by": ["string"],
      "examples_generated": []
    }
  }
}
```

---

## IR 流转

```
Pass 1 → 写入 pass_1_analyze
Pass 2 → 读取 pass_1_analyze，写入 pass_2_extract
Pass 3 → 读取 pass_1 + pass_2，写入 pass_3_design
Pass 4 → 读取全部 IR，生成文件
Pass 5 → 读取生成结果，更新 IR（优化变更）
Pass 6 → 读取生成结果 + IR，输出 review
```

**IR 是唯一数据源。** 所有 Pass 通过 IR 通信，不直接传递未结构化文本。
