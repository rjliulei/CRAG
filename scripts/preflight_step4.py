#!/usr/bin/env python3
"""Step 4 跑前检查（无需 GPU / 不 import vllm/ray）。"""
from __future__ import annotations

import bz2
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBSET = os.path.join(
    REPO, "example_data", "dev_subset_200_typical_20260825_222321.jsonl.bz2"
)
LFS_PREFIX = "version https://git-lfs.github.com/spec/v1"


def is_lfs_pointer(path: str) -> bool:
    if not os.path.isfile(path) or os.path.getsize(path) > 512:
        return False
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read(64).startswith(LFS_PREFIX)


def count_bz2_lines(path: str) -> int:
    with bz2.open(path, "rt", encoding="utf-8") as f:
        return sum(1 for _ in f)


def main() -> int:
    ok = True
    print("=== Step 4 preflight ===")

    if not os.path.isfile(SUBSET):
        print(f"FAIL: subset missing: {SUBSET}")
        ok = False
    elif is_lfs_pointer(SUBSET):
        print(f"FAIL: subset is Git LFS pointer (not real bz2): {SUBSET}")
        print("  fix: python scripts/rebuild_subset_from_manifest.py")
        ok = False
    else:
        try:
            n = count_bz2_lines(SUBSET)
            print(f"OK: subset exists, n={n}")
        except OSError as e:
            print(f"FAIL: cannot read subset bz2: {e}")
            print("  fix: python scripts/rebuild_subset_from_manifest.py")
            ok = False

    user_cfg = os.path.join(REPO, "models", "user_config.py")
    with open(user_cfg, encoding="utf-8") as f:
        cfg_text = f.read()
    if "UserModel = RAGModel" in cfg_text and "from models.rag_llama_baseline import RAGModel" in cfg_text:
        print("OK: user_config.py -> RAGModel")
    else:
        print("FAIL: user_config.py not set to RAGModel")
        ok = False

    rag_py = os.path.join(REPO, "models", "rag_llama_baseline.py")
    with open(rag_py, encoding="utf-8") as f:
        rag_text = f.read()
    for token in ("RAG_ABSTAIN_ENABLED", "RAG_ABSTAIN_MIN_MAX_SCORE", "abstain_flags"):
        if token not in rag_text:
            print(f"FAIL: rag_llama_baseline.py missing {token}")
            ok = False
    if ok:
        print("OK: rag_llama_baseline.py has Step4 abstain gate")

    env_path = os.path.join(REPO, ".env")
    if os.path.isfile(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s.startswith("DATASET_PATH=") and "dev_subset_200" in s:
                    print(f"OK: .env {s}")
                if s.startswith("RAG_ABSTAIN_ENABLED="):
                    print(f"OK: .env {s}")
    else:
        print("WARN: .env not found")

    script = os.path.join(REPO, "scripts", "run_step4_subset200.sh")
    if os.path.isfile(script):
        print("OK: scripts/run_step4_subset200.sh exists")
    else:
        print("FAIL: missing run_step4_subset200.sh")
        ok = False

    print("=== preflight", "PASS" if ok else "FAIL", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
