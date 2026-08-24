# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# Local evaluation variant: judge with deepseek-ai/DeepSeek-V3.2 via an
# OpenAI-compatible API (SiliconFlow by default).
#
# Original OpenAI GPT judge path remains in local_evaluation.py.

"""
Usage (SiliconFlow example):

  # Put keys in project-root .env (see .env), then:
  python local_evaluation_deepseek.py

  # Or export manually:
  # export SILICONFLOW_API_KEY=sk-...
  # export OPENAI_BASE_URL=https://api.siliconflow.cn/v1
  # export EVALUATION_MODEL_NAME=deepseek-ai/DeepSeek-V3.2

Same generation pipeline as local_evaluation.py; only the judge client/model differs.
"""

import os

from local_evaluation import (
    evaluate_predictions,
    generate_predictions,
    load_dotenv,
)


if __name__ == "__main__":
    from models.user_config import UserModel

    load_dotenv()
    # 全量 Task1/2 开发集（已下载目录）；冒烟可改回 example_data/dev_data.jsonl.bz2
    DATASET_PATH = os.getenv(
        "DATASET_PATH",
        "/root/autodl-tmp/20260820-crag/crag_task_1_and_2_dev_v4.jsonl.bz2",
    )
    EVALUATION_MODEL_NAME = os.getenv(
        "EVALUATION_MODEL_NAME", "deepseek-ai/DeepSeek-V3.2"
    )

    participant_model = UserModel()
    participant_model_name = type(participant_model).__name__
    queries, ground_truths, predictions = generate_predictions(
        DATASET_PATH, participant_model
    )
    evaluation_results = evaluate_predictions(
        queries,
        ground_truths,
        predictions,
        EVALUATION_MODEL_NAME,
        dataset_path=DATASET_PATH,
        participant_model_name=participant_model_name,
    )
