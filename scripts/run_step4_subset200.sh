#!/usr/bin/env bash
# Step 4：200 子集 RAG 对照 + 拒答（在 AutoDL 上执行）
# 用法：
#   cd /root/autodl-tmp/CRAG
#   bash scripts/run_step4_subset200.sh baseline    # Step 2
#   bash scripts/run_step4_subset200.sh abstain     # Step 3（τ=0.40）
#   bash scripts/run_step4_subset200.sh abstain 0.35  # Step 4 调参

set -euo pipefail

MODE="${1:-}"
TAU="${2:-0.40}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SUBSET="example_data/dev_subset_200_typical_20260825_222321.jsonl.bz2"
ENV_FILE="$REPO_ROOT/.env"

if [[ ! -f "$SUBSET" ]]; then
  echo "ERROR: missing $SUBSET"
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  echo "ERROR: .venv not found; activate/create venv first"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
unset OMP_NUM_THREADS

set_env_kv() {
  local key="$1" val="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
  fi
}

set_env_kv "DATASET_PATH" "$SUBSET"

case "$MODE" in
  baseline)
    set_env_kv "RAG_ABSTAIN_ENABLED" "0"
    LOG="logs/eval_rag_subset200_baseline_$(date +%Y%m%d_%H%M%S).log"
    ;;
  abstain)
    set_env_kv "RAG_ABSTAIN_ENABLED" "1"
    set_env_kv "RAG_ABSTAIN_MIN_MAX_SCORE" "$TAU"
    LOG="logs/eval_rag_subset200_abstain_t${TAU/./}_$(date +%Y%m%d_%H%M%S).log"
    ;;
  *)
    echo "Usage: $0 baseline | abstain [tau]"
    echo "  baseline       RAG 原版 (RAG_ABSTAIN_ENABLED=0)"
    echo "  abstain [tau]  RAG+拒答 (default tau=0.40)"
    exit 1
    ;;
esac

mkdir -p logs
echo "=== MODE=$MODE DATASET_PATH=$SUBSET LOG=$LOG ==="
grep -E '^(DATASET_PATH|RAG_ABSTAIN_ENABLED|RAG_ABSTAIN_MIN_MAX_SCORE)=' "$ENV_FILE" || true

python local_evaluation_deepseek.py 2>&1 | tee "$LOG"
echo "=== DONE. Log: $LOG ==="
