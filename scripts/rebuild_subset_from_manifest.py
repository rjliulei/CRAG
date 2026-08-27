#!/usr/bin/env python3
"""从 manifest.json 的 idx 列表 + 全量 v4，重建子集 bz2（修复 Git LFS 占位文件）。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# reuse writer from build_typical_subset
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_typical_subset import write_selected_full_rows  # noqa: E402


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=repo / "example_data/dev_subset_200_typical_20260825_222321.manifest.json",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("/root/autodl-tmp/20260820-crag/crag_task_1_and_2_dev_v4.jsonl.bz2"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=repo / "example_data/dev_subset_200_typical_20260825_222321.jsonl.bz2",
    )
    args = parser.parse_args()

    if not args.manifest.is_file():
        raise SystemExit(f"missing manifest: {args.manifest}")
    if not args.dataset.is_file():
        raise SystemExit(f"missing dataset: {args.dataset}")

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    idxs = {int(item["idx"]) for item in data.get("items", [])}
    if not idxs:
        raise SystemExit("manifest has no items")

    print(f"rebuild {len(idxs)} rows from {args.dataset}")
    written = write_selected_full_rows(args.dataset, idxs, args.out)
    if written != len(idxs):
        raise SystemExit(f"wrote {written} but expected {len(idxs)}")
    print(f"OK: {args.out} ({args.out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
