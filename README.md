# CRAG：综合 RAG 基准 / CRAG: Comprehensive RAG Benchmark

综合 RAG 基准（Comprehensive RAG Benchmark，CRAG）是一个丰富且全面的事实问答基准，旨在推动 RAG 研究。除了问答对之外，CRAG 还提供模拟 API，用于模拟网页与知识图谱搜索。CRAG 涵盖五个领域、八类问题，反映从热门到长尾的实体流行度差异，以及从年到秒的时间动态性。

The Comprehensive RAG Benchmark (CRAG) is a rich and comprehensive factual question answering benchmark designed to advance research in RAG. Besides question-answer pairs, CRAG provides mock APIs to simulate web and knowledge graph search. CRAG is designed to encapsulate a diverse array of questions across five domains and eight question categories, reflecting varied entity popularity from popular to long-tail, and temporal dynamisms ranging from years to seconds.

本仓库迁移自 / This repository is migrated from [meta-comprehensive-rag-benchmark-kdd-cup-2024](https://gitlab.aicrowd.com/aicrowd/challenges/meta-comprehensive-rag-benchmark-kdd-cup-2024)。

## 📁 仓库目录说明 / Repository Layout

| 目录 / Directory | 作用 / Purpose |
|------------------|----------------|
| [`models/`](models/) | 参赛/基线模型实现与入口配置（`user_config.py` 选择 Vanilla / RAG / RAG-KG）；本地权重也放在此目录下约定路径。 / Participant & baseline model code and entry config (`user_config.py`); local model weights live under the expected paths here. |
| [`mock_api/`](mock_api/) | 模拟知识图谱 / 垂直搜索 API（`server.py`、`cragkg/` 离线数据、`apiwrapper/` 客户端）。Task 2/3 与 RAG-KG 基线会用到。 / Mock KG / domain APIs (`server.py`, offline `cragkg/`, `apiwrapper/`). Used by Task 2/3 and the RAG-KG baseline. |
| [`docs/`](docs/) | 官方说明：数据集、基线、权重下载等；本机落地步骤见 [`docs/工作记录/`](docs/工作记录/)。 / Official docs (dataset, baselines, weight download); local AutoDL runbooks under [`docs/工作记录/`](docs/工作记录/). |
| [`prompts/`](prompts/) | 自动评估裁判用的指令与上下文示例模板。 / Judge prompts / in-context templates for auto-evaluation. |
| [`tokenizer/`](tokenizer/) | 评估侧截断答案用的分词器资源（与生成模型分词不必完全同一套）。 / Tokenizer assets used when truncating answers for evaluation. |
| [`utils/`](utils/) | 公共工具（如 `cragapi_wrapper.py`，封装对 Mock API 的调用）。 / Shared helpers (e.g. Mock API client wrapper). |
| [`example_data/`](example_data/) | 小样本或指向开发集的数据入口（如 `dev_data.jsonl.bz2`）。 / Small sample / symlink entry for the eval dataset. |
| [`data/`](data/) | 官方预留的数据目录位（大文件通常放数据盘，再链到此处或改 `DATASET_PATH`）。 / Placeholder for datasets (large files often live on a data disk; symlink or set `DATASET_PATH`). |
| [`logs/`](logs/) | 本地跑评估时的日志输出（如 `tee` 落盘）。 / Local evaluation logs (e.g. from `tee`). |
| [`api_responses/`](api_responses/) | 裁判 API 调用的请求/响应落盘，便于排查自动评估。 / Saved judge API request/response dumps for debugging auto-eval. |

根目录关键脚本 / Key root scripts：

| 文件 / File | 作用 / Purpose |
|-------------|----------------|
| [`local_evaluation.py`](local_evaluation.py) | 端到端：生成答案 + 自动评估（默认 GPT 裁判）。 / End-to-end generation + auto-eval (default GPT judge). |
| [`local_evaluation_deepseek.py`](local_evaluation_deepseek.py) | 同上流水线，裁判改为 DeepSeek（如硅基流动 OpenAI 兼容接口）。 / Same pipeline with a DeepSeek-compatible judge. |
| [`requirements.txt`](requirements.txt) | Python 依赖（含 `vllm`、`transformers` 等版本约束）。 / Python dependencies (incl. pinned `vllm` / `transformers`). |

本机 AutoDL 操作请优先看 / For AutoDL single-GPU runbooks, start at：[`docs/工作记录/00-目录.md`](docs/工作记录/00-目录.md)。


## 📊 数据集与模拟 API / Dataset and Mock APIs

关于 CRAG 数据集（下载、模式等）的更多细节，请参见 [docs/dataset.md](docs/dataset.md)；模拟 API 请参见 [mock_api](mock_api)。

Please find more details about the CRAG dataset (download, schema, etc.) in [docs/dataset.md](docs/dataset.md) and mock APIs in [mock_api](mock_api).


## 📏 评估指标 / Evaluation Metrics

RAG 系统通过评分方法评估，衡量对评估集问题的回答质量。回答被评为完美、可接受、缺失或不正确：

RAG systems are evaluated using a scoring method that measures response quality to questions in the evaluation set. Responses are rated as perfect, acceptable, missing, or incorrect:

- 完美（Perfect）：回答正确回应用户问题，且不含幻觉内容。 / The response correctly answers the user question and contains no hallucinated content.

- 可接受（Acceptable）：回答对用户问题有用，但可能含不影响答案有用性的轻微错误。 / The response provides a useful answer to the user question, but may contain minor errors that do not harm the usefulness of the answer.

- 缺失（Missing）：未提供所请求的信息。例如 “I don’t know”、“I’m sorry I can’t find …” 或类似表述，而未给出具体答案。 / The answer does not provide the requested information. Such as “I don’t know”, “I’m sorry I can’t find …” or similar sentences without providing a concrete answer to the question.

- 不正确（Incorrect）：提供错误或与问题无关的信息。 / The response provides wrong or irrelevant information to answer the user question


自动评估 / Auto-evaluation：
- 自动评估采用基于规则的匹配与 LLM 评判来检查答案正确性。会给出三种分数：正确（1 分）、缺失（0 分）、不正确（-1 分）。
- Automatic evaluation employs rule-based matching and LLM assessment to check answer correctness. It will assign three scores: correct (1 point), missing (0 points), and incorrect (-1 point).


评估实现细节请参见 / Please refer to [local_evaluation.py](local_evaluation.py) for more details on how the evaluation was implemented.


## ✍️ 如何运行端到端评估？ / How to run end-to-end evaluation?

1. **安装** 指定依赖 / **Install** specific dependencies
    ```bash
    pip install -r requirements.txt
    ```

2. 请按照 [models/README.md](models/README.md) 中的说明与示例编写自己的模型。 / Please follow the instructions in [models/README.md](models/README.md) for instructions and examples on how to write your own models.

3. 编写完模型后，更新 [models/user_config.py](models/user_config.py) / After writing your own model(s), update [models/user_config.py](models/user_config.py)

   例如，在 models/user_config.py 中指定 InstructModel 以调用 llama3-8b-instruct 模型 / For example, in models/user_config.py, specify InstructModel to call llama3-8b-instruct model
   ```bash
   from models.vanilla_llama_baseline import InstructModel 
   UserModel = InstructModel

   ```

4. 使用 `python local_evaluation.py` 在本地测试模型。该脚本将运行答案生成与自动评估。 / Test your model locally using `python local_evaluation.py`. This script will run answer generation and auto-evaluation.


## 🏁 基线 / Baselines

我们提供三个基线供演示，更多说明见 [docs/baselines.md](docs/baselines.md)。 / We include three baselines for demonstration purposes, and you can read more about them in [docs/baselines.md](docs/baselines.md).


## 引用 / Citations

```
@article{yang2024crag,
      title={CRAG -- Comprehensive RAG Benchmark}, 
      author={Xiao Yang and Kai Sun and Hao Xin and Yushi Sun and Nikita Bhalla and Xiangsen Chen and Sajal Choudhary and Rongze Daniel Gui and Ziran Will Jiang and Ziyu Jiang and Lingkun Kong and Brian Moran and Jiaqi Wang and Yifan Ethan Xu and An Yan and Chenyu Yang and Eting Yuan and Hanwen Zha and Nan Tang and Lei Chen and Nicolas Scheffer and Yue Liu and Nirav Shah and Rakesh Wanga and Anuj Kumar and Wen-tau Yih and Xin Luna Dong},
      year={2024},
      journal={arXiv preprint arXiv:2406.04744},
      url={https://arxiv.org/abs/2406.04744}
}
```

## 许可证 / License

本项目采用 [Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)](LICENSE) 许可。该许可允许在非商业用途下分享与改编作品，并需注明出处。快速了解请访问 [Creative Commons License](https://creativecommons.org/licenses/by-nc/4.0/)。

This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)](LICENSE). This license permits sharing and adapting the work, provided it's not used for commercial purposes and appropriate credit is given. For a quick overview, visit [Creative Commons License](https://creativecommons.org/licenses/by-nc/4.0/).
