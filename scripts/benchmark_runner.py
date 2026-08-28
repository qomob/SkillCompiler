#!/usr/bin/env python3
"""Benchmark Runner — Creative Compiler 的 North Star 度量工具（v3.2）。

回答唯一一个问题：
    "同一任务，多版本（原 Prompt / Legacy Skill / Creative v3.0 / Creative v3.1+）产出对比，
     更新版本是否显著更好？"

本脚本是构建时分析器，不执行任何 LLM 调用、不运行被测 skill——它**消费已经生成的输出**：

    tests/benchmark-cases.json（C4 产出，机器可读 Golden Set）
    + N 个版本的输出目录（每 case 一个 {case_id}.md；--variants label=dir 可重复）
    + creative-ir.json（目标 fingerprint + anti_patterns，作为评判 oracle）
      ↓
    per-case: 实测指纹 → style_fidelity / anti_pattern 命中 / golden 期望核对 / category_novelty
      ↓
    benchmark-report.json + stdout 对比矩阵 + capability_gain 汇总

North Star 指标：
    Creative Capability Gain = 最新版本表现 - 基线（首版本）表现
    （不是"最新版本自评多少分"）

用法:
  python3 scripts/benchmark_runner.py --cases tests/benchmark-cases.json \
      --variants legacy=results/legacy/ v30=results/v30/ v31=results/v31/ \
      --ir creative-ir.json [--category xiaohongshu] [--report benchmark-report.json]
  # 兼容旧双版本 CLI：--baseline dir --candidate dir
退出码: 0=正常产出报告 2=用法/文件错误（指标好坏不改变退出码，由人决策）
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from style_analyzer import analyze_text, normalize, fingerprint_distance  # noqa: E402

try:
    from novelty_detector import category_novelty as _cat_novelty, load_patterns  # noqa: E402
except Exception:  # novelty 集成为可选能力，缺失不阻塞
    _cat_novelty = None
    load_patterns = None

TOOL_NAME = "benchmark-runner"
TOOL_VERSION = "1.1.0"


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: 无法读取 {path}: {e}", file=sys.stderr)
        sys.exit(2)


def read_output(out_dir, case_id):
    for ext in (".md", ".txt", ".json"):
        p = os.path.join(out_dir, case_id + ext)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return f.read()
    return None


def check_expected(expected, output, fp):
    """核对单条 case 的期望特征。返回 (passed, failed)。
    支持（v3.2 对齐评审 §46）: fingerprint 方向断言 / should_contain_any / must_not_contain /
    qualities（应含特征关键词）/ constraints（禁用词，同 must_not_contain）。"""
    passed, failed = [], []
    exp_fp = expected.get("fingerprint", {})
    for dim, rule in exp_fp.items():
        val = fp.get(dim)
        if val is None:
            failed.append(f"fingerprint.{dim}: 产物指纹缺失该维度")
            continue
        ok, op = False, str(rule).strip()
        try:
            if op.startswith(">="):
                ok = val >= float(op[2:])
            elif op.startswith("<="):
                ok = val <= float(op[2:])
            elif op.startswith(">"):
                ok = val > float(op[1:])
            elif op.startswith("<"):
                ok = val < float(op[1:])
            elif op in ("high", "高"):
                ok = val >= 0.6
            elif op in ("low", "低"):
                ok = val <= 0.4
        except ValueError:
            ok = False
        (passed if ok else failed).append(f"fingerprint.{dim} {rule} (实测 {val})")

    for kw in expected.get("should_contain_any", []):
        (passed if kw in output else failed).append(f"应含任一标记: {kw!r}")
    for kw in expected.get("qualities", []):
        (passed if kw in output else failed).append(f"质量特征应出现: {kw!r}")
    banned = list(expected.get("must_not_contain", [])) + list(expected.get("constraints", []))
    for kw in banned:
        (passed if kw not in output else failed).append(f"约束禁用词未出现: {kw!r}")
    return passed, failed


def eval_version(cases, out_dir, target_fp, anti_patterns, label, patterns=None):
    """评估一个版本在全部 case 上的表现。"""
    results = []
    fidelity_sum, anti_hit, golden_pass, novelty_sum, novelty_n, evaluated, missing = 0.0, 0, 0, 0.0, 0, 0, 0
    for case in cases:
        cid = case["id"]
        output = read_output(out_dir, cid)
        if output is None:
            missing += 1
            results.append({"id": cid, "status": "missing_output"})
            continue
        raw = analyze_text(output)
        fp = {k: round(v, 3) for k, v in normalize(raw).items()}
        dist = fingerprint_distance(fp, target_fp) if target_fp else None
        fidelity = round(1 - dist, 4) if dist is not None else None

        signals = []
        for ap in anti_patterns:
            for sig in ap.get("detection_signals", []):
                if sig and sig in output:
                    signals.append({"anti_pattern": ap.get("id", "?"), "signal": sig,
                                    "severity": ap.get("severity", "medium")})

        cat_nov = None
        if patterns is not None and _cat_novelty is not None:
            cat_nov = round(_cat_novelty(output, patterns)[0], 4)

        passed, failed = check_expected(case.get("expected", {}), output, fp)
        golden_ok = not failed
        evaluated += 1
        if fidelity is not None:
            fidelity_sum += fidelity
        if signals:
            anti_hit += 1
        if golden_ok:
            golden_pass += 1
        if cat_nov is not None:
            novelty_sum += cat_nov
            novelty_n += 1
        results.append({
            "id": cid, "status": "ok",
            "style_fidelity": fidelity,
            "category_novelty": cat_nov,
            "anti_pattern_hits": signals,
            "golden": {"pass": golden_ok, "passed": passed, "failed": failed},
            "ai_pattern_risk": fp.get("ai_pattern_risk"),
        })

    summary = {
        "label": label,
        "cases_total": len(cases),
        "cases_evaluated": evaluated,
        "cases_missing_output": missing,
        "style_fidelity_avg": round(fidelity_sum / evaluated, 4) if evaluated else None,
        "anti_pattern_rate": round(anti_hit / evaluated, 4) if evaluated else None,
        "golden_pass_rate": round(golden_pass / evaluated, 4) if evaluated else None,
        "category_novelty_avg": round(novelty_sum / novelty_n, 4) if novelty_n else None,
        "cases": results,
    }
    return summary


def capability_gain(baseline, latest):
    """Creative Capability Gain（North Star）：正向指标均值差。
    style_fidelity / golden_pass_rate 越高越好，anti_pattern_rate 越低越好。"""
    parts = {}
    for m, sign in (("style_fidelity_avg", 1), ("golden_pass_rate", 1), ("anti_pattern_rate", -1)):
        b, c = baseline.get(m), latest.get(m)
        if b is None or c is None:
            continue
        parts[m] = round(sign * (c - b), 4)
    if not parts:
        return None
    return round(sum(parts.values()) / len(parts), 4)


def main():
    ap = argparse.ArgumentParser(description="Creative Compiler Benchmark Runner (multi-variant)")
    ap.add_argument("--cases", required=True, help="benchmark-cases.json（机器可读 Golden Set）")
    ap.add_argument("--baseline", help="（旧 CLI）baseline 输出目录")
    ap.add_argument("--candidate", help="（旧 CLI）candidate 输出目录")
    ap.add_argument("--variants", nargs="+", action="append", metavar="LABEL=DIR",
                    help="多版本：--variants legacy=results/legacy/ v30=results/v30/（= 两侧为版本标签与输出目录，"
                         "可重复 --variants 或在同一 flag 后空格分隔多个 label=dir；第一个为基线）")
    ap.add_argument("--ir", required=True, help="Creative IR JSON（target fingerprint + anti_patterns oracle）")
    ap.add_argument("--category", help="品类名（可选）：提供则计算 category_novelty（见 category_patterns.json）")
    ap.add_argument("--report", help="报告写入该 JSON 文件（缺省打印 stdout）")
    args = ap.parse_args()

    spec = load_json(args.cases)
    cases = spec.get("cases")
    if not isinstance(cases, list) or not cases:
        print("ERROR: cases 文件须含非空 cases 数组", file=sys.stderr)
        sys.exit(2)
    ir = load_json(args.ir)
    target_fp = (ir.get("style") or {}).get("fingerprint")
    anti_patterns = ir.get("anti_patterns") or []

    # 版本布局：--variants 优先；否则由 --baseline/--candidate 组装；至少 2 版
    def parse_variant_token(tok):
        """支持 'label=dir'（文档契约）；纯目录时从路径名派生标签（容错）。"""
        if "=" in tok:
            label, d = tok.split("=", 1)
            return label.strip(), d.strip()
        return os.path.basename(os.path.normpath(tok)) or tok, tok

    variants = []
    if args.variants:
        for group in args.variants:
            variants.extend(parse_variant_token(tok) for tok in group)
    else:
        if args.baseline:
            variants.append(("baseline", args.baseline))
        if args.candidate:
            variants.append(("candidate", args.candidate))
    if len(variants) < 2:
        print("ERROR: 至少提供两个版本（--variants label=dir 可重复，或 --baseline + --candidate）",
              file=sys.stderr)
        sys.exit(2)

    patterns = None
    if args.category:
        if load_patterns is None:
            print("WARN: novelty_detector 不可用，跳过 category_novelty", file=sys.stderr)
        else:
            patterns = load_patterns(args.category)

    versions = [eval_version(cases, d, target_fp, anti_patterns, label, patterns)
                for label, d in variants]

    baseline_v, latest_v = versions[0], versions[-1]
    metrics = ["style_fidelity_avg", "anti_pattern_rate", "golden_pass_rate", "category_novelty_avg"]
    better_when_lower = {"anti_pattern_rate"}

    def delta(b, c):
        if b is None or c is None:
            return None
        return round(c - b, 4)

    comparison = {}
    for m in metrics:
        comparison[m] = {"baseline": baseline_v[m], "latest": latest_v[m], "delta": delta(baseline_v[m], latest_v[m])}
        if m in better_when_lower:
            comparison[m]["better_when"] = "lower"
    # 其余中间版本相对基线的 delta（四组对比矩阵）
    matrix = {v["label"]: {m: v[m] for m in metrics} for v in versions}

    wins = sum(1 for m, v in comparison.items()
               if v["delta"] is not None and (
                   (v.get("better_when") == "lower" and v["delta"] < 0) or
                   ("better_when" not in v and v["delta"] > 0)))

    report = {
        "benchmark": spec.get("benchmark", "unnamed"),
        "tool": f"{TOOL_NAME} v{TOOL_VERSION}",
        "north_star_question": "更新版本的编译产物是否比基线更会创作？",
        "variants": [v["label"] for v in versions],
        "baseline_label": baseline_v["label"],
        "latest_label": latest_v["label"],
        "comparison_baseline_vs_latest": comparison,
        "capability_gain": capability_gain(baseline_v, latest_v),
        "variant_matrix": matrix,
        "candidate_metric_wins": f"{wins}/{len(comparison)}",
        "note": ("指标由词表启发式与 golden 断言计算；LLM preference 与 human preference 不在 "
                 "本工具范围（四组对比中 Human Reference 组需另行采集，见 creative-compiler.md "
                 "§Benchmark 四组协议）。是否'显著更好'由人结合 delta 规模与样本量决策。"),
        "versions_detail": versions,
    }

    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)

    print("\n===== Benchmark Matrix（各版本指标）=====", file=sys.stderr)
    header = f"{'variant':<14}" + "".join(f"{m.split('_')[0][:9]:>12}" for m in metrics)
    print(header, file=sys.stderr)
    for v in versions:
        row = f"{v['label']:<14}"
        for m in metrics:
            val = v[m]
            row += f"{('-' if val is None else f'{val:.3f}'):>12}"
        print(row, file=sys.stderr)
    print(f"\ncapability_gain ({latest_v['label']} vs {baseline_v['label']}): {report['capability_gain']}",
          file=sys.stderr)
    print(f"metric wins: {report['candidate_metric_wins']}", file=sys.stderr)


if __name__ == "__main__":
    main()
