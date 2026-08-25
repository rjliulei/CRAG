#!/usr/bin/env python3
"""Summarize Phase B heuristic labels to markdown snippet."""

import json
from collections import Counter
from pathlib import Path

IN = Path("example_data/error_analysis_phaseB_labeled_heuristic_20260825.json")
OUT = Path("example_data/phaseB_summary_for_doc.md")

TRUST_LABELS = {"缺证据", "检索未用", "过度检索", "应拒却答", "生成错", "查询偏移", "冲突"}


def main() -> None:
    q = json.loads(IN.read_text(encoding="utf-8"))
    items = q["items"]
    n = len(items)
    ctr = Counter(it["fine_label"] for it in items)
    err = [it for it in items if it["fine_label"] not in ("检索有效", "合理拒答")]
    err_ctr = Counter(it["fine_label"] for it in err)
    trust_n = sum(v for k, v in ctr.items() if k in TRUST_LABELS)

    lines = [
        f"<!-- auto from {IN.name} -->",
        "",
        f"**样本 n={n}**（硬例优先队列；启发式 `heuristic_v1`，待人工抽检）",
        "",
        "### 细标签占比（110 条）",
        "",
        "| 细标签 | n | 占 110 | 与拒答/可信主线 |",
        "|--------|---|--------|-----------------|",
    ]
    for lab, c in ctr.most_common():
        rel = "✓ 相关" if lab in TRUST_LABELS else ("对照" if lab == "检索有效" else "拒答行为")
        lines.append(f"| {lab} | {c} | {c/n:.1%} | {rel} |")

    lines += [
        "",
        f"**主攻相关标签合计**（缺证据/检索未用/过度检索/应拒却答/生成错/查询偏移/冲突）："
        f" **{trust_n}/{n} = {trust_n/n:.1%}**",
        "",
        "**错误态 Top-3**（排除检索有效、合理拒答）：",
    ]
    for i, (lab, c) in enumerate(err_ctr.most_common(3), 1):
        lines.append(f"{i}. **{lab}** — {c} 条（{c/len(err):.1%} of {len(err)} 条错误态）")

    lines += ["", "### 桶 × 细标签", "", "| bucket | 细标签 | n |", "|--------|--------|---|"]
    c2 = Counter((it["bucket"], it["fine_label"]) for it in items)
    for (b, lab), c in sorted(c2.items(), key=lambda x: (-x[1], x[0][0])):
        lines.append(f"| {b} | {lab} | {c} |")

    lines += [
        "",
        "### 代表 case（人工 sense-check）",
        "",
        "| bucket | 标签 | 题型 | 问题摘要 | 预测摘要 |",
        "|--------|------|------|----------|----------|",
    ]
    shown = set()
    for bucket in (
        "rag_worse_hallucination",
        "both_hallucination",
        "rag_hallucination",
        "rag_helps",
    ):
        for it in [x for x in items if x["bucket"] == bucket]:
            if bucket in shown:
                break
            shown.add(bucket)
            qtxt = it["query"][:60].replace("|", "/")
            ptxt = (it.get("pred_snip") or "")[:50].replace("|", "/")
            lines.append(
                f"| {bucket} | {it['fine_label']} | {it['question_type']} | {qtxt} | {ptxt} |"
            )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
