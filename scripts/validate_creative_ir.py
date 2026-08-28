#!/usr/bin/env python3
"""Validate Creative Skill IR JSON against schemas/creative-ir-schema.json required constraints.

Creative Compiler Pass C3→C4 Decision Gate 的 harness 层强制。
除 schema 结构约束外，还覆盖判断回路的核心业务规则：
  #1 judgment.weighting 键与 dimensions 一一对应，权重和 = 1.0（±0.05）
  #2 revision.diagnose_before_rewrite=false 仅允许 quick 模式
  #3 所有 source_refs.document_id 必须可在 provenance.source_documents 中溯源
  #4 warning 级：confidence < 0.6 / 示例缺 explanation（不阻塞，但必须知情）

v3.1 新增——结构 Validator 之外的 Capability 检查（结构正确 ≠ 有能力）：
  #5 空洞评分维度（quality/good/better 类不可观察词）→ FAIL
  #6 权重完全均匀且无 policy.tradeoffs → WARN（均匀分配 = 没做判断）
  #7 空洞原则（"内容要精彩"式口号）→ WARN
  #8 anti-pattern 检测信号全部不可操作 → WARN
  #9/V1 full 模式缺 style.measurements（逐维测量证据）→ FAIL；quick 模式 → WARN
  #10/V2 advertising/branding/naming 缺 policy 或 policy 无 tradeoffs → FAIL（缺决策层的判断只是评分器）

v3.2 新增 Capability 检查（V1-V6 对照）：
  V1 同 #9：fingerprint 裸数字无 value+measurement 证据 → FAIL（full）
  V2 同 #10 + policy.tradeoffs 为空数组同样 FAIL（三类高决策型）
  V3 revision.rejudge_isolation=false（full 模式）→ FAIL（Evaluator 未与 Generator 解耦）
  V4 revision 缺 stop_conditions 且缺 marginal_gain_threshold → WARN（修订无收敛条件）
  V5 Novelty/Diversity 分开：文档级指标定义（creative-compiler.md §C5），静态不可查，跳过
  V6 learning.upgrade_gate.benchmark_required 缺失/false → FAIL（Learning 无 Regression Gate）

v3.2 新增字段校验：style.measurements / style.style_confidence / policy.priorities(对象+数值
priority) / tradeoffs.when(对象或字符串) / decision_rules.action(枚举) / risk_tolerance /
revision.rejudge_isolation / revision.marginal_gain_threshold / learning.capability_deltas(新结构) /
learning.mutation_proposals。

用法: python3 scripts/validate_creative_ir.py <creative-ir.json>
退出码: 0=合法 1=不合法 2=文件/用法错误
"""
import json
import re
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
FINGERPRINT_REQUIRED = ["sentence_length", "abstraction", "concreteness", "emotional_explicitness", "narrative_density", "ai_pattern_risk"]
RUNTIME_DEPS = ["creativity", "style_dependency", "context_dependency", "knowledge_dependency", "iteration_dependency", "judgment_dependency"]
# v3.1/v3.2 Capability 检查
POLICY_EXPECTED_TYPES = {"advertising", "branding", "naming"}  # 高决策型：缺 policy 或无 tradeoffs → FAIL
HOLLOW_DIMENSIONS = {"quality", "good", "better", "best", "overall", "general",
                     "高质量", "好坏", "优秀", "精彩", "整体质量"}
HOLLOW_PRINCIPLE_RE = re.compile(r"^(内容)?要(精彩|好看|有感染力|吸引人|高质量|优秀|打动人)[。.!！]?$")
OPERABLE_SIGNAL_MIN_LEN = 4  # 检测信号至少 4 字符才算可操作（"AI腔"这类纯标签不可执行）
RUNTIME_ROLE_ENUM = {"generation", "judgment", "revision", "routing", "evaluation", "documentation"}
# v3.2 policy / learning 结构枚举
POLICY_ACTIONS = {"keep", "revise", "reject", "explore_more"}
DELTA_TARGETS = {"style", "principle", "heuristic", "decision_policy", "anti_pattern", "judgment", "generation"}
DELTA_OPERATIONS = {"add", "remove", "increase", "decrease", "replace"}
PROPOSAL_STATUSES = {"proposed", "benchmark_passed", "approved", "rejected"}

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

    # --- style (Style Fingerprint 完整性) ---
    style = require(ir, "style", "ir")
    if isinstance(style, dict):
        fp = require(style, "fingerprint", "style")
        if isinstance(fp, dict):
            for fld in FINGERPRINT_REQUIRED:
                require(fp, fld, "style.fingerprint", unit_number)
            for k, v in fp.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool) and not 0 <= v <= 1:
                    err(f"style.fingerprint.{k} 必须为 0-1 数值，实际为 {v!r}")
        # #9/V1 capability：逐维测量证据（裸数字不可验证）
        fpp = style.get("fingerprint_provenance")
        if fpp is not None:
            if not isinstance(fpp, dict):
                err("style.fingerprint_provenance 必须为 object")
            else:
                require(fpp, "tool", "style.fingerprint_provenance", non_empty_str)
                if not fpp.get("corpus_sufficient", True):
                    warn("style.fingerprint_provenance.corpus_sufficient=false：语料不足，C2 应降 meta.confidence 并在诚实边界声明")
        elif mode == "full":
            warn("#9 style.fingerprint_provenance 缺失（full 模式）：fingerprint 可能非实测——由 scripts/style_analyzer.py 产出并携带溯源")
        meas = style.get("measurements")
        if meas is not None:
            if not isinstance(meas, dict):
                err("style.measurements 必须为 object（key 与 fingerprint 同构）")
            else:
                for dim, m in meas.items():
                    p = f"style.measurements.{dim}"
                    if not isinstance(m, dict):
                        err(f"{p} 必须为 object")
                        continue
                    require(m, "value", p, unit_number)
                    require(m, "measurement", p, non_empty_str)
                    if "sample_size" in m and not isinstance(m["sample_size"], (int, float)):
                        err(f"{p}.sample_size 必须为数值")
                    if "confidence" in m:
                        require(m, "confidence", p, unit_number)
        elif mode == "full":
            err("#9/V1 style.measurements 缺失（full 模式）：裸数字 fingerprint 不可验证——由 style_analyzer 产出 value+sample_size+confidence+measurement 证据对象")
        else:
            warn("#9/V1 style.measurements 缺失（quick 模式）：fingerprint 缺逐维测量证据")
        sc = style.get("style_confidence")
        if sc is not None:
            if not isinstance(sc, dict):
                err("style.style_confidence 必须为 object")
            else:
                for fld in ("feature_coverage", "overall_confidence"):
                    if fld in sc:
                        require(sc, fld, "style.style_confidence", unit_number)
                if isinstance(sc.get("overall_confidence"), (int, float)) and sc["overall_confidence"] < 0.6:
                    warn("style.style_confidence.overall_confidence < 0.6：Style Drift 阈值应放宽 + 建议人工复核（corpus 不足）")

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
            # #7 capability：空洞原则检测
            stmt = pr.get("statement") if isinstance(pr.get("statement"), str) else ""
            if HOLLOW_PRINCIPLE_RE.match(stmt.strip()) or len(stmt.strip()) <= 4:
                warn(f"#7 {p}.statement 为空洞口号（{stmt!r}）——不可执行的原则不产生判断能力")

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
            # #8 capability：检测信号可操作性
            signals = ap.get("detection_signals")
            if isinstance(signals, list) and not any(
                    isinstance(s, str) and len(s.strip()) >= OPERABLE_SIGNAL_MIN_LEN for s in signals):
                warn(f"#8 {p}.detection_signals 全部为不可操作短标签（如'AI腔'）——无具体文本信号的 anti-pattern 无法进入判断回路")

    # --- generation（v3.1：边际收益发散，territory_count 不再强制 ≥2）---
    generation = ir.get("generation")
    if isinstance(generation, dict):
        div = generation.get("divergence")
        if isinstance(div, dict):
            tc = div.get("territory_count")
            if tc is not None and (not isinstance(tc, int) or isinstance(tc, bool) or tc < 1):
                err(f"generation.divergence.territory_count 必须 ≥1，实际为 {tc!r}")
            mn = div.get("min_territories")
            if mn is not None and (not isinstance(mn, int) or isinstance(mn, bool) or mn < 1):
                err(f"generation.divergence.min_territories 必须 ≥1，实际为 {mn!r}")
            tg = div.get("target_territories")
            if tg is not None and (not isinstance(tg, int) or isinstance(tg, bool) or tg < 1):
                err(f"generation.divergence.target_territories 必须 ≥1，实际为 {tg!r}")
            if isinstance(mn, int) and isinstance(tg, int) and tg < mn:
                err(f"generation.divergence.target_territories({tg}) 不得小于 min_territories({mn})")
            if isinstance(tc, int) and isinstance(mn, int) and tc < mn:
                err(f"generation.divergence.territory_count({tc}) 低于 min_territories({mn})")
            sw = div.get("stop_when_marginal_gain_below")
            if sw is not None and (not isinstance(sw, (int, float)) or isinstance(sw, bool) or not 0 <= sw <= 1):
                err(f"generation.divergence.stop_when_marginal_gain_below 必须为 0-1 数值，实际为 {sw!r}")
            if isinstance(tg, int) and tg < 2:
                warn("generation.divergence.target_territories < 2：低发散配置——确认这是源材料特征（如品牌定位单一强方向），而非省事")

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
        # --- Capability 检查 #5/#6：维度可观察性与权重判断力 ---
        if isinstance(dims, list):
            hollow = [d for d in dims if isinstance(d, str) and d.strip().lower() in HOLLOW_DIMENSIONS]
            if hollow:
                err(f"#5 judgment.dimensions 含空洞维度 {hollow}——'quality/good' 类词什么都测不到（结构正确 ≠ 有判断能力），须替换为可观察维度（如 specificity=具体事实密度）")
        if isinstance(weighting, dict) and weighting:
            vals = [v for v in weighting.values() if isinstance(v, (int, float)) and not isinstance(v, bool)]
            if len(vals) == len(weighting) and vals and (max(vals) - min(vals)) < 0.01:
                has_tradeoffs = isinstance(ir.get("policy"), dict) and ir["policy"].get("tradeoffs")
                if not has_tradeoffs:
                    warn("#6 judgment.weighting 权重完全均匀且无 policy.tradeoffs——均匀分配 = 没做判断。专家的权重必然有偏重，或以 tradeoffs 显式声明取舍")
        # #10/V2 capability：高决策型缺 policy 或无 tradeoffs → FAIL（v3.2 从 WARN 升级）
        mtype = meta.get("type") if isinstance(meta, dict) else None
        policy_obj = ir.get("policy") if isinstance(ir.get("policy"), dict) else None
        if mtype in POLICY_EXPECTED_TYPES:
            if policy_obj is None:
                err(f"#10/V2 meta.type={mtype} 但缺 policy 层——缺决策规则的判断只是加权评分器，无法执行'抓住战略矛盾者优先'式专家取舍")
            elif not policy_obj.get("tradeoffs"):
                err(f"#10/V2 meta.type={mtype} 的 policy.tradeoffs 为空——没有取舍规则的决策层是空壳（评分之外必须声明冲突时保谁弃谁）")

    # --- policy（v3.1/v3.2）---
    policy = ir.get("policy")
    if policy is not None:
        if not isinstance(policy, dict):
            err("policy 必须为 object")
        else:
            priorities = policy.get("priorities")
            if priorities is not None:
                if not isinstance(priorities, list):
                    err("policy.priorities 必须为 array")
                else:
                    for i, pr in enumerate(priorities):
                        p = f"policy.priorities[{i}]"
                        if not isinstance(pr, dict):
                            err(f"{p} 必须为 object（v3.2 结构：dimension + priority 数值，不再接受纯字符串）")
                            continue
                        require(pr, "dimension", p, non_empty_str)
                        require(pr, "priority", p, unit_number)
            tradeoffs = policy.get("tradeoffs")
            if tradeoffs is not None:
                if not isinstance(tradeoffs, list):
                    err("policy.tradeoffs 必须为 array")
                else:
                    for i, t in enumerate(tradeoffs):
                        p = f"policy.tradeoffs[{i}]"
                        if not isinstance(t, dict):
                            err(f"{p} 必须为 object")
                            continue
                        when = t.get("when")
                        if isinstance(when, dict):
                            require(when, "dimension_a", f"{p}.when", non_empty_str)
                            require(when, "dimension_b", f"{p}.when", non_empty_str)
                        else:
                            require(t, "when", p, non_empty_str)
                        require(t, "prefer", p, non_empty_str)
                        require(t, "rationale", p, non_empty_str)
                        if "tolerance" in t:
                            require(t, "tolerance", p, unit_number)
                        check_source_refs(t.get("source_refs"), f"{p}.source_refs", doc_ids)
            rules = policy.get("decision_rules")
            if rules is not None:
                if not isinstance(rules, list):
                    err("policy.decision_rules 必须为 array")
                else:
                    for i, r in enumerate(rules):
                        p = f"policy.decision_rules[{i}]"
                        if not isinstance(r, dict):
                            err(f"{p} 必须为 object")
                            continue
                        require(r, "condition", p, non_empty_str)
                        act = r.get("action")
                        if act not in POLICY_ACTIONS:
                            err(f"{p}.action 必须为 {sorted(POLICY_ACTIONS)} 之一，实际为 {act!r}")
                        if "priority" in r:
                            require(r, "priority", p, unit_number)
            exceptions = policy.get("exceptions")
            if exceptions is not None:
                if not isinstance(exceptions, list):
                    err("policy.exceptions 必须为 array")
                else:
                    for i, e in enumerate(exceptions):
                        p = f"policy.exceptions[{i}]"
                        if not isinstance(e, dict):
                            err(f"{p} 必须为 object")
                            continue
                        require(e, "context", p, non_empty_str)
                        require(e, "override", p)
            rt = policy.get("risk_tolerance")
            if rt is not None:
                if not isinstance(rt, dict):
                    err("policy.risk_tolerance 必须为 object")
                else:
                    for axis in ("novelty", "ambiguity"):
                        node = rt.get(axis)
                        if node is None:
                            continue
                        if not isinstance(node, dict):
                            err(f"policy.risk_tolerance.{axis} 必须为 object")
                            continue
                        if "value" in node:
                            require(node, "value", f"policy.risk_tolerance.{axis}", unit_number)

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
        # V3：评价器与生成器解耦
        if revision.get("rejudge_isolation") is False and mode != "quick":
            err("V3 revision.rejudge_isolation=false（full 模式）：re-judge 不隔离会引入 Evaluator Leakage——Judge B 不得看 Critique 摘要/预期改善/修订 diff")
        if "marginal_gain_threshold" in revision:
            require(revision, "marginal_gain_threshold", "revision", unit_number)
        # V4：修订收敛条件
        sc = revision.get("stop_conditions")
        if (not isinstance(sc, list) or not sc) and "marginal_gain_threshold" not in revision:
            warn("V4 revision 缺 stop_conditions 且缺 marginal_gain_threshold：修订只有轮数上限、无收益收敛条件——容易把轮数预算烧完在递减收益上")

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

    # --- learning（v3.1/v3.2）---
    learning = ir.get("learning")
    if learning is not None:
        if not isinstance(learning, dict):
            err("learning 必须为 object")
        else:
            flog = learning.get("feedback_log")
            if flog is not None:
                if not isinstance(flog, list):
                    err("learning.feedback_log 必须为 array")
                else:
                    for i, fb in enumerate(flog):
                        p = f"learning.feedback_log[{i}]"
                        if not isinstance(fb, dict):
                            err(f"{p} 必须为 object")
                            continue
                        require(fb, "feedback", p, non_empty_str)
                        require(fb, "parsed", p, non_empty_str)
            deltas = learning.get("capability_deltas")
            if deltas is not None:
                if not isinstance(deltas, list):
                    err("learning.capability_deltas 必须为 array")
                else:
                    for i, d in enumerate(deltas):
                        p = f"learning.capability_deltas[{i}]"
                        if not isinstance(d, dict):
                            err(f"{p} 必须为 object")
                            continue
                        tgt = d.get("target")
                        if tgt not in DELTA_TARGETS:
                            err(f"{p}.target 必须为 {sorted(DELTA_TARGETS)} 之一，实际为 {tgt!r}")
                        op = d.get("operation")
                        if op not in DELTA_OPERATIONS:
                            err(f"{p}.operation 必须为 {sorted(DELTA_OPERATIONS)} 之一，实际为 {op!r}")
                        require(d, "rationale", p, non_empty_str)
                        ev = d.get("evidence")
                        if not isinstance(ev, list) or not ev:
                            err(f"{p}.evidence 必须为非空数组——无证据的能力变化禁止落盘（Skill Evolution 最小单位的硬约束）")
                        if "magnitude" in d:
                            require(d, "magnitude", p, unit_number)
            proposals = learning.get("mutation_proposals")
            if proposals is not None:
                if not isinstance(proposals, list):
                    err("learning.mutation_proposals 必须为 array")
                else:
                    for i, pr in enumerate(proposals):
                        p = f"learning.mutation_proposals[{i}]"
                        if not isinstance(pr, dict):
                            err(f"{p} 必须为 object")
                            continue
                        require(pr, "version_from", p, non_empty_str)
                        require(pr, "version_to", p, non_empty_str)
                        require(pr, "changes", p)
                        chgs = pr.get("changes")
                        if isinstance(chgs, list):
                            for j, c in enumerate(chgs):
                                cp = f"{p}.changes[{j}]"
                                if not isinstance(c, dict):
                                    err(f"{cp} 必须为 object")
                                    continue
                                require(c, "type", cp, non_empty_str)
                                require(c, "target", cp, non_empty_str)
                        require(pr, "reason", p, non_empty_str)
                        if "status" in pr and pr["status"] not in PROPOSAL_STATUSES:
                            err(f"{p}.status 必须为 {sorted(PROPOSAL_STATUSES)} 之一，实际为 {pr['status']!r}")
            gate = learning.get("upgrade_gate")
            if gate is not None:
                if not isinstance(gate, dict):
                    err("learning.upgrade_gate 必须为 object")
                else:
                    # V6：Learning 必须具备 Regression Gate
                    if gate.get("benchmark_required") is False:
                        err("V6 learning.upgrade_gate.benchmark_required=false：无 Regression Gate 的学习回路会单方向漂移——vNext 必须过 benchmark 对比才允许落盘")
                    if "mutation_threshold" in gate:
                        require(gate, "mutation_threshold", "learning.upgrade_gate", unit_number)

    # --- runtime_roles（v3.1）---
    rroles = ir.get("runtime_roles")
    if rroles is not None:
        if not isinstance(rroles, dict):
            err("runtime_roles 必须为 object")
        else:
            for field, roles in rroles.items():
                if not isinstance(roles, list) or not roles:
                    err(f"runtime_roles.{field} 必须为非空数组")
                    continue
                for r in roles:
                    if r not in RUNTIME_ROLE_ENUM:
                        err(f"runtime_roles.{field} 含非法角色 {r!r}（合法值: {sorted(RUNTIME_ROLE_ENUM)}）")

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
    print("PASS: Creative IR 校验通过，可进入 Pass C4")
    sys.exit(0)


if __name__ == "__main__":
    main()
