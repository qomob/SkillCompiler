#!/usr/bin/env python3
"""Benchmark Runner — Creative Compiler 基准评测引擎（v3.1）

验证唯一 North Star Metric：编译出来的 Skill 到底是不是比原来的 Skill 更会创作。

    Skill Legacy  → N cases ─┐
    Skill v1      → N cases ─┼→ 指标计算 → 版本对比 → Benchmark Report
    Skill v2      → N cases ─┘

用法:
    python3 scripts/benchmark_runner.py \
        --golden-set tests/golden-set.json \
        --runs runs/legacy.json runs/creative_v1.json \
        [--report reports/benchmark.md]

输入:
  golden-set.json —— 基准用例（输入 + 目标 fingerprint + 任务达成标准 + 品类套路参照系）
  run 文件        —— 某版本 skill 跑完全部 case 后的产物记录

指标（全部可离线机器计算，不依赖运行时 LLM）:
  task_fit_rate        任务达成率（golden-set task_fit_criteria 逐条核对）
  style_fidelity       1 - fingerprint 距离（选中的候选 vs 目标 fingerprint）
  anti_pattern_rate    反模式命中率（命中的候选占比）
  diversity            候选间最小 fingerprint 距离（发散是否真发散）
  novelty              1 - 品类套路簇命中率（命中同一套路簇 = 文字不同也算不新）
  revision_gain        独立评价口径的修订增益（post - pre，Judge B 评分）
  model_preference     L4 模型偏好胜率（跨版本 pairwise 的胜场占比）

注意:
  - revision_gain 只统计 independent_pre/post_score 字段。若 run 文件记录的是
    自评分数（Generator/Judge A 自己打分），本工具会拒绝计算并给出警告——
    Evaluator Leakage 下的 gain 是自证循环（见 references/creative-runtime.md §4）。
  - case 数 < 20 时输出样本量警告：结论置信度低。

退出码: 0=成功 1=输入非法 2=文件/用法错误
"""
import json
import sys
from pathlib import Path

FP_KEYS = ["sentence_length", "sentence_variance", "abstraction", "concreteness", "metaphor_density",
           "emotional_explicitness", "narrative_density", "rhetorical_density", "repetition",
           "whitespace", "commercial_explicitness", "ai_pattern_risk"]
MIN_CASES = 20


def load_json(path, what):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: 无法读取{what}: {path}: {e}", file=sys.stderr)
        sys.exit(2)


def fp_distance(a, b):
    keys = [k for k in FP_KEYS if k in a and k in b]
    if not keys:
        return None
    return sum(abs(a[k] - b[k]) for k in keys) / len(keys)


def norm_text(s):
    return "".join(ch for ch in s if ch.isalnum())


def convention_hit_rate(text, conventions):
    """品类套路命中率：候选文本命中套路信号的比例。"""
    if not conventions:
        return None
    t = norm_text(text)
    hits = sum(1 for c in conventions if norm_text(c) and norm_text(c) in t)
    return hits / len(conventions)


def mean(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    return sum(vals) / len(vals) if vals else None


def evaluate_run(run, golden):
    """计算单版本指标。返回 (metrics dict, warnings list)。"""
    warnings = []
    cases = {c["id"]: c for c in golden.get("cases", [])}
    target_fp = golden.get("target_fingerprint")

    task_fit_met, task_fit_total = 0, 0
    fidelity_vals, anti_hits, anti_total = [], 0, 0
    diversity_vals, novelty_vals = [], []
    gain_vals, pref_wins, pref_total = [], 0, 0

    for r in run.get("results", []):
        cid = r.get("case_id")
        case = cases.get(cid)
        if case is None:
            warnings.append(f"run 含 golden-set 不存在的 case: {cid}")
            continue
        candidates = r.get("candidates", [])

        # task fit
        tf = r.get("task_fit")
        criteria = case.get("task_fit_criteria", [])
        if isinstance(tf, dict) and criteria:
            for c in criteria:
                task_fit_total += 1
                if tf.get(c) is True:
                    task_fit_met += 1

        # anti-pattern / diversity / novelty / style fidelity
        selected_id = r.get("selected")
        fps = [c.get("fingerprint") for c in candidates if isinstance(c.get("fingerprint"), dict)]
        for c in candidates:
            anti_total += 1
            if c.get("anti_pattern_hits"):
                anti_hits += 1
        if len(fps) >= 2:
            min_d = min(fp_distance(fps[i], fps[j])
                        for i in range(len(fps)) for j in range(i + 1, len(fps)))
            if min_d is not None:
                diversity_vals.append(min_d)
        sel = next((c for c in candidates if c.get("id") == selected_id), None)
        if sel is None and candidates:
            sel = candidates[0]
            warnings.append(f"case {cid}: 未标记 selected，取第一个候选")
        if sel:
            if target_fp and isinstance(sel.get("fingerprint"), dict):
                d = fp_distance(sel["fingerprint"], target_fp)
                if d is not None:
                    fidelity_vals.append(1 - d)
            conv = case.get("category_conventions") or golden.get("category_conventions")
            hr = convention_hit_rate(sel.get("text", ""), conv)
            if hr is not None:
                novelty_vals.append(1 - hr)

        # revision gain（独立口径校验）
        for c in candidates:
            pre, post = c.get("independent_pre_score"), c.get("independent_post_score")
            if pre is None and post is None:
                continue
            if pre is None or post is None:
                warnings.append(f"case {cid} candidate {c.get('id')}: independent_pre/post_score 必须成对出现")
                continue
            gain_vals.append(post - pre)

        # model preference（跨版本 pairwise 胜负，由运行时记录）
        pw = r.get("pairwise_vs_baseline")
        if isinstance(pw, dict) and pw.get("total"):
            pref_total += pw["total"]
            pref_wins += pw.get("wins", 0)
        elif sel is not None:
            w, t = sel.get("pairwise_wins"), sel.get("pairwise_total")
            if isinstance(w, int) and isinstance(t, int) and t > 0:
                pref_total += t
                pref_wins += w

    def rate(n, d):
        return round(n / d, 3) if d else None

    def r3(v):
        return round(v, 3) if isinstance(v, float) else v

    metrics = {
        "cases": len(run.get("results", [])),
        "task_fit_rate": rate(task_fit_met, task_fit_total),
        "style_fidelity": r3(mean(fidelity_vals)),
        "anti_pattern_rate": rate(anti_hits, anti_total),
        "diversity": r3(mean(diversity_vals)),
        "novelty": r3(mean(novelty_vals)),
        "revision_gain": r3(mean(gain_vals)),
        "model_preference_win_rate": rate(pref_wins, pref_total),
    }
    if gain_vals and "self_pre_score" in json.dumps(run):
        warnings.append("检测到 self_pre/self_post_score 字段——自评口径的 revision_gain 是 Evaluator Leakage，本报告只采信 independent_* 字段")
    return metrics, warnings


def fmt(v):
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:+.3f}" if v < 0 else f"{v:.3f}"
    return str(v)


def render_report(golden, runs_metrics, warnings):
    lines = []
    lines.append(f"# Benchmark Report — {golden.get('skill_name', 'unnamed-skill')}")
    lines.append("")
    lines.append("North Star Metric：编译出来的 Skill 是否比原来的 Skill 更会创作。")
    lines.append("")
    metric_keys = ["cases", "task_fit_rate", "style_fidelity", "anti_pattern_rate", "diversity",
                   "novelty", "revision_gain", "model_preference_win_rate"]
    header = "| 指标 | " + " | ".join(m["version"] for m in runs_metrics) + " |"
    sep = "|------|" + "|".join(["------"] * len(runs_metrics)) + "|"
    lines.append(header)
    lines.append(sep)
    for k in metric_keys:
        label = k + (" (↓好)" if k == "anti_pattern_rate" else "")
        lines.append(f"| {label} | " + " | ".join(fmt(m[k]) for m in runs_metrics) + " |")
    lines.append("")
    baseline = runs_metrics[0]
    if len(runs_metrics) > 1:
        lines.append("## 相对基线的增量（基线 = 第一个 run）")
        lines.append("")
        lines.append("| 指标 | " + " | ".join(m["version"] for m in runs_metrics[1:]) + " |")
        lines.append("|------|" + "|".join(["------"] * (len(runs_metrics) - 1)) + "|")
        for k in metric_keys[1:]:
            row = []
            for m in runs_metrics[1:]:
                b, v = baseline[k], m[k]
                row.append("n/a" if b is None or v is None else f"{v - b:+.3f}")
            lines.append(f"| {k} Δ | " + " | ".join(row) + " |")
        lines.append("")
    if warnings:
        lines.append("## 警告")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")
    lines.append("## 判读")
    lines.append("")
    lines.append("- style_fidelity / novelty / revision_gain 显著提升且 anti_pattern_rate 下降 → Creative Compiler 成立")
    lines.append("- 各版本差距 < 0.05 → 架构漂亮但创造能力增量不足，优化方向应回到 C2/C3 而非继续加字段")
    lines.append("- revision_gain 计算必须来自独立评价器（Judge B），自评口径一律不采信")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    if "--golden-set" not in args or "--runs" not in args:
        print("用法: python3 scripts/benchmark_runner.py --golden-set <golden-set.json> "
              "--runs <run1.json> [<run2.json> ...] [--report <report.md>]", file=sys.stderr)
        sys.exit(2)

    gs_path = args[args.index("--golden-set") + 1]
    runs_paths = []
    i = args.index("--runs") + 1
    while i < len(args) and not args[i].startswith("--"):
        runs_paths.append(args[i])
        i += 1
    report_path = None
    if "--report" in args:
        report_path = args[args.index("--report") + 1]

    golden = load_json(gs_path, "golden-set")
    if not golden.get("cases"):
        print("ERROR: golden-set.json 缺少 cases", file=sys.stderr)
        sys.exit(1)

    all_warnings = []
    if len(golden["cases"]) < MIN_CASES:
        all_warnings.append(f"golden-set 仅 {len(golden['cases'])} cases（建议 ≥{MIN_CASES}）——样本量不足，结论置信度低")

    runs_metrics = []
    for p in runs_paths:
        run = load_json(p, "run 文件")
        version = run.get("version", Path(p).stem)
        metrics, warns = evaluate_run(run, golden)
        runs_metrics.append({"version": version, **metrics})
        for w in warns:
            all_warnings.append(f"[{version}] {w}")

    report = render_report(golden, runs_metrics, all_warnings)
    if report_path:
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        Path(report_path).write_text(report, encoding="utf-8")
        print(f"OK: Benchmark report 已写入 {report_path}")
    else:
        print(report)
    sys.exit(0)


if __name__ == "__main__":
    main()
