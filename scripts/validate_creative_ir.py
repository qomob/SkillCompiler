#!/usr/bin/env python3
"""Validate Creative Skill IR JSON against schemas/creative-ir-schema.json required constraints.

Creative Compiler Pass C3→C4 Decision Gate 的 harness 层强制。
除 schema 结构约束外，还覆盖判断回路与 v3.1 能力层的核心业务规则：
  #1 judgment.weighting 键与 dimensions 一一对应，权重和 = 1.0（±0.05）
  #2 revision.diagnose_before_rewrite=false 仅允许 quick 模式
  #3 所有 source_refs.document_id 必须可在 provenance.source_documents 中溯源
  #4 policy.priorities ≥2（创造能力的核心是取舍，≥2 项才有取舍可言）
  #5 full 模式禁止关闭独立评价器（evaluation.independent_judge=false → Evaluator Leakage）
  #6 v3.1 起发散为边际增益模型：legacy territory_count 报错；target < min 报错
  #7 full 模式 style.fingerprint 必须为 measured（estimated 仅 quick 模式允许，WARN）
  #8 warning 级：confidence < 0.6 / 示例缺 explanation / policy 无 tradeoffs / 缺 evaluation 配置

用法: python3 scripts/validate_creative_ir.py <creative-ir.json>
退出码: 0=合法 1=不合法 2=文件/用法错误
"""
import json
import sys

CREATIVE_TYPES = {"creative-writing", "copywriting", "advertising", "script", "branding", "naming", "founder-ip", "visual-concept", "hybrid"}
PLATFORMS = {"trae", "claude", "generic"}
MODES = {"quick", "full"}
PRIORITIES = {"critical", "high", "medium", "low"}
TENDENCIES = {"positive", "negative"}
EXAMPLE_TYPES = {"positive", "negative", "contrastive", "before-after"}
OUTPUT_FORMATS = {"text", "markdown", "json", "script", "structured-content"}
ORIGINS = {"explicit", "inferred", "heuristic", "generated"}
FAILURE_TYPES = {"generic", "off-brand", "too-commercial", "too-ai", "boring", "unclear", "redundant"}
FP_SOURCES = {"measured", "estimated"}
SEPARATIONS = {"perspective", "prompt", "model"}
NOVELTY_FRAMES = {"category_conventions", "source_examples", "own_output_history"}
FINGERPRINT_REQUIRED = ["sentence_length", "abstraction", "concreteness", "emotional_explicitness", "narrative_density", "ai_pattern_risk"]
RUNTIME_DEPS = ["creativity", "style_dependency", "context_dependency", "knowledge_dependency", "iteration_dependency", "judgment_dependency"]

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def require(obj, field, path, check=None):
    if not isinstance(obj, dict) or field not in obj:
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


def obj_list_min(n):
    def check(val, path):
        if not isinstance(val, list) or len([x for x in val if isinstance(x, dict)]) < n:
            err(f"{path} 需至少 {n} 条 object（当前 {len(val) if isinstance(val, list) else type(val).__name__} 条）")
    return check


def unit_number(val, path):
    if not isinstance(val, (int, float)) or isinstance(val, bool) or not 0 <= val <= 1:
        err(f"{path} 必须为 0-1 数值，实际为 {val!r}")


def check_source_refs(refs, path, doc_ids):
    if not isinstance(refs, list):
        return
    for i, ref in enumerate(refs):
        p = f"{path}[{i}]"
        if not isinstance(ref, dict):
            err(f"{p} 必须为 object")
            continue
        require(ref, "document_id", p, non_empty_str)
        require(ref, "origin", p, in_enum(ORIGINS))
        require(ref, "confidence", p, unit_number)
        doc_id = ref.get("document_id")
        if isinstance(doc_id, str) and doc_ids and doc_id not in doc_ids:
            err(f"{p}.document_id {doc_id!r} 未在 provenance.source_documents 中登记（编译器推断不能脱离溯源）")


def check_example(ex, path, expected_type=None):
    if not isinstance(ex, dict):
        err(f"{path} 必须为 object")
        return
    require(ex, "id", path, non_empty_str)
    require(ex, "type", path, in_enum(EXAMPLE_TYPES))
    if expected_type and ex.get("type") != expected_type:
        err(f"{path}.type 应为 {expected_type!r}，实际为 {ex.get('type')!r}")
    require(ex, "output", path, non_empty_str)
    if not isinstance(ex.get("explanation"), str) or not ex["explanation"].strip():
        warn(f"{path}.explanation 缺失——无解释的示例只是语料，不是示范学习材料")


def main():
    if len(sys.argv) != 2:
        print("用法: python3 scripts/validate_creative_ir.py <creative-ir.json>", file=sys.stderr)
        sys.exit(2)
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            ir = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: 无法读取/解析 Creative IR 文件: {e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(ir, dict):
        print("FAIL: Creative IR 顶层必须为 object")
        sys.exit(1)

    # --- meta ---
    meta = require(ir, "meta", "ir")
    if isinstance(meta, dict):
        for fld in ("name", "version", "compiler_version", "source_hash"):
            require(meta, fld, "meta", non_empty_str)
        require(meta, "type", "meta", in_enum(CREATIVE_TYPES))
        require(meta, "confidence", "meta", unit_number)
        if "target_platform" in meta:
            require(meta, "target_platform", "meta", in_enum(PLATFORMS))
        if "compilation_mode" in meta:
            require(meta, "compilation_mode", "meta", in_enum(MODES))
        if isinstance(meta.get("confidence"), (int, float)) and meta["confidence"] < 0.6:
            warn(f"meta.confidence={meta['confidence']} < 0.6：材料不足，必须在产物 honest-boundaries 中显式声明")

    mode = meta.get("compilation_mode") if isinstance(meta, dict) else None

    # provenance 溯源登记表（knowledge/principles 等的 source_refs 均须可溯源）
    doc_ids = set()
    prov = ir.get("provenance")
    if isinstance(prov, dict) and isinstance(prov.get("source_documents"), list):
        doc_ids = {d.get("document_id") for d in prov["source_documents"] if isinstance(d, dict)}

    # --- intent ---
    intent = require(ir, "intent", "ir")
    if isinstance(intent, dict):
        require(intent, "primary_goal", "intent", non_empty_str)
        require(intent, "output_type", "intent", non_empty_str)

    # --- knowledge（可选：领域知识，存在时校验结构与溯源）---
    knowledge = ir.get("knowledge")
    if knowledge is not None:
        if not isinstance(knowledge, dict):
            err("knowledge 必须为 object")
        else:
            facts = knowledge.get("domain_facts")
            if facts is not None:
                if not isinstance(facts, list):
                    err("knowledge.domain_facts 必须为 array")
                else:
                    for i, fact in enumerate(facts):
                        p = f"knowledge.domain_facts[{i}]"
                        if not isinstance(fact, dict):
                            err(f"{p} 必须为 object")
                            continue
                        require(fact, "content", p, non_empty_str)
                        require(fact, "source_refs", p)
                        check_source_refs(fact.get("source_refs"), f"{p}.source_refs", doc_ids)

    # --- style (Style Fingerprint 完整性 + 实测来源，业务规则 #7) ---
    style = require(ir, "style", "ir")
    if isinstance(style, dict):
        fp = require(style, "fingerprint", "style")
        if isinstance(fp, dict):
            for fld in FINGERPRINT_REQUIRED:
                require(fp, fld, "style.fingerprint", unit_number)
            for k, v in fp.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool) and not 0 <= v <= 1:
                    err(f"style.fingerprint.{k} 必须为 0-1 数值，实际为 {v!r}")
        fp_source = style.get("fingerprint_source")
        if fp_source is not None and fp_source not in FP_SOURCES:
            err(f"style.fingerprint_source 必须为 {sorted(FP_SOURCES)} 之一，实际为 {fp_source!r}")
        if fp_source != "measured":
            if mode == "full":
                err("full 模式 style.fingerprint_source 必须为 measured——Fingerprint 数值须来自 scripts/style_analyzer.py 实测，禁止凭印象填数值（Gotcha #14）")
            else:
                warn("style.fingerprint_source 非 measured（或缺失）——Fingerprint 为估计值，漂移检测基准不可靠，建议用 style_analyzer.py 实测")

    # --- principles ---
    principles = require(ir, "principles", "ir", obj_list_min(1))
    if isinstance(principles, list):
        for i, pr in enumerate(principles):
            p = f"principles[{i}]"
            if not isinstance(pr, dict):
                err(f"{p} 必须为 object")
                continue
            require(pr, "id", p, non_empty_str)
            require(pr, "statement", p, non_empty_str)
            require(pr, "priority", p, in_enum(PRIORITIES))
            require(pr, "source_refs", p)
            check_source_refs(pr.get("source_refs"), f"{p}.source_refs", doc_ids)

    # --- heuristics ---
    heuristics = ir.get("heuristics")
    if isinstance(heuristics, list):
        for i, h in enumerate(heuristics):
            p = f"heuristics[{i}]"
            if not isinstance(h, dict):
                err(f"{p} 必须为 object")
                continue
            require(h, "id", p, non_empty_str)
            require(h, "signals", p, str_list_min(1))
            require(h, "tendency", p, in_enum(TENDENCIES))
            require(h, "strength", p, unit_number)
            check_source_refs(h.get("source_refs"), f"{p}.source_refs", doc_ids)

    # --- constraints ---
    constraints = ir.get("constraints")
    if isinstance(constraints, dict):
        for cat in ("hard", "soft", "contextual", "creative"):
            items = constraints.get(cat)
            if items is None:
                continue
            if not isinstance(items, list):
                err(f"constraints.{cat} 必须为 array")
                continue
            for i, c in enumerate(items):
                p = f"constraints.{cat}[{i}]"
                if not isinstance(c, dict):
                    err(f"{p} 必须为 object")
                    continue
                require(c, "name", p, non_empty_str)
                if "weight" in c:
                    require(c, "weight", p, unit_number)

    # --- examples ---
    examples = require(ir, "examples", "ir")
    if isinstance(examples, dict):
        positive = require(examples, "positive", "examples")
        if isinstance(positive, list):
            if len(positive) < 1:
                err("examples.positive 需至少 1 条示例")
            for i, ex in enumerate(positive):
                check_example(ex, f"examples.positive[{i}]", expected_type="positive")
        for cat, ex_type in (("negative", "negative"), ("contrastive", "contrastive"), ("before_after", "before-after")):
            items = examples.get(cat)
            if items is None:
                continue
            if not isinstance(items, list):
                err(f"examples.{cat} 必须为 array")
                continue
            for i, ex in enumerate(items):
                check_example(ex, f"examples.{cat}[{i}]", expected_type=ex_type)

    # --- anti_patterns ---
    anti_patterns = ir.get("anti_patterns")
    if isinstance(anti_patterns, list):
        for i, ap in enumerate(anti_patterns):
            p = f"anti_patterns[{i}]"
            if not isinstance(ap, dict):
                err(f"{p} 必须为 object")
                continue
            require(ap, "id", p, non_empty_str)
            require(ap, "detection_signals", p, str_list_min(1))
            require(ap, "severity", p, in_enum(PRIORITIES))
            check_source_refs(ap.get("source_refs"), f"{p}.source_refs", doc_ids)

    # --- generation（业务规则 #6：边际增益模型）---
    generation = ir.get("generation")
    if isinstance(generation, dict):
        div = generation.get("divergence")
        if isinstance(div, dict):
            if "territory_count" in div:
                err("generation.divergence.territory_count 已被 v3.1 边际增益模型取代——使用 min_territories / target_territories / stop_when_marginal_gain_below")
            mn, tg = div.get("min_territories"), div.get("target_territories")
            if mn is not None and (not isinstance(mn, int) or isinstance(mn, bool) or mn < 1):
                err(f"generation.divergence.min_territories 必须 ≥1 整数，实际为 {mn!r}")
            if tg is not None and (not isinstance(tg, int) or isinstance(tg, bool) or tg < 1):
                err(f"generation.divergence.target_territories 必须 ≥1 整数，实际为 {tg!r}")
            if isinstance(mn, int) and isinstance(tg, int) and tg < mn:
                err(f"generation.divergence.target_territories({tg}) 不得小于 min_territories({mn})")
            sm = div.get("stop_when_marginal_gain_below")
            if sm is not None:
                require(div, "stop_when_marginal_gain_below", "generation.divergence", unit_number)

    # --- judgment（业务规则 #1）---
    judgment = require(ir, "judgment", "ir")
    if isinstance(judgment, dict):
        dims = require(judgment, "dimensions", "judgment", str_list_min(3))
        weighting = require(judgment, "weighting", "judgment")
        if isinstance(dims, list) and isinstance(weighting, dict):
            dim_set, weight_keys = set(dims), set(weighting.keys())
            if dim_set != weight_keys:
                only_dims = sorted(dim_set - weight_keys)
                only_weights = sorted(weight_keys - dim_set)
                err(f"judgment.weighting 键须与 dimensions 一一对应（缺权重: {only_dims}，多余键: {only_weights}）")
            total = sum(v for v in weighting.values() if isinstance(v, (int, float)) and not isinstance(v, bool))
            if weight_keys and not 0.95 <= total <= 1.05:
                err(f"judgment.weighting 权重和应为 1.0（±0.05），实际为 {round(total, 4)}")
        penalties = judgment.get("penalties")
        if isinstance(penalties, list):
            for i, pen in enumerate(penalties):
                p = f"judgment.penalties[{i}]"
                if not isinstance(pen, dict):
                    err(f"{p} 必须为 object")
                    continue
                require(pen, "name", p, non_empty_str)
                require(pen, "weight", p, unit_number)

    # --- revision（业务规则 #2）---
    revision = require(ir, "revision", "ir")
    if isinstance(revision, dict):
        enabled = require(revision, "enabled", "revision")
        if not isinstance(enabled, bool):
            err("revision.enabled 必须为 boolean")
        mr = require(revision, "max_rounds", "revision")
        if not isinstance(mr, int) or isinstance(mr, bool) or not 1 <= mr <= 5:
            err(f"revision.max_rounds 必须为 1-5 整数，实际为 {mr!r}")
        if revision.get("diagnose_before_rewrite") is False and mode != "quick":
            err("revision.diagnose_before_rewrite=false 仅允许 quick 模式（full 模式必须先 Critique 后 Revise）")

    # --- policy（业务规则 #4：决策模型必填）---
    policy = require(ir, "policy", "ir")
    if isinstance(policy, dict):
        require(policy, "priorities", "policy", str_list_min(2))
        tradeoffs = policy.get("tradeoffs")
        if not isinstance(tradeoffs, list) or not tradeoffs:
            warn("policy.tradeoffs 缺失——无取舍规则的 policy 退化为优先级口号")
        if isinstance(tradeoffs, list):
            for i, t in enumerate(tradeoffs):
                p = f"policy.tradeoffs[{i}]"
                if not isinstance(t, dict):
                    err(f"{p} 必须为 object")
                    continue
                for fld in ("when", "prefer", "rationale"):
                    require(t, fld, p, non_empty_str)
                check_source_refs(t.get("source_refs"), f"{p}.source_refs", doc_ids)
        drules = policy.get("decision_rules")
        if isinstance(drules, list):
            for i, d in enumerate(drules):
                p = f"policy.decision_rules[{i}]"
                if not isinstance(d, dict):
                    err(f"{p} 必须为 object")
                    continue
                require(d, "condition", p, non_empty_str)
                require(d, "action", p, non_empty_str)
        excs = policy.get("exceptions")
        if isinstance(excs, list):
            for i, e in enumerate(excs):
                p = f"policy.exceptions[{i}]"
                if not isinstance(e, dict):
                    err(f"{p} 必须为 object")
                    continue
                require(e, "context", p, non_empty_str)
                require(e, "override", p, non_empty_str)

    # --- evaluation（业务规则 #5：独立评价器）---
    evaluation = ir.get("evaluation")
    if evaluation is None:
        warn("evaluation 配置缺失——建议配置独立评价器（independent_judge）与 novelty 参照系，否则 Revision Gain 存在自证循环风险")
    elif not isinstance(evaluation, dict):
        err("evaluation 必须为 object")
    else:
        ij = evaluation.get("independent_judge")
        if ij is not None and not isinstance(ij, bool):
            err("evaluation.independent_judge 必须为 boolean")
        if ij is False and mode == "full":
            err("full 模式禁止 evaluation.independent_judge=false——Generator 与 Evaluator 不分离的 revision_gain 是 Evaluator Leakage（评价器偏爱自己的修改）")
        sep = evaluation.get("evaluator_separation")
        if sep is not None and sep not in SEPARATIONS:
            err(f"evaluation.evaluator_separation 必须为 {sorted(SEPARATIONS)} 之一，实际为 {sep!r}")
        novelty = evaluation.get("novelty")
        if isinstance(novelty, dict):
            frames = novelty.get("reference_frames")
            if isinstance(frames, list):
                for i, fr in enumerate(frames):
                    if fr not in NOVELTY_FRAMES:
                        err(f"evaluation.novelty.reference_frames[{i}] 必须为 {sorted(NOVELTY_FRAMES)} 之一，实际为 {fr!r}")
            elif frames is not None:
                err("evaluation.novelty.reference_frames 必须为 array")
        elif novelty is not None:
            err("evaluation.novelty 必须为 object")

    # --- learning ---
    learning = ir.get("learning")
    if learning is not None:
        if not isinstance(learning, dict):
            err("learning 必须为 object")
        else:
            mut = learning.get("mutation")
            if isinstance(mut, dict):
                if mut.get("requires_benchmark") is False:
                    warn("learning.mutation.requires_benchmark=false——跳过回归的 skill 升级是赌博，C5 将判 CONDITIONAL")
                if mut.get("requires_human_approval") is False:
                    warn("learning.mutation.requires_human_approval=false——静默升级 skill 版本违反所有权边界，C5 将判 CONDITIONAL")
                mpo = mut.get("min_pattern_occurrences")
                if mpo is not None and (not isinstance(mpo, int) or isinstance(mpo, bool) or mpo < 3):
                    err(f"learning.mutation.min_pattern_occurrences 必须 ≥3（单例反馈不改规则），实际为 {mpo!r}")

    # --- memory ---
    memory = ir.get("memory")
    if isinstance(memory, dict):
        fm = memory.get("failure_memory")
        if isinstance(fm, list):
            for i, item in enumerate(fm):
                p = f"memory.failure_memory[{i}]"
                if not isinstance(item, dict):
                    err(f"{p} 必须为 object")
                    continue
                require(item, "idea", p, non_empty_str)
                require(item, "reasons", p, str_list_min(1))
                require(item, "failure_type", p, in_enum(FAILURE_TYPES))

    # --- output ---
    output = require(ir, "output", "ir")
    if isinstance(output, dict):
        require(output, "format", "output", in_enum(OUTPUT_FORMATS))
        vr = output.get("variants_required")
        if vr is not None and (not isinstance(vr, int) or isinstance(vr, bool) or vr < 1):
            err(f"output.variants_required 必须 ≥1，实际为 {vr!r}")

    # --- runtime_profile ---
    rp = ir.get("runtime_profile")
    if isinstance(rp, dict):
        for fld in RUNTIME_DEPS:
            if fld in rp:
                require(rp, fld, "runtime_profile", unit_number)

    # --- provenance ---
    if isinstance(prov, dict):
        sd = require(prov, "source_documents", "provenance")
        if isinstance(sd, list):
            for i, d in enumerate(sd):
                p = f"provenance.source_documents[{i}]"
                if not isinstance(d, dict):
                    err(f"{p} 必须为 object")
                    continue
                require(d, "document_id", p, non_empty_str)
                require(d, "type", p, non_empty_str)
        require(prov, "extraction_run_id", "provenance", non_empty_str)
    elif "provenance" in ir:
        err("provenance 必须为 object")

    if errors:
        print(f"FAIL: Creative IR 未通过校验（{len(errors)} 处错误，{len(warnings)} 处警告）")
        for e in errors:
            print(f"  - {e}")
        for w in warnings:
            print(f"  - [WARN] {w}")
        sys.exit(1)
    for w in warnings:
        print(f"  - [WARN] {w}")
    print("PASS: Creative IR 校验通过（v3.1：判断回路 + 决策模型 + 实测 Fingerprint 就位），可进入 Pass C4")
    sys.exit(0)


if __name__ == "__main__":
    main()
