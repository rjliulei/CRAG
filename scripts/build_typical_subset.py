#!/usr/bin/env python3
"""从 Vanilla / RAG 全量评测落盘中，按题型·领域·对错类型分层抽典型子集。

不必手工逐条挑选。RAG dump 用 sample_idx；Vanilla 旧 dump 用 query 对齐。
无 dump 近似为 missing（含少量 exact-match 未落盘）。输出文件名含时间戳。

两遍扫描全量数据：第 1 遍只读元数据抽样；第 2 遍写出选中完整行（含 search_results）。
"""

from __future__ import annotations

import argparse
import bz2
import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

SCORE_RE = re.compile(r'"score"\s*:\s*(\d+)')
QUERY_RE = re.compile(
    r"Question:\s*(.*?)\s*\n\s*Ground truth:",
    re.DOTALL | re.IGNORECASE,
)

META_KEYS = (
    "interaction_id",
    "query",
    "domain",
    "question_type",
    "static_or_dynamic",
    "split",
)


def parse_score(response: str) -> int | None:
    try:
        return int(json.loads(response).get("score"))
    except Exception:
        m = SCORE_RE.search(response or "")
        return int(m.group(1)) if m else None


def score_to_label(score: int | None) -> str:
    if score == 1:
        return "correct"
    if score == 0:
        return "hallucination"
    return "unknown"


def load_rag_labels(dump_dir: Path) -> dict[int, str]:
    labels: dict[int, str] = {}
    for fp in dump_dir.glob("*.json"):
        if fp.name == "run_metadata.json":
            continue
        m = re.match(r"^(\d+)_", fp.name)
        if not m:
            continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        labels[int(m.group(1))] = score_to_label(parse_score(data.get("response", "")))
    return labels


def load_vanilla_labels_by_query(dump_dir: Path) -> dict[str, str]:
    by_query: dict[str, str] = {}
    for fp in dump_dir.glob("*.json"):
        if fp.name == "run_metadata.json":
            continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        user = ""
        for msg in data.get("messages") or []:
            if msg.get("role") == "user":
                user = msg.get("content") or ""
                break
        qm = QUERY_RE.search(user)
        if not qm:
            continue
        by_query[qm.group(1).strip()] = score_to_label(
            parse_score(data.get("response", ""))
        )
    return by_query


def outcome_bucket(vanilla: str, rag: str) -> str:
    if rag == "hallucination" and vanilla == "hallucination":
        return "both_hallucination"
    if rag == "hallucination" and vanilla == "correct":
        return "rag_worse_hallucination"
    if rag == "hallucination":
        return "rag_hallucination"
    if rag == "correct" and vanilla != "correct":
        return "rag_helps"
    if rag == "correct" and vanilla == "correct":
        return "both_correct"
    if rag == "missing" and vanilla == "missing":
        return "both_missing"
    if rag == "missing":
        return "rag_missing"
    return f"other_{vanilla}_{rag}"


def _field(line: str, key: str) -> str | None:
    """从超长 jsonl 行里抠标量字段，避免 json.loads 解析整页 HTML。"""
    m = re.search(rf'"{re.escape(key)}"\s*:\s*"((?:\\.|[^"\\])*)"', line)
    if not m:
        return None
    return json.loads(f'"{m.group(1)}"')


def load_meta(path: Path) -> list[dict]:
    """只保留抽样所需字段，避免把 HTML 全塞进内存。"""
    rows: list[dict] = []
    with bz2.open(path, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            rows.append({k: _field(line, k) for k in META_KEYS} | {"_idx": i})
            if (i + 1) % 500 == 0:
                print(f"  meta loaded {i + 1} ...", flush=True)
    return rows


def stratified_sample(
    records: list[dict],
    *,
    n: int,
    seed: int,
    min_false_premise: int = 28,
) -> list[dict]:
    """先保证 false_premise 配额，再按硬例桶 + 题型×领域补齐。"""
    rng = random.Random(seed)
    # 硬例桶优先；配额随 n 缩放
    quota_order = [
        ("both_hallucination", max(20, n // 6)),
        ("rag_worse_hallucination", max(15, n // 8)),
        ("rag_hallucination", max(25, n // 5)),
        ("rag_helps", max(15, n // 8)),
        ("both_correct", max(10, n // 12)),
        ("both_missing", max(15, n // 8)),
        ("rag_missing", max(10, n // 12)),
    ]
    # false_premise 内再偏硬例
    fp_bucket_pref = [
        "both_hallucination",
        "rag_worse_hallucination",
        "rag_hallucination",
        "rag_helps",
        "both_missing",
        "rag_missing",
        "both_correct",
    ]

    by_bucket: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_bucket[r["_bucket"]].append(r)

    selected: list[dict] = []
    selected_ids: set[str] = set()

    def take_from(pool: list[dict], k: int) -> int:
        avail = [x for x in pool if x["interaction_id"] not in selected_ids]
        rng.shuffle(avail)
        took = 0
        for x in avail[:k]:
            selected.append(x)
            selected_ids.add(x["interaction_id"])
            took += 1
        return took

    # 1) false_premise 保底（略高于全量 ~11%）
    fp_pool = [r for r in records if r.get("question_type") == "false_premise"]
    fp_by_bucket: dict[str, list[dict]] = defaultdict(list)
    for r in fp_pool:
        fp_by_bucket[r["_bucket"]].append(r)
    fp_need = min(min_false_premise, len(fp_pool), n)
    for b in fp_bucket_pref:
        if sum(1 for x in selected if x.get("question_type") == "false_premise") >= fp_need:
            break
        remain = fp_need - sum(
            1 for x in selected if x.get("question_type") == "false_premise"
        )
        take_from(fp_by_bucket.get(b, []), remain)
    # 若偏好桶不够，任意 false_premise 补满
    fp_have = sum(1 for x in selected if x.get("question_type") == "false_premise")
    if fp_have < fp_need:
        take_from(fp_pool, fp_need - fp_have)

    # 2) 硬例桶配额（已选计入）
    for bucket, k in quota_order:
        have = sum(1 for x in selected if x["_bucket"] == bucket)
        if have < k:
            take_from(by_bucket.get(bucket, []), k - have)

    # 3) 题型 × 领域补覆盖
    by_type_domain: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in records:
        if r["interaction_id"] in selected_ids:
            continue
        key = (r.get("question_type") or "unk", r.get("domain") or "unk")
        by_type_domain[key].append(r)

    keys = list(by_type_domain.keys())
    rng.shuffle(keys)
    while len(selected) < n and keys:
        progressed = False
        for key in list(keys):
            if len(selected) >= n:
                break
            pool = [
                x for x in by_type_domain[key] if x["interaction_id"] not in selected_ids
            ]
            if not pool:
                keys.remove(key)
                continue
            pick = rng.choice(pool)
            selected.append(pick)
            selected_ids.add(pick["interaction_id"])
            progressed = True
        if not progressed:
            break

    if len(selected) < n:
        rest = [r for r in records if r["interaction_id"] not in selected_ids]
        rng.shuffle(rest)
        for x in rest[: n - len(selected)]:
            selected.append(x)
            selected_ids.add(x["interaction_id"])

    rng.shuffle(selected)
    return selected[:n]


def write_selected_full_rows(
    dataset: Path, selected_idxs: set[int], out_path: Path
) -> int:
    written = 0
    with bz2.open(dataset, "rt", encoding="utf-8") as fin, bz2.open(
        out_path, "wt", encoding="utf-8"
    ) as fout:
        for i, line in enumerate(fin):
            if i not in selected_idxs:
                continue
            line = line.strip()
            if line:
                fout.write(line + "\n")
                written += 1
            if written % 20 == 0:
                print(f"  wrote {written}/{len(selected_idxs)} ...", flush=True)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="构建 CRAG 典型开发子集")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/crag_task_1_and_2_dev_v4.jsonl.bz2"),
    )
    parser.add_argument(
        "--rag-dumps",
        type=Path,
        default=Path(
            "api_responses/eval_RAGModel_DeepSeek-V3.2_20260824_163051_crag_task_1_and_2_dev_v4"
        ),
    )
    parser.add_argument(
        "--vanilla-dumps",
        type=Path,
        default=Path("api_responses/eval_deepseek_20260821_225909"),
    )
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--min-false-premise",
        type=int,
        default=28,
        help="false_premise 最少条数（全量约 11%%，默认略抬高）",
    )
    parser.add_argument("--out-dir", type=Path, default=Path("example_data"))
    args = parser.parse_args()

    print("loading RAG dumps ...", flush=True)
    rag_by_idx = load_rag_labels(args.rag_dumps)
    print(f"  rag labeled: {len(rag_by_idx)}", flush=True)

    print("loading Vanilla dumps ...", flush=True)
    vanilla_by_q = load_vanilla_labels_by_query(args.vanilla_dumps)
    print(f"  vanilla labeled: {len(vanilla_by_q)}", flush=True)

    print("pass1: load meta ...", flush=True)
    metas = load_meta(args.dataset)
    print(f"  total: {len(metas)}", flush=True)

    for r in metas:
        q = (r.get("query") or "").strip()
        rag = rag_by_idx.get(r["_idx"], "missing")
        vanilla = vanilla_by_q.get(q, "missing")
        r["_vanilla_label"] = vanilla
        r["_rag_label"] = rag
        r["_bucket"] = outcome_bucket(vanilla, rag)

    selected = stratified_sample(
        metas,
        n=args.n,
        seed=args.seed,
        min_false_premise=args.min_false_premise,
    )
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_data = args.out_dir / f"dev_subset_{len(selected)}_typical_{ts}.jsonl.bz2"
    out_meta = args.out_dir / f"dev_subset_{len(selected)}_typical_{ts}.manifest.json"

    print("pass2: write selected full rows ...", flush=True)
    written = write_selected_full_rows(
        args.dataset, {r["_idx"] for r in selected}, out_data
    )
    if written != len(selected):
        raise SystemExit(f"wrote {written} but selected {len(selected)}")

    fp_n = sum(1 for r in selected if r.get("question_type") == "false_premise")
    summary = {
        "created_at": ts,
        "n": len(selected),
        "seed": args.seed,
        "min_false_premise": args.min_false_premise,
        "false_premise_n": fp_n,
        "dataset": str(args.dataset),
        "rag_dumps": str(args.rag_dumps),
        "vanilla_dumps": str(args.vanilla_dumps),
        "output": str(out_data),
        "label_caveat": (
            "无裁判 dump 记为 missing（含少量 exact-match 未落盘）；"
            "Vanilla 用 query 对齐 dump。"
        ),
        "bucket_counts": dict(Counter(r["_bucket"] for r in selected)),
        "question_type_counts": dict(
            Counter(r.get("question_type") for r in selected)
        ),
        "domain_counts": dict(Counter(r.get("domain") for r in selected)),
        "rag_label_counts": dict(Counter(r["_rag_label"] for r in selected)),
        "vanilla_label_counts": dict(
            Counter(r["_vanilla_label"] for r in selected)
        ),
        "items": [
            {
                "idx": r["_idx"],
                "interaction_id": r["interaction_id"],
                "domain": r.get("domain"),
                "question_type": r.get("question_type"),
                "vanilla": r["_vanilla_label"],
                "rag": r["_rag_label"],
                "bucket": r["_bucket"],
            }
            for r in selected
        ],
    }
    out_meta.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"wrote {out_data}")
    print(f"wrote {out_meta}")
    print("buckets:", summary["bucket_counts"])
    print("question_type:", summary["question_type_counts"])
    print("domain:", summary["domain_counts"])


if __name__ == "__main__":
    main()
