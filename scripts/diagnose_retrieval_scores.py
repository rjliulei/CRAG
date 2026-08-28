#!/usr/bin/env python3
"""
Step A：200 子集 max 检索余弦分分布诊断（不调用生成 LLM / 裁判）。

用法（AutoDL，需 MiniLM 权重）:
  cd /root/autodl-tmp/CRAG
  source .venv/bin/activate
  python scripts/diagnose_retrieval_scores.py

输出:
  example_data/step4_max_score_diag_*.jsonl
  example_data/step4_max_score_diag_*.summary.json
"""
from __future__ import annotations

import argparse
import bz2
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]


def sentence_split(text: str, max_len: int = 1000) -> list[str]:
    """Prefer blingfire; fall back to regex."""
    text = text.strip()
    if not text:
        return [""]
    try:
        from blingfire import text_to_sentences_and_offsets

        _, offsets = text_to_sentences_and_offsets(text)
        return [text[s:e][:max_len] for s, e in offsets] or [""]
    except Exception:
        parts = re.split(r"(?<=[.!?。！？])\s+", text)
        return [p[:max_len] for p in parts if p.strip()] or [""]


def html_to_chunks(html: str) -> list[str]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html or "", "lxml")
    text = soup.get_text(" ", strip=True)
    return sentence_split(text)


def percentile(xs: list[float], p: float) -> float:
    if not xs:
        return float("nan")
    return float(np.percentile(np.asarray(xs, dtype=np.float64), p))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dataset",
        type=Path,
        default=REPO / "example_data/dev_subset_200_typical_20260825_222321.jsonl.bz2",
    )
    ap.add_argument(
        "--manifest",
        type=Path,
        default=REPO / "example_data/dev_subset_200_typical_20260825_222321.manifest.json",
    )
    ap.add_argument(
        "--embed-model",
        type=Path,
        default=REPO / "models/sentence-transformers/all-MiniLM-L6-v2",
    )
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--out-dir", type=Path, default=REPO / "example_data")
    args = ap.parse_args()

    if not args.dataset.is_file():
        print(f"ERROR: dataset missing: {args.dataset}")
        return 1
    if not (args.embed_model / "config.json").is_file():
        print(f"ERROR: MiniLM not found at {args.embed_model}")
        print("Run on AutoDL after hf download, or pass --embed-model")
        return 1

    try:
        import torch
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"ERROR: need sentence_transformers + torch: {e}")
        return 1

    meta_by_id: dict[str, dict] = {}
    if args.manifest.is_file():
        man = json.loads(args.manifest.read_text(encoding="utf-8"))
        for it in man.get("items") or []:
            meta_by_id[it["interaction_id"]] = it

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"loading embedder on {device}: {args.embed_model}", flush=True)
    model = SentenceTransformer(str(args.embed_model), device=device)

    rows: list[dict] = []
    print(f"scanning {args.dataset} ...", flush=True)
    with bz2.open(args.dataset, "rt", encoding="utf-8") as f:
        for line_i, line in enumerate(f):
            obj = json.loads(line)
            iid = obj["interaction_id"]
            query = obj.get("query") or ""
            pages = obj.get("search_results") or []
            chunks: list[str] = []
            for page in pages:
                chunks.extend(html_to_chunks(page.get("page_result") or ""))
            # de-dup like baseline
            chunks = list(dict.fromkeys(chunks))
            if not chunks:
                chunks = [""]

            emb_q = model.encode(
                [query], normalize_embeddings=True, batch_size=1, show_progress_bar=False
            )[0]
            emb_c = model.encode(
                chunks,
                normalize_embeddings=True,
                batch_size=args.batch_size,
                show_progress_bar=False,
            )
            scores = (emb_c * emb_q).sum(axis=1)
            order = (-scores).argsort()
            max_score = float(scores.max())
            top5 = scores[order[:5]]
            mean_top5 = float(top5.mean()) if len(top5) else 0.0
            top1 = float(scores[order[0]]) if len(scores) else 0.0
            top2 = float(scores[order[1]]) if len(scores) > 1 else top1
            gap = top1 - top2

            m = meta_by_id.get(iid, {})
            rows.append(
                {
                    "line_in_subset": line_i,
                    "interaction_id": iid,
                    "domain": obj.get("domain") or m.get("domain"),
                    "question_type": obj.get("question_type") or m.get("question_type"),
                    "rag_label": m.get("rag"),
                    "bucket": m.get("bucket"),
                    "n_chunks": len(chunks),
                    "max_score": max_score,
                    "mean_top5": mean_top5,
                    "top1_top2_gap": gap,
                    "below_0_30": max_score < 0.30,
                    "below_0_40": max_score < 0.40,
                    "below_0_50": max_score < 0.50,
                    "below_0_60": max_score < 0.60,
                }
            )
            if (line_i + 1) % 20 == 0:
                print(f"  {line_i + 1} done", flush=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_jsonl = args.out_dir / f"step4_max_score_diag_{ts}.jsonl"
    out_sum = args.out_dir / f"step4_max_score_diag_{ts}.summary.json"
    args.out_dir.mkdir(parents=True, exist_ok=True)

    with out_jsonl.open("w", encoding="utf-8") as fout:
        for r in rows:
            fout.write(json.dumps(r, ensure_ascii=False) + "\n")

    scores = [r["max_score"] for r in rows]
    gaps = [r["top1_top2_gap"] for r in rows]

    def count_below(thr: float) -> int:
        return sum(1 for s in scores if s < thr)

    by_rag: dict[str, list[float]] = defaultdict(list)
    by_bucket: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        by_rag[str(r.get("rag_label"))].append(r["max_score"])
        by_bucket[str(r.get("bucket"))].append(r["max_score"])

    def group_stats(d: dict[str, list[float]]) -> dict:
        return {
            k: {
                "n": len(v),
                "mean": float(np.mean(v)) if v else None,
                "p10": percentile(v, 10),
                "p25": percentile(v, 25),
                "p50": percentile(v, 50),
                "p75": percentile(v, 75),
            }
            for k, v in sorted(d.items(), key=lambda x: -len(x[1]))
        }

    summary = {
        "n": len(rows),
        "dataset": str(args.dataset),
        "embed_model": str(args.embed_model),
        "max_score": {
            "mean": float(np.mean(scores)),
            "p10": percentile(scores, 10),
            "p25": percentile(scores, 25),
            "p50": percentile(scores, 50),
            "p75": percentile(scores, 75),
            "p90": percentile(scores, 90),
            "min": float(min(scores)) if scores else None,
            "max": float(max(scores)) if scores else None,
        },
        "triggers_at_tau": {
            "0.30": count_below(0.30),
            "0.40": count_below(0.40),
            "0.50": count_below(0.50),
            "0.55": count_below(0.55),
            "0.60": count_below(0.60),
        },
        "top1_top2_gap": {
            "mean": float(np.mean(gaps)),
            "p25": percentile(gaps, 25),
            "p50": percentile(gaps, 50),
        },
        "by_rag_label": group_stats(by_rag),
        "by_bucket": group_stats(by_bucket),
        "detail_jsonl": str(out_jsonl),
    }
    out_sum.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== SUMMARY ===")
    print(json.dumps(summary["max_score"], indent=2))
    print("triggers_at_tau:", summary["triggers_at_tau"])
    print(f"wrote {out_jsonl}")
    print(f"wrote {out_sum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
