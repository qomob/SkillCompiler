#!/usr/bin/env python3
"""Novelty Detector — 三参照系新颖度检测（Creative Compiler v3.2 可执行能力层）。

解决的问题：v3.1 把 Originality 拆为 Diversity + Novelty，但 Novelty 的第一参照系
（品类套路簇）此前只存在于文档定义。本脚本使其可执行：

    Novelty = Candidate Novelty（内部候选空间：本产物 vs 同批其他候选）
            + Category Novelty（品类常见表达：vs category_patterns 套路簇）
            + Corpus Novelty（历史案例：vs 源语料实测指纹）

输出四值：
    {"candidate_novelty": 0.78, "category_novelty": 0.41,
     "corpus_novelty": 0.66, "overall_novelty": 0.61}

权重默认 candidate 0.3 / category 0.5 / corpus 0.2（缺哪个分量则剩余权重重归一）。

诚实边界：
  - category_patterns 是启发式词表，检测的是"结构套路命中密度"，不是语义原创性——
    它能抓住"没抄任何一句但整体很套路"，抓不住"换了新说法的旧逻辑"。
  - corpus_novelty 用指纹距离近似内容距离（指纹近≠内容近，指纹只覆盖风格形式层）。

用法:
  python3 scripts/novelty_detector.py --target out.md --category xiaohongshu \
      [--peers peer1.md peer2.md ...] [--corpus corpus1.md corpus2.md ...] [--json out.json]
退出码: 0=正常 2=用法/文件错误
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from style_analyzer import analyze_text, normalize, fingerprint_distance, ALL_DIMS  # noqa: E402

TOOL_NAME = "novelty-detector"
TOOL_VERSION = "1.0.0"
PATTERNS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "category_patterns.json")

# 默认权重：品类套路是 Novelty 最直接的证据，权重最高
W_CANDIDATE, W_CATEGORY, W_CORPUS = 0.3, 0.5, 0.2


def load_patterns(category):
    try:
        with open(PATTERNS_PATH, encoding="utf-8") as f:
            lib = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: 无法读取品类套路库 {PATTERNS_PATH}: {e}", file=sys.stderr)
        sys.exit(2)
    if category not in lib:
        print(f"ERROR: 品类 {category!r} 不在套路库中。可用: {sorted(k for k in lib if not k.startswith('_'))}",
              file=sys.stderr)
        sys.exit(2)
    return lib[category]


def read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        print(f"ERROR: 无法读取文件 {path}: {e}", file=sys.stderr)
        sys.exit(2)


def fp_of(text):
    return {k: round(v, 3) for k, v in normalize(analyze_text(text)).items()}


def category_novelty(text, patterns):
    """1 - 品类套路命中密度（每千字命中数 / 8 归一）。"""
    n_chars = max(len(text), 1)
    hits = 0
    hit_detail = {}
    for group, words in patterns.items():
        g = sum(text.count(w) for w in words)
        if g:
            hit_detail[group] = g
        hits += g
    density_per_1000 = hits * 1000.0 / n_chars
    novelty = max(0.0, 1.0 - density_per_1000 / 8.0)
    return novelty, density_per_1000, hit_detail


def main():
    ap = argparse.ArgumentParser(description="Novelty Detector: 3-reference-space novelty scoring")
    ap.add_argument("--target", required=True, help="被检测的产物文件")
    ap.add_argument("--category", required=True, help="品类名（见 category_patterns.json）")
    ap.add_argument("--peers", nargs="*", default=[], help="同批其他候选文件（candidate novelty 参照）")
    ap.add_argument("--corpus", nargs="*", default=[], help="源语料文件（corpus novelty 参照）")
    ap.add_argument("--json", dest="out", help="结果写入该 JSON 文件（缺省打印 stdout）")
    args = ap.parse_args()

    patterns = load_patterns(args.category)
    target_text = read_text(args.target)
    target_fp = fp_of(target_text)

    result = {"tool": f"{TOOL_NAME} v{TOOL_VERSION}", "target": args.target, "category": args.category}
    weights, scores = [], []

    # ① candidate novelty：与同批候选的平均指纹距离（彼此越不同越新颖）
    if args.peers:
        peer_fps = [fp_of(read_text(p)) for p in args.peers]
        dists = [fingerprint_distance(target_fp, p) for p in peer_fps]
        dists = [d for d in dists if d is not None]
        if dists:
            result["candidate_novelty"] = round(sum(dists) / len(dists), 4)
            scores.append(result["candidate_novelty"])
            weights.append(W_CANDIDATE)

    # ② category novelty：1 - 品类套路命中密度
    cat_nov, density, detail = category_novelty(target_text, patterns)
    result["category_novelty"] = round(cat_nov, 4)
    result["_category_pattern_hits_per_1000"] = round(density, 2)
    result["_category_pattern_hit_groups"] = detail
    scores.append(cat_nov)
    weights.append(W_CATEGORY)

    # ③ corpus novelty：与源语料实测指纹的距离（防止高级复述）
    if args.corpus:
        # 多文件聚合必须均匀平均——逐对 (prev+next)/2 会让后读的文件权重翻倍（3 篇时 1/4、1/4、1/2）
        corpus_raws = [analyze_text(read_text(c)) for c in args.corpus]
        raw = {}
        for k in corpus_raws[0]:
            vals = [r[k] for r in corpus_raws]
            if isinstance(vals[0], dict):
                raw[k] = {kk: sum(v[kk] for v in vals) / len(vals) for kk in vals[0]}
            elif isinstance(vals[0], (int, float)):
                raw[k] = sum(vals) / len(vals)
            else:
                raw[k] = vals[0]
        corpus_fp = {k: round(v, 3) for k, v in normalize(raw).items()}
        d = fingerprint_distance(target_fp, corpus_fp)
        if d is not None:
            result["corpus_novelty"] = d
            scores.append(d)
            weights.append(W_CORPUS)

    total_w = sum(weights)
    result["overall_novelty"] = round(sum(s * w for s, w in zip(scores, weights)) / total_w, 4) if total_w else None
    result["weights_applied"] = {"candidate": W_CANDIDATE, "category": W_CATEGORY, "corpus": W_CORPUS}
    result["note"] = ("category_novelty 为词表启发式（测结构套路命中，非语义原创）；"
                      "corpus_novelty 为风格形式距离近似。Diversity（候选间差异）是另一指标，勿混用。")

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        print(f"OK: novelty 报告已写入 {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
