#!/usr/bin/env python3
"""Style Analyzer — 语料 → 实测 Style Fingerprint（Creative Compiler v3.1 可执行能力层）。

解决的问题：v3.0 规定 "Style Fingerprint 禁止凭印象填写"，但没有提供"怎么不拍脑袋"的工具。
本脚本把 fingerprint 从 Schema-level claim 变成 Executable measurement：

    Corpus → 原始测量（raw measurements）→ 归一化 → 12 维 Fingerprint + 溯源

产物四部分（v3.2）：
  1. raw_measurements — 句长分布/词频比/修辞标记等原始统计（可人工复核）
  2. fingerprint — 轻量数值向量（Runtime 消费，12 维 0-1）
  3. measurements — 逐维测量证据 value + sample_size + confidence + measurement
     （裸数字不可验证；证据对象才能支撑 Style Drift / Benchmark / Regression）
  4. fingerprint_provenance + style_confidence — 测量溯源与整体置信度

Weighted Style Distance（v3.2）：
    Σ(|feature_distance| × feature_confidence) / Σ(feature_confidence)
    样本不足/证据缺失的维度自动降权；无 measurements 时退化为等权平均。

诚实边界（必读）：
  - 词表匹配是启发式测量，不是语义理解。metaphor/emotional 等维度基于显式语言标记，
    会低估不使用标记词的隐喻/克制表达。所有维度输出均带 method=heuristic 标注。
  - 英文语料支持基础统计（句长/问句/重复），词表维度以中文为主。
  - 语料 < 3 篇完整作品时输出 corpus_sufficient=false，调用方（C2）应降 confidence。

用法:
  python3 scripts/style_analyzer.py <corpus_file> [corpus_file ...] [--json out.json]
  python3 scripts/style_analyzer.py --compare fingerprint_a.json fingerprint_b.json
退出码: 0=正常 2=用法/文件错误
"""
import argparse
import datetime
import json
import math
import re
import sys

TOOL_NAME = "style-analyzer"
TOOL_VERSION = "1.1.0"

# 12 维 fingerprint 中必填的 6 项核心指标（与 validate_creative_ir.py 对齐）
CORE_DIMS = ["sentence_length", "abstraction", "concreteness",
             "emotional_explicitness", "narrative_density", "ai_pattern_risk"]
ALL_DIMS = CORE_DIMS + ["sentence_variance", "metaphor_density", "rhetorical_density",
                        "repetition", "whitespace", "commercial_explicitness"]

# v3.2：逐维测量方法名（写入 measurements[].measurement，可审计）
MEASUREMENT_METHODS = {
    "sentence_length": "mean-sentence-length/30",
    "sentence_variance": "sentence-length-cv/0.6",
    "abstraction": "abstract-suffix-ratio-per-100/12",
    "concreteness": "concrete-marker-ratio-per-100/15",
    "metaphor_density": "metaphor-mark-ratio-per-100/4",
    "emotional_explicitness": "emotion-word-ratio-per-100/5",
    "narrative_density": "narrative-mark-ratio-per-100/3",
    "rhetorical_density": "question-ratio/0.35",
    "repetition": "repeated-trigram-ratio/0.08",
    "whitespace": "short-para-ratio+blank-line-rate",
    "commercial_explicitness": "commercial-word-ratio-per-100/3",
    "ai_pattern_risk": "ai-phrase-hits-per-1000/8",
}
# v3.2：词表标记类维度——命中为 0 时无法区分"真没有"与"不用标记词"，置信度上限压低
LEXICON_ZERO_CAP_DIMS = {"metaphor_density", "emotional_explicitness", "narrative_density",
                         "commercial_explicitness"}

# ---- 启发式词表（中文为主；维度均为显式标记匹配，非语义判断） ----

ABSTRACT_SUFFIX = ("性", "化", "度", "感", "主义", "能力", "思维", "价值", "意义", "精神",
                   "状态", "关系", "方式", "问题", "概念", "体系", "模式", "逻辑", "力量")
CONCRETE_MARKERS = ("万", "块", "年", "月", "天", "小时", "分钟", "岁", "公里", "斤", "次",
                    "杯", "碗", "间", "楼", "路", "街", "城", "号", "折", "人")
NUM_RE = re.compile(r"\d")
EMOTION_WORDS = ("难过", "开心", "后悔", "崩溃", "害怕", "绝望", "激动", "感动", "愤怒", "委屈",
                 "孤独", "幸福", "心疼", "羞耻", "骄傲", "恐惧", "温暖", "窒息", "痛快", "遗憾",
                 "爱", "恨", "哭", "笑", "泪", "慌")
METAPHOR_MARKS = ("像", "仿佛", "好像", "如同", "好比", "宛如", "简直就是")
NARRATIVE_MARKS = ("那年", "那天", "那时", "后来", "当时", "有一次", "第一次", "去年", "前年",
                   "上周", "昨天", "小时候", "毕业", "入职", "开店", "创业", "回国")
COMMERCIAL_WORDS = ("下单", "购买", "优惠", "链接", "折扣", "秒杀", "拼团", "咨询", "私信",
                    "购买链接", "直播间", "优惠券", "限时", "名额")
AI_PATTERN_PHRASES = ("今天给大家分享", "在这个时代", "让我们一起", "你是否也有", "首先其次",
                      "不仅仅", "越来越多的人", "众所周知", "总的来说", "综上所述", "亲爱的",
                      "宝子们", "干货", "满满", "建议收藏", "码住", "纯干货", "深度好文")
QUESTION_RE = re.compile(r"[?？]")
SENT_SPLIT_RE = re.compile(r"[。！？!?…；;\n]+")
CLAUSE_SPLIT_RE = re.compile(r"[，,、：:]+")


def clamp01(x):
    return max(0.0, min(1.0, x))


def split_sentences(text):
    sents = [s.strip() for s in SENT_SPLIT_RE.split(text) if s.strip()]
    return sents or ([text.strip()] if text.strip() else [])


def count_haystack(haystack, needles):
    return sum(haystack.count(n) for n in needles)


def analyze_text(text):
    """单篇文本的原始测量。"""
    sents = split_sentences(text)
    n_sents = len(sents)
    n_chars = len(re.sub(r"\s", "", text))
    lengths = [len(re.sub(r"\s", "", s)) for s in sents]
    mean_len = sum(lengths) / n_sents if n_sents else 0.0
    variance = (sum((L - mean_len) ** 2 for L in lengths) / n_sents) if n_sents > 1 else 0.0
    cv = (math.sqrt(variance) / mean_len) if mean_len > 0 else 0.0

    n_clauses = len(CLAUSE_SPLIT_RE.split(text))
    # 问号在分句符中被移除，须在原文本上统计
    q_sents = len(re.findall(r"[?？]", text))

    concrete_hits = count_haystack(text, CONCRETE_MARKERS) + len(NUM_RE.findall(text))
    abstract_hits = count_haystack(text, ABSTRACT_SUFFIX)
    first_person_hits = text.count("我")
    emotion_hits = count_haystack(text, EMOTION_WORDS)
    metaphor_hits = count_haystack(text, METAPHOR_MARKS)
    narrative_hits = count_haystack(text, NARRATIVE_MARKS)
    commercial_hits = count_haystack(text, COMMERCIAL_WORDS)
    ai_hits = count_haystack(text, AI_PATTERN_PHRASES)

    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    short_paras = sum(1 for p in paragraphs if len(p.strip()) <= 30)
    blank_lines = len(re.findall(r"\n\s*\n", text))

    # 3-gram 重复率（字级，衡量口头禅/复读结构）
    chars = re.sub(r"\s", "", text)
    ngrams = {}
    for i in range(len(chars) - 2):
        g = chars[i:i + 3]
        if not re.fullmatch(r"[\u4e00-\u9fff]{3}", g):
            continue
        ngrams[g] = ngrams.get(g, 0) + 1
    repeated = sum(c for c in ngrams.values() if c > 1)

    per_100 = lambda hits: (hits * 100.0 / max(n_chars, 1))
    return {
        "sentence_count": n_sents,
        "char_count": n_chars,
        "clause_count": n_clauses,
        "sentence_length": {"mean": round(mean_len, 2),
                            "median": sorted(lengths)[n_sents // 2] if lengths else 0,
                            "variance": round(variance, 2),
                            "cv": round(cv, 3)},
        "question_ratio": round(q_sents / n_sents, 3) if n_sents else 0.0,
        "first_person_per_100": round(per_100(first_person_hits), 2),
        "concrete_per_100": round(per_100(concrete_hits), 2),
        "abstract_per_100": round(per_100(abstract_hits), 2),
        "emotion_per_100": round(per_100(emotion_hits), 2),
        "metaphor_per_100": round(per_100(metaphor_hits), 2),
        "narrative_per_100": round(per_100(narrative_hits), 2),
        "commercial_per_100": round(per_100(commercial_hits), 2),
        "ai_pattern_hits": ai_hits,
        "ai_pattern_per_1000": round(ai_hits * 1000.0 / max(n_chars, 1), 2),
        "repeated_trigram_ratio": round(repeated / max(len(ngrams), 1), 3),
        "short_paragraph_ratio": round(short_paras / len(paragraphs), 3) if paragraphs else 0.0,
        "blank_line_per_100": round(blank_lines * 100.0 / max(n_chars, 1), 2),
    }


def normalize(raw):
    """raw measurements → 12 维 0-1 fingerprint。归一化锚点见各维度注释（启发式标定）。"""
    sl = raw["sentence_length"]
    total_conc = raw["concrete_per_100"] + raw["abstract_per_100"]
    return {
        # 平均句长：10字≈0.33 / 30字≈1.0 锚点
        "sentence_length": clamp01(sl["mean"] / 30.0),
        # 变异系数：CV 0.6≈参差充分（大量写作实测落在0.4-0.9）
        "sentence_variance": clamp01(sl["cv"] / 0.6),
        "abstraction": clamp01(raw["abstract_per_100"] / 12.0),
        "concreteness": clamp01(raw["concrete_per_100"] / 15.0),
        "metaphor_density": clamp01(raw["metaphor_per_100"] / 4.0),
        "emotional_explicitness": clamp01(raw["emotion_per_100"] / 5.0),
        "narrative_density": clamp01(raw["narrative_per_100"] / 3.0),
        "rhetorical_density": clamp01(raw["question_ratio"] / 0.35),
        "repetition": clamp01(raw["repeated_trigram_ratio"] / 0.08),
        "whitespace": clamp01(raw["short_paragraph_ratio"] * 0.5 + min(raw["blank_line_per_100"] / 3.0, 0.5)),
        "commercial_explicitness": clamp01(raw["commercial_per_100"] / 3.0),
        "ai_pattern_risk": clamp01(raw["ai_pattern_per_1000"] / 8.0),
    }


def fingerprint_distance(fp_a, fp_b, conf=None):
    """Weighted Style Distance（v3.2）：Σ(|Δ| × confidence) / Σ(confidence)。
    conf: 可选 {dim: confidence} 映射（来自 measurements）；缺省等权（v3.1 行为）。"""
    dims = [d for d in ALL_DIMS if d in fp_a and d in fp_b]
    if not dims:
        return None
    if conf:
        pairs = [(d, conf.get(d, 1.0)) for d in dims]
        total_w = sum(w for _, w in pairs)
        if total_w > 0:
            return round(sum(abs(fp_a[d] - fp_b[d]) * w for d, w in pairs) / total_w, 4)
    return round(sum(abs(fp_a[d] - fp_b[d]) for d in dims) / len(dims), 4)


def build_measurements(fp, avg, total_chars, n_sents):
    """v3.2：fingerprint → 逐维证据对象（value/sample_size/confidence/measurement）。"""
    zero_hit_dims = {
        "metaphor_density": avg["metaphor_per_100"] <= 0,
        "emotional_explicitness": avg["emotion_per_100"] <= 0,
        "narrative_density": avg["narrative_per_100"] <= 0,
        "commercial_explicitness": avg["commercial_per_100"] <= 0,
    }
    base_conf = clamp01(total_chars / 3000.0)
    sent_dims = {"sentence_length", "sentence_variance", "rhetorical_density"}
    out = {}
    for dim in ALL_DIMS:
        conf = base_conf
        if dim in LEXICON_ZERO_CAP_DIMS and zero_hit_dims.get(dim):
            conf = min(conf, 0.4)  # 无法区分"真没有"与"不用标记词"
        out[dim] = {
            "value": fp[dim],
            "sample_size": round(n_sents, 1) if dim in sent_dims else total_chars,
            "confidence": round(conf, 3),
            "measurement": MEASUREMENT_METHODS[dim],
        }
    return out


def build_report(paths):
    docs = []
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                docs.append(f.read())
        except OSError as e:
            print(f"ERROR: 无法读取语料文件 {p}: {e}", file=sys.stderr)
            sys.exit(2)

    per_doc = [analyze_text(t) for t in docs]
    n = len(per_doc)

    # 汇总测量：多文件取均值（分母统一为 100 字，可直接平均）
    avg = {}
    for k in per_doc[0]:
        vals = [d[k] for d in per_doc]
        if isinstance(vals[0], dict):
            avg[k] = {kk: round(sum(v[kk] for v in vals) / n, 3) for kk in vals[0]}
        elif isinstance(vals[0], (int, float)):
            avg[k] = round(sum(vals) / n, 3)
        else:
            avg[k] = vals[0]

    fp = {k: round(v, 3) for k, v in normalize(avg).items()}
    total_chars = sum(d["char_count"] for d in per_doc)
    avg_sents = round(avg["sentence_count"], 1)
    measurements = build_measurements(fp, avg, total_chars, avg_sents)
    coverage = sum(1 for m in measurements.values() if m["confidence"] > 0) / len(measurements)
    base_conf = clamp01(total_chars / 3000.0)
    style_confidence = {
        "corpus_size": total_chars,
        "feature_coverage": round(coverage, 3),
        "overall_confidence": round(base_conf * (0.5 + 0.5 * coverage), 3),
    }
    return {
        "raw_measurements": {
            "method": "heuristic-lexicon",
            "corpus": [ {"file": p, "sentence_count": d["sentence_count"], "char_count": d["char_count"]}
                        for p, d in zip(paths, per_doc) ],
            "aggregated": avg,
        },
        "fingerprint": fp,
        "measurements": measurements,
        "style_confidence": style_confidence,
        "fingerprint_provenance": {
            "tool": f"{TOOL_NAME} v{TOOL_VERSION}",
            "method": "heuristic-lexicon（词表标记匹配，非语义理解；隐喻/情绪维度会低估不用标记词的表达）",
            "corpus_size": {"documents": n, "total_chars": total_chars},
            "corpus_sufficient": n >= 3 and total_chars >= 1500,
            "measured_at": datetime.datetime.now().isoformat(timespec="seconds"),
        },
    }


def main():
    ap = argparse.ArgumentParser(description="Style Analyzer: corpus → measured 12-dim fingerprint")
    ap.add_argument("corpus", nargs="*", help="语料文件（txt/md，可多个）")
    ap.add_argument("--json", dest="out", help="结果写入该 JSON 文件（缺省打印 stdout）")
    ap.add_argument("--compare", nargs=2, metavar=("FP_A", "FP_B"),
                    help="比较两个 fingerprint JSON，输出 Style Distance")
    args = ap.parse_args()

    if args.compare:
        try:
            with open(args.compare[0], encoding="utf-8") as f:
                a = json.load(f)
            with open(args.compare[1], encoding="utf-8") as f:
                b = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"ERROR: 无法读取 fingerprint 文件: {e}", file=sys.stderr)
            sys.exit(2)
        fp_a = a.get("fingerprint", a)
        fp_b = b.get("fingerprint", b)
        # v3.2：双方均有 measurements 时用 confidence 加权距离（低置信维度降权）
        conf = None
        ma, mb = a.get("measurements"), b.get("measurements")
        if isinstance(ma, dict) and isinstance(mb, dict):
            conf = {d: min(ma[d].get("confidence", 1.0), mb[d].get("confidence", 1.0))
                    for d in ALL_DIMS if d in ma and d in mb}
        dist = fingerprint_distance(fp_a, fp_b, conf)
        print(json.dumps({"style_distance": dist,
                          "style_fidelity": round(1 - dist, 4) if dist is not None else None,
                          "weighting": "confidence-weighted" if conf else "equal-weight"},
                         ensure_ascii=False, indent=2))
        sys.exit(0)

    if not args.corpus:
        print("ERROR: 至少提供一个语料文件，或使用 --compare", file=sys.stderr)
        sys.exit(2)

    report = build_report(args.corpus)
    if not report["fingerprint_provenance"]["corpus_sufficient"]:
        report["fingerprint_provenance"]["warning"] = (
            "语料不足（<3 篇或 <1500 字）：fingerprint 置信度低，C2 应降 meta.confidence 并在诚实边界声明")
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        print(f"OK: fingerprint 已写入 {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
