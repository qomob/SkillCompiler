#!/usr/bin/env python3
"""Validate Skill IR JSON against schemas/ir-schema.json required constraints.

Pass 3→4 Decision Gate 的 harness 层强制（AP-13 修复）。
覆盖 Gotcha #2（IR 字段缺失是最常见失败）与 Pass 3 IR 校验表 9 条。

用法: python3 scripts/validate_ir.py <ir.json>
退出码: 0=合法 1=不合法 2=文件/用法错误
"""
import json
import sys

PLATFORMS = {"trae", "claude", "generic"}
MODES = {"quick", "full", "audit"}
ARCH_TYPES = {"single-prompt", "workflow", "multi-agent"}
SKILL_PATTERNS = {"tool-wrapper", "generator", "reviewer", "inversion", "pipeline", "stateful-domain-os"}

errors = []


def err(msg):
    errors.append(msg)


def require(obj, field, path, check=None):
    if field not in obj:
        err(f"{path}.{field} 缺失")
        return None
    val = obj[field]
    if check:
        check(val, f"{path}.{field}")
    return val


def non_empty_str(val, path):
    if not isinstance(val, str) or not val.strip():
        err(f"{path} 必须为非空字符串")


def str_list_min(n):
    def check(val, path):
        if not isinstance(val, list) or len([x for x in val if isinstance(x, str) and x.strip()]) < n:
            err(f"{path} 需至少 {n} 条非空字符串（当前 {len(val) if isinstance(val, list) else type(val).__name__} 条）")
    return check


def in_enum(allowed):
    def check(val, path):
        if val not in allowed:
            err(f"{path} 必须为 {sorted(allowed)} 之一，实际为 {val!r}")
    return check


def main():
    if len(sys.argv) != 2:
        print("用法: python3 scripts/validate_ir.py <ir.json>", file=sys.stderr)
        sys.exit(2)
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            ir = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: 无法读取/解析 IR 文件: {e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(ir, dict):
        print("FAIL: IR 顶层必须为 object")
        sys.exit(1)

    # --- meta ---
    meta = require(ir, "meta", "ir")
    if isinstance(meta, dict):
        for fld in ("compiler_version", "source_prompt_hash", "created_at"):
            require(meta, fld, "meta", non_empty_str)
        require(meta, "target_platform", "meta", in_enum(PLATFORMS))
        require(meta, "compilation_mode", "meta", in_enum(MODES))

    # --- pass_1_analyze ---
    p1 = require(ir, "pass_1_analyze", "ir")
    if isinstance(p1, dict):
        require(p1, "prompt_summary", "pass_1_analyze", non_empty_str)
        goal = require(p1, "prompt_goal", "pass_1_analyze")
        if isinstance(goal, dict):
            for fld in ("stated", "actual"):
                require(goal, fld, "pass_1_analyze.prompt_goal", non_empty_str)
        for spec in ("input_spec", "output_spec"):
            s = require(p1, spec, "pass_1_analyze")
            if isinstance(s, dict):
                require(s, "type", f"pass_1_analyze.{spec}")
                require(s, "description", f"pass_1_analyze.{spec}", non_empty_str)
        require(p1, "capability_hints", "pass_1_analyze")
        b = require(p1, "boundary", "pass_1_analyze")
        if isinstance(b, dict):
            require(b, "in_scope", "pass_1_analyze.boundary")
            require(b, "out_of_scope", "pass_1_analyze.boundary")

    # --- pass_2_extract ---
    p2 = require(ir, "pass_2_extract", "ir")
    if isinstance(p2, dict):
        cg = require(p2, "capability_graph", "pass_2_extract")
        if isinstance(cg, dict):
            require(cg, "primary", "pass_2_extract.capability_graph", str_list_min(1))
            require(cg, "secondary", "pass_2_extract.capability_graph")
            require(cg, "graph", "pass_2_extract.capability_graph")
        require(p2, "knowledge_inventory", "pass_2_extract")
        rm = require(p2, "role_matrix", "pass_2_extract")
        if isinstance(rm, dict):
            require(rm, "existing", "pass_2_extract.role_matrix")
            require(rm, "to_add", "pass_2_extract.role_matrix")

    # --- pass_3_design ---
    p3 = require(ir, "pass_3_design", "ir")
    if isinstance(p3, dict):
        require(p3, "architecture_type", "pass_3_design", in_enum(ARCH_TYPES))
        ssp = require(p3, "single_skill_pattern", "pass_3_design", in_enum(SKILL_PATTERNS))
        md = require(p3, "module_decomposition", "pass_3_design")
        if isinstance(md, dict):
            require(md, "core_prompt", "pass_3_design.module_decomposition", non_empty_str)
        require(p3, "folder_structure", "pass_3_design", non_empty_str)
        stc = require(p3, "self_test_cases", "pass_3_design")
        if isinstance(stc, dict):
            require(stc, "positive", "pass_3_design.self_test_cases", str_list_min(3))
            require(stc, "negative", "pass_3_design.self_test_cases", str_list_min(1))
            require(stc, "near_miss", "pass_3_design.self_test_cases")
        # 校验表 #8: stateful-domain-os → State 三件套齐全
        if ssp == "stateful-domain-os":
            sm = p3.get("state_management")
            if not isinstance(sm, dict) or sm.get("applicable") is not True:
                err("pass_3_design.state_management.applicable 必须为 true（stateful-domain-os）")
            else:
                require(sm, "context_schema_file", "pass_3_design.state_management", non_empty_str)
                require(sm, "validator_script", "pass_3_design.state_management", non_empty_str)
                fx = sm.get("fixtures")
                if not isinstance(fx, list) or len(fx) < 2:
                    err("pass_3_design.state_management.fixtures 需 ≥2（valid + invalid）")
        # 校验表 #9: skill_package 输入 → 必须为 stateful-domain-os
        pi = ir.get("pass_ingestion") or {}
        if isinstance(pi, dict) and pi.get("source_type") == "skill_package" and ssp != "stateful-domain-os":
            err("skill_package 输入时 single_skill_pattern 必须为 stateful-domain-os（无统一 Context 的合并是拼接）")

    if errors:
        print(f"FAIL: IR 未通过校验（{len(errors)} 处）")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("PASS: IR 校验通过，可进入 Pass 4")
    sys.exit(0)


if __name__ == "__main__":
    main()
