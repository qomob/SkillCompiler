#!/usr/bin/env python3
"""Style Analyzer — 语料 → 实测 Style Fingerprint（v3.1）

解决 v3.0 的核心技术债：Style Fingerprint 是 schema-level claim，不是 executable measurement。
本脚本把"禁止凭印象填数值"（Gotcha #14）变成可执行约束：

    Corpus → Linguistic / Structural / Semantic / Pattern 测量 → 归一化 → 12 维 Fingerprint

用法:
    python3 scripts/style_analyzer.py <corpus_dir_or_file> [--output fingerprint.json]

输入: 目录（递归读取 *.txt / *.md）或单个文本文件。语料必须是创作者本人的实际作品，
     不是本人谈创作的文字（否则测出来的是"方法论文体"而非"作品文体"）。
输出: JSON —— raw_measurements（原始测量，含句长 mean/median/variance）
     + fingerprint（0-1 归一化，对齐 schemas/creative-ir-schema.json 的 12 维）
     + corpus 统计 + warnings。

C2 阶段消费方式: fingerprint 直接写入 Creative IR style.fingerprint，
fingerprint_source 置 "measured"（validate_creative_ir.py 在 full 模式强制校验）。

实现约束: 纯 stdlib。中文为主的语料按字符级启发式测量（无分词依赖），
所有归一化参数为中文语料经验值，集中在 NORMALIZATION 常量，可审计可复现。
测量是统计拟合，不是风格复刻——结果用于漂移检测基准，见 honest-boundaries。

退出码: 0=成功 2=文件/用法错误
"""
import json
import math
import re
import sys
from pathlib import Path

VERSION = "1.0.0"

# ---------------------------------------------------------------- 语料信号表 #

FIRST_PERSON = ("我", "我们", "俺", "咱", "本人", "我自己")
FIRST_PERSON_EN = re.compile(r"\b(I|we|my|me|our|us)\b", re.IGNORECASE)

EMOTION_WORDS = (
    "开心 难过 痛苦 兴奋 愤怒 生气 恨 爱 喜欢 感动 害怕 焦虑 崩溃 幸福 温暖 孤独 "
    "骄傲 羞愧 惊讶 失望 期待 想念 遗憾 快乐 悲伤 恐惧 激动 心疼 委屈 后悔 无助 "
    "happy sad angry love hate afraid excited lonely grateful proud"
).split()

CTA_MARKERS = (
    "关注 点赞 收藏 转发 点击 购买 下单 链接 优惠 折扣 私聊 私信 扫码 报名 咨询 "
    "加我 秒杀 限时 福利 赠品 客服 优惠券 带货 好物推荐"
).split()

AI_CLICHE_SIGNALS = (
    "今天给大家分享 你是否也有 在这个快节奏的时代 不知道大家有没有 让我们一起 "
    "总的来说 综上所述 深深地 默默地 静静地 璀璨 绽放 心中的 照亮 征程 扬帆 起航 "
    "砥砺 行稳致远 赋能 抓手 突破自我 遇见更好的自己 愿你 余生 星辰大海 奔赴 "
    "不仅仅是 更是 生活不止 诗和远方 岁月 沉淀自己 致敬每一个 努力的你"
).split()

METAPHOR_MARKERS = ("像 仿佛 如同 好比 犹如 宛如 恰似 像极了 是一场".split())

NARRATIVE_MARKERS = (
    "那天 当时 后来 有一次 记得 去年 上周 昨天 前天 那次 第一次 结果 没想到 原来 "
    "去年 年初 年底 早上 晚上 半夜 那年 那段时间"
).split()

ABSTRACT_MARKERS = (
    "本质 意义 价值 概念 思维 逻辑 层面 方式 关系 程度 感觉 气质 灵魂 氛围 力量 "
    "精神 境界 格局 维度 状态 能力 效率 体系 模式 趋势 周期 认知 心态 情绪 能量 "
    "频率 颗粒度 方法论 增长 底层 顶层 闭环 链路 抓手 矩阵 心智 声量 调性"
).split()
ABSTRACT_SUFFIX = re.compile(r"[\u4e00-\u9fff]{2}(?:性|化|度|感|力|主义|效应)")

CONCRETE_TIME = re.compile(r"\d{4}\s*年|\d+\s*(?:岁|年|天|小时|分钟|万|块|元|斤|公里|次|遍|人|家|条|%|折)")

SENTENCE_SPLIT = re.compile(r"[。！？!?；;\n]+")
ELLIPSIS = "……"
PUNCT_STRIP = re.compile(r"[\s，。！？!?；;：:、\u201c\u201d\u2018\u2019\"'()\[\]（）——-…·~～,\.]+")

# 归一化参数：分子密度单位与缩放上限（中文语料经验值，修改必须记录理由）
NORMALIZATION = {
    "sentence_length_cap": 40,      # 平均句长 40+ 字 → 1.0
    "sentence_cv_cap": 1.0,         # 句长变异系数 1.0 → 1.0
    "abstraction_per_100_cap": 6,   # 每 100 字抽象标记 6 个 → 1.0
    "concreteness_per_100_cap": 5,  # 每 100 字具体锚点 5 个 → 1.0
    "metaphor_rate_cap": 0.3,       # 30% 句子含隐喻 → 1.0
    "emotion_per_100_cap": 3,       # 每 100 字情绪词 3 个 → 1.0
    "rhetorical_rate_cap": 0.4,     # 问句+感叹+隐喻 合计占比 40% → 1.0
    "dup4gram_rate_cap": 0.10,      # 4-gram 重复率 10% → 1.0
    "whitespace_per_100_cap": 25,   # 每 100 行 25 个空行 → 1.0
    "commercial_per_100_cap": 3,    # 每 100 字 CTA 3 个 → 1.0
    "ai_per_1000_cap": 5,           # 每 1000 字 AI 腔信号 5 个 → 1.0
}

MIN_DOCS = 3
MIN_SENTENCES = 50


def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else round(x, 3))


def load_corpus(path):
    p = Path(path)
    if p.is_file():
        return [p.read_text(encoding="utf-8", errors="ignore")], [p.name]
    if p.is_dir():
        docs, names = [], []
        for f in sorted(p.rglob("*")):
            if f.suffix.lower() in (".txt", ".md") and f.is_file():
                docs.append(f.read_text(encoding="utf-8", errors="ignore"))
                names.append(str(f.relative_to(p)))
        return docs, names
    print(f"ERROR: 语料路径不存在或不可读: {path}", file=sys.stderr)
    sys.exit(2)


def split_sentences(text):
    text = text.replace(ELLIPSIS, "。")
    parts = [s for s in SENTENCE_SPLIT.split(text) if s.strip()]
    return parts


def content_len(sentence):
    return len(PUNCT_STRIP.sub("", sentence))


def count_substring_hits(text, markers):
    return sum(text.count(m) for m in markers)


def measure(docs):
    """对语料做全部原始测量。所有密度分母统一为 100 字符（内容字符）。"""
    sentences = []
    para_lengths, blank_lines, total_lines = [], 0, 0
    q_count = exclaim_count = 0
    full_text = ""
    for doc in docs:
        full_text += doc
        sentences.extend(split_sentences(doc))
        lines = doc.split("\n")
        total_lines += len(lines)
        blank_lines += sum(1 for ln in lines if not ln.strip())
        para = [ln for ln in lines if ln.strip()]
        para_lengths.append(len("\n".join(para)))
    for s in sentences:
        if s.rstrip().endswith("？") or s.rstrip().endswith("?"):
            q_count += 1
        if s.rstrip().endswith("！") or s.rstrip().endswith("!"):
            exclaim_count += 1

    lengths = [content_len(s) for s in sentences]
    n = len(lengths)
    mean = sum(lengths) / n if n else 0.0
    median = sorted(lengths)[n // 2] if n else 0
    variance = sum((x - mean) ** 2 for x in lengths) / n if n else 0.0
    stdev = math.sqrt(variance)
    cv = stdev / mean if mean else 0.0

    chars = max(len(PUNCT_STRIP.sub("", full_text)), 1)
    n100 = chars / 100.0
    n1000 = chars / 1000.0

    fp_sentences = [s for s in sentences if any(m in s for m in FIRST_PERSON) or FIRST_PERSON_EN.search(s)]
    metaphor_sents = [s for s in sentences if any(m in s for m in METAPHOR_MARKERS)]
    narrative_sents = [s for s in sentences if any(m in s for m in NARRATIVE_MARKERS)]
    fragments = [x for x in lengths if 0 < x < 10]

    abstract_hits = count_substring_hits(full_text, ABSTRACT_MARKERS) + len(ABSTRACT_SUFFIX.findall(full_text))
    concrete_hits = len(CONCRETE_TIME.findall(full_text))
    emotion_hits = count_substring_hits(full_text, EMOTION_WORDS)
    cta_hits = count_substring_hits(full_text, CTA_MARKERS)
    ai_hits = count_substring_hits(full_text, AI_CLICHE_SIGNALS)

    # 4-gram 重复率（内容字符流）
    stream = PUNCT_STRIP.sub("", full_text)
    grams = [stream[i:i + 4] for i in range(len(stream) - 3)]
    gram_count = {}
    for g in grams:
        gram_count[g] = gram_count.get(g, 0) + 1
    dup_grams = sum(c for c in gram_count.values() if c > 1)
    dup4_rate = (dup_grams / len(grams)) if grams else 0.0

    return {
        "total_chars": chars,
        "total_sentences": n,
        "sentence_length": {"mean": round(mean, 2), "median": median, "variance": round(variance, 2), "stdev": round(stdev, 2), "cv": round(cv, 3)},
        "fragment_rate": round(len(fragments) / n, 3) if n else 0.0,
        "first_person_sentence_ratio": round(len(fp_sentences) / n, 3) if n else 0.0,
        "rhetorical_question_rate": round(q_count / n, 3) if n else 0.0,
        "exclamation_rate": round(exclaim_count / n, 3) if n else 0.0,
        "metaphor_sentence_rate": round(len(metaphor_sents) / n, 3) if n else 0.0,
        "narrative_marker_rate": round(len(narrative_sents) / n, 3) if n else 0.0,
        "abstract_marker_per_100": round(abstract_hits / n100, 3),
        "concrete_anchor_per_100": round(concrete_hits / n100, 3),
        "emotion_word_per_100": round(emotion_hits / n100, 3),
        "cta_per_100": round(cta_hits / n100, 3),
        "ai_cliche_per_1000": round(ai_hits / n1000, 3),
        "dup4gram_rate": round(dup4_rate, 4),
        "blank_line_per_100_lines": round(blank_lines / (total_lines / 100.0), 2) if total_lines else 0.0,
        "avg_paragraph_chars": round(sum(para_lengths) / len(para_lengths), 1) if para_lengths else 0.0,
    }


def normalize(raw):
    """raw_measurements → 12 维 0-1 fingerprint（对齐 creative-ir-schema.json）。"""
    N = NORMALIZATION
    sl = raw["sentence_length"]
    fingerprint = {
        "sentence_length": clamp01(sl["mean"] / N["sentence_length_cap"]),
        "sentence_variance": clamp01(sl["cv"] / N["sentence_cv_cap"]),
        "abstraction": clamp01(raw["abstract_marker_per_100"] / N["abstraction_per_100_cap"]),
        "concreteness": clamp01(raw["concrete_anchor_per_100"] / N["concreteness_per_100_cap"]),
        "metaphor_density": clamp01(raw["metaphor_sentence_rate"] / N["metaphor_rate_cap"]),
        "emotional_explicitness": clamp01(
            0.6 * raw["emotion_word_per_100"] / N["emotion_per_100_cap"] + 0.4 * raw["exclamation_rate"]),
        "narrative_density": clamp01(
            0.5 * raw["narrative_marker_rate"] + 0.5 * raw["first_person_sentence_ratio"]),
        "rhetorical_density": clamp01(
            (raw["rhetorical_question_rate"] + raw["exclamation_rate"] + raw["metaphor_sentence_rate"])
            / N["rhetorical_rate_cap"]),
        "repetition": clamp01(raw["dup4gram_rate"] / N["dup4gram_rate_cap"]),
        "whitespace": clamp01(raw["blank_line_per_100_lines"] / N["whitespace_per_100_cap"]),
        "commercial_explicitness": clamp01(raw["cta_per_100"] / N["commercial_per_100_cap"]),
        "ai_pattern_risk": clamp01(raw["ai_cliche_per_1000"] / N["ai_per_1000_cap"]),
    }
    return fingerprint


def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python3 scripts/style_analyzer.py <corpus_dir_or_file> [--output fingerprint.json]", file=sys.stderr)
        sys.exit(2)
    corpus_path = args[0]
    out_path = None
    if "--output" in args:
        i = args.index("--output")
        if i + 1 >= len(args):
            print("ERROR: --output 需要一个文件路径", file=sys.stderr)
            sys.exit(2)
        out_path = args[i + 1]

    docs, names = load_corpus(corpus_path)
    warnings = []
    if len(docs) < MIN_DOCS:
        warnings.append(f"语料仅 {len(docs)} 篇（建议 ≥{MIN_DOCS} 篇完整作品）——Fingerprint 置信度低，应降低 IR meta.confidence 并在 honest-boundaries 声明")

    raw = measure(docs)
    if raw["total_sentences"] < MIN_SENTENCES:
        warnings.append(f"语料仅 {raw['total_sentences']} 句（建议 ≥{MIN_SENTENCES}）——统计量不稳定，只填有把握的维度")

    result = {
        "tool": "style_analyzer.py",
        "tool_version": VERSION,
        "corpus": {
            "path": str(corpus_path),
            "documents": len(docs),
            "document_names": names[:20],
            "total_sentences": raw["total_sentences"],
            "total_chars": raw["total_chars"],
            "enough_corpus": len(docs) >= MIN_DOCS and raw["total_sentences"] >= MIN_SENTENCES,
        },
        "raw_measurements": raw,
        "fingerprint": normalize(raw),
        "fingerprint_source": "measured",
        "warnings": warnings,
    }
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if out_path:
        Path(out_path).write_text(output, encoding="utf-8")
        print(f"OK: Fingerprint 已写入 {out_path}（{len(docs)} 篇语料，{raw['total_sentences']} 句）")
    else:
        print(output)
    for w in warnings:
        print(f"  - [WARN] {w}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
