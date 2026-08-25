#!/usr/bin/env python3
"""Phase B：从典型子集导出硬例待标队列，并附 query / 裁判预测摘要。"""

from __future__ import annotations

import bz2
import json
import re
from collections import Counter
from pathlib import Path

MANIFEST = Path("example_data/dev_subset_200_typical_20260825_222321.manifest.json")
DATASET = Path("data/crag_task_1_and_2_dev_v4.jsonl.bz2")
RAG_DIR = Path(
    "api_responses/eval_RAGModel_DeepSeek-V3.2_20260824_163051_crag_task_1_and_2_dev_v4"
)
OUT = Path("example_data/error_analysis_phaseB_queue_20260825.json")

PRED_RE = re.compile(r"Prediction:\s*(.*)$", re.S | re.I)
GT_RE = re.compile(r"Ground truth:\s*(.*?)\n\s*Prediction:", re.S | re.I)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    items = manifest["items"]
    need = {it["idx"] for it in items}

    print("loading queries ...", flush=True)
    queries: dict[int, str] = {}
    with bz2.open(DATASET, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i not in need:
                continue
            obj = json.loads(line)
            queries[i] = (obj.get("query") or "")[:500]
            if len(queries) == len(need):
                break
    print(f"  queries: {len(queries)}", flush=True)

    print("loading RAG dumps for subset ...", flush=True)
    rag_info: dict[int, dict] = {}
    for fp in RAG_DIR.glob("*.json"):
        if fp.name == "run_metadata.json":
            continue
        m = re.match(r"^(\d+)_", fp.name)
        if not m:
            continue
        idx = int(m.group(1))
        if idx not in need:
            continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        user = ""
        for msg in data.get("messages") or []:
            if msg.get("role") == "user":
                user = msg.get("content") or ""
                break
        pred_m = PRED_RE.search(user)
        gt_m = GT_RE.search(user)
        resp = data.get("response", "")
        expl, score = "", None
        try:
            parsed = json.loads(resp)
            expl = str(parsed.get("explanation", ""))[:240]
            score = parsed.get("score")
        except Exception:
            pass
        rag_info[idx] = {
            "pred": (pred_m.group(1).strip() if pred_m else "")[:300],
            "gt": (gt_m.group(1).strip() if gt_m else "")[:200],
            "score": score,
            "explanation": expl,
        }
    print(f"  rag dumps: {len(rag_info)}", flush=True)

    by_b: dict[str, list] = {}
    for it in items:
        by_b.setdefault(it["bucket"], []).append(it)

    selected: list[dict] = []
    seen: set[int] = set()

    def take(bucket: str, k: int) -> None:
        for it in by_b.get(bucket, []):
            if len([x for x in selected if x["bucket"] == bucket]) >= k:
                break
            if it["idx"] in seen:
                continue
            selected.append(it)
            seen.add(it["idx"])

    take("rag_worse_hallucination", 25)
    take("both_hallucination", 30)
    take("rag_hallucination", 30)
    take("rag_helps", 10)
    take("rag_missing", 5)
    take("both_missing", 5)

    n_fp = 0
    for it in items:
        if n_fp >= 5:
            break
        if it.get("question_type") != "false_premise":
            continue
        if it["idx"] in seen:
            continue
        selected.append(it)
        seen.add(it["idx"])
        n_fp += 1

    rows = []
    for it in selected:
        idx = it["idx"]
        info = rag_info.get(idx, {})
        rows.append(
            {
                "idx": idx,
                "interaction_id": it.get("interaction_id"),
                "domain": it["domain"],
                "question_type": it["question_type"],
                "vanilla": it["vanilla"],
                "rag": it["rag"],
                "bucket": it["bucket"],
                "query": queries.get(idx, ""),
                "gt_snip": info.get("gt", ""),
                "pred_snip": info.get("pred", ""),
                "judge_explanation": info.get("explanation", ""),
                "fine_label": "",
                "note": "",
            }
        )

    OUT.write_text(
        json.dumps(
            {
                "n": len(rows),
                "note": "hard-first Phase B queue; fill fine_label",
                "label_set": [
                    "缺证据",
                    "检索未用",
                    "过早停",
                    "过度检索",
                    "查询偏移",
                    "冲突",
                    "生成错",
                    "应拒却答",
                    "合理拒答",
                    "检索有效",
                ],
                "items": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {OUT} n={len(rows)}")
    print("buckets:", dict(Counter(r["bucket"] for r in rows)))
    print("with_pred:", sum(1 for r in rows if r["pred_snip"]))


if __name__ == "__main__":
    main()
