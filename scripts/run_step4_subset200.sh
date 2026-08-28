#!/usr/bin/env bash
# Step 4：200 子集 RAG 对照 / v1 / v2 / 诊断
# 用法：
#   bash scripts/run_step4_subset200.sh baseline
#   bash scripts/run_step4_subset200.sh abstain [tau]      # v1
#   bash scripts/run_step4_subset200.sh abstain_v2 [sim]   # v2
#   bash scripts/run_step4_subset200.sh diagnose           # Step A

set -euo pipefail

MODE="${1:-}"
ARG2="${2:-}"
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
  diagnose)
    echo "=== Step A: max_score diagnose ==="
    python scripts/diagnose_retrieval_scores.py
    exit $?
    ;;
  baseline)
    set_env_kv "RAG_ABSTAIN_ENABLED" "0"
    set_env_kv "RAG_ABSTAIN_V2_ENABLED" "0"
    LOG="logs/eval_rag_subset200_baseline_$(date +%Y%m%d_%H%M%S).log"
    ;;
  abstain)
    TAU="${ARG2:-0.40}"
    set_env_kv "RAG_ABSTAIN_ENABLED" "1"
    set_env_kv "RAG_ABSTAIN_MIN_MAX_SCORE" "$TAU"
    set_env_kv "RAG_ABSTAIN_V2_ENABLED" "0"
    LOG="logs/eval_rag_subset200_abstain_t${TAU/./}_$(date +%Y%m%d_%H%M%S).log"
    ;;
  abstain_v2)
    SIM="${ARG2:-0.35}"
    set_env_kv "RAG_ABSTAIN_ENABLED" "0"
    set_env_kv "RAG_ABSTAIN_V2_ENABLED" "1"
    set_env_kv "RAG_ABSTAIN_ANSWER_MIN_SIM" "$SIM"
    LOG="logs/eval_rag_subset200_abstain_v2_s${SIM/./}_$(date +%Y%m%d_%H%M%S).log"
    ;;
  *)
    echo "Usage: $0 baseline | abstain [tau] | abstain_v2 [sim] | diagnose"
    exit 1
    ;;
esac

mkdir -p logs
echo "=== MODE=$MODE DATASET_PATH=$SUBSET LOG=$LOG ==="
grep -E '^(DATASET_PATH|RAG_ABSTAIN_ENABLED|RAG_ABSTAIN_MIN_MAX_SCORE|RAG_ABSTAIN_V2_ENABLED|RAG_ABSTAIN_ANSWER_MIN_SIM)=' "$ENV_FILE" || true

python local_evaluation_deepseek.py 2>&1 | tee "$LOG"
echo "=== DONE. Log: $LOG ==="
