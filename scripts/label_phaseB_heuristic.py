#!/usr/bin/env python3
"""Phase B 启发式首轮细标（可人工修订）。"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

IN = Path("example_data/error_analysis_phaseB_queue_20260825.json")
OUT = Path("example_data/error_analysis_phaseB_labeled_heuristic_20260825.json")

REFUSAL_KEYS = (
    "i don't know",
    "i do not know",
    "unknown",
    "not sure",
    "cannot find",
    "can't find",
    "no information",
    "insufficient",
)


def is_refusal(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in REFUSAL_KEYS)


def provisional(it: dict) -> tuple[str, str]:
    bucket = it["bucket"]
    qt = it["question_type"]
    pred = it.get("pred_snip") or ""
    rag = it["rag"]

    if bucket == "rag_helps":
        return "检索有效", "RAG救回"
    if qt == "false_premise" and rag == "missing":
        return "合理拒答", "假前提+missing"
    if qt == "false_premise" and rag == "hallucination":
        return "应拒却答", "假前提仍作答"
    if bucket == "rag_worse_hallucination":
        return "过度检索", "Vanilla对RAG幻觉"
    if bucket in ("both_missing", "rag_missing"):
        if qt == "false_premise":
            return "合理拒答", "假前提拒答"
        return "过早停", "拒答/待核是否过保守"
    if bucket in ("both_hallucination", "rag_hallucination"):
        if pred and len(pred.split()) <= 6:
            return "生成错", "短答错误(启发式)"
        return "缺证据", "幻觉默认(启发式-待精标)"
    return "缺证据", "fallback"


def main() -> None:
    q = json.loads(IN.read_text(encoding="utf-8"))
    items = q["items"]
    for it in items:
        lab, note = provisional(it)
        it["fine_label"] = lab
        it["note"] = note
        it["label_source"] = "heuristic_v1"

    q["label_pass"] = "heuristic_v1"
    q["caveat"] = (
        "启发式首轮：rag_worse→过度检索；幻觉默认缺证据/短答生成错；"
        "需人工抽检修订。不代替通读检索原文。"
    )
    OUT.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"n={len(items)}")
    print("labels:", dict(Counter(it["fine_label"] for it in items)))
    print("bucket x label:")
    c2 = Counter((it["bucket"], it["fine_label"]) for it in items)
    for (b, lab), v in sorted(c2.items(), key=lambda x: (x[0][0], -x[1])):
        print(f"  {b:28} {lab:8} {v}")
    print(f"wrote {OUT}")

    print("\n== samples ==")
    for bucket in (
        "rag_worse_hallucination",
        "both_hallucination",
        "rag_hallucination",
        "rag_helps",
    ):
        for it in [x for x in items if x["bucket"] == bucket][:2]:
            print("---", bucket, it["fine_label"], it["question_type"], it["domain"])
            print("Q:", it["query"][:140])
            print("P:", (it.get("pred_snip") or "")[:120])
            print("note:", it["note"])


if __name__ == "__main__":
    main()
