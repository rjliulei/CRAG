# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# Local evaluation variant: judge with deepseek-ai/DeepSeek-V3.2 via an
# OpenAI-compatible API (SiliconFlow by default).
#
# Original OpenAI GPT judge path remains in local_evaluation.py.

"""
Usage (SiliconFlow example):

  export SILICONFLOW_API_KEY=sk-...
  # optional:
  # export OPENAI_BASE_URL=https://api.siliconflow.cn/v1
  # export EVALUATION_MODEL_NAME=deepseek-ai/DeepSeek-V3.2

  python local_evaluation_deepseek.py

Same generation pipeline as local_evaluation.py; only the judge client/model differs.
"""

import os

from local_evaluation import evaluate_predictions, generate_predictions


if __name__ == "__main__":
    from models.user_config import UserModel

    DATASET_PATH = "example_data/dev_data.jsonl.bz2"
    EVALUATION_MODEL_NAME = os.getenv(
        "EVALUATION_MODEL_NAME", "deepseek-ai/DeepSeek-V3.2"
    )

    participant_model = UserModel()
    queries, ground_truths, predictions = generate_predictions(
        DATASET_PATH, participant_model
    )
    evaluation_results = evaluate_predictions(
        queries, ground_truths, predictions, EVALUATION_MODEL_NAME
    )
