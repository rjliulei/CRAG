# CRAG 数据集文档 / CRAG Dataset Documentation

## 概述 / Overview

CRAG 数据集旨在支持检索增强生成（Retrieval-Augmented Generation，RAG）模型的开发与评估。它包含两类主要数据：

The CRAG dataset is designed to support the development and evaluation of Retrieval-Augmented Generation (RAG) models. It consists of two main types of data:

1. **问答对 / Question Answering Pairs：** 问题及其对应答案。 / Pairs of questions and their corresponding answers.
2. **检索内容 / Retrieval Contents：** 用于信息检索以支持答案生成的内容。 / Contents for information retrieval to support answer generation.

检索内容分为两类，以模拟 RAG 的实际场景： / Retrieval contents are divided into two types to simulate practical scenarios for RAG:

1. **网页搜索结果 / Web Search Results：** 对每个问题，最多存储 `50` 个**完整 HTML 页面**，以问题文本作为搜索查询检索得到。对于 Task 1 与 Task 2，会从 `top-10` 页面中**随机选取** `5` 个页面。这些页面很可能与问题相关，但不保证一定相关。 / For each question, up to `50` **full HTML pages** are stored, retrieved using the question text as a search query. For Task 1 & 2, `5 pages` are **randomly selected** from the `top-10 pages`. These pages are likely relevant to the question, but relevance is not guaranteed.
2. **模拟知识图谱与 API / Mock KGs and APIs：** Mock API 用于模拟真实世界的**知识图谱（KG）**或 **API 搜索**。给定若干输入参数，它们输出可能有助于也可能无助于回答用户问题的相关结果。 / The Mock API is designed to mimic real-world **Knowledge Graphs (KGs)** or **API searches**. Given some input parameters, they output relevant results, which may or may not be helpful in answering the user's question.

## 下载 CRAG 数据 / Download CRAG Data

- **Task #1：** [问答对与检索内容 / QA Pairs & Retrieval Contents](https://github.com/facebookresearch/CRAG/raw/refs/heads/main/data/crag_task_1_and_2_dev_v4.jsonl.bz2?download=)
- **Task #2：** [问答对与检索内容 / QA Pairs & Retrieval Contents](https://github.com/facebookresearch/CRAG/raw/refs/heads/main/data/crag_task_1_and_2_dev_v4.jsonl.bz2?download=)，[模拟知识图谱与 API / Mock KGs and APIs](/mock_api)
- **Task #3：** 问答对与检索内容 / QA Pairs & Retrieval Contents（分别下载第 [1](https://github.com/facebookresearch/CRAG/raw/refs/heads/main/data/crag_task_3_dev_v4.tar.bz2.part1?download=)、[2](https://github.com/facebookresearch/CRAG/raw/refs/heads/main/data/crag_task_3_dev_v4.tar.bz2.part2?download=)、[3](https://github.com/facebookresearch/CRAG/raw/refs/heads/main/data/crag_task_3_dev_v4.tar.bz2.part3?download=)、[4](https://github.com/facebookresearch/CRAG/raw/refs/heads/main/data/crag_task_3_dev_v4.tar.bz2.part4?download=) 部分；然后用 `cat crag_task_3_dev_v4.tar.bz2.part* > crag_task_3_dev_v4.tar.bz2` 合并），[模拟知识图谱与 API / Mock KGs and APIs](/mock_api)

## 数据模式 / Data Schema

| 字段名 / Field Name             | 类型 / Type          | 描述 / Description                                                                                                                                                           |
|------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `interaction_id`       | string        | 每个样本的唯一标识符。 / A unique identifier for each example.                                                                                                                                |
| `query_time`           | string        | 查询与网页搜索发生的日期与时间。 / Date and time when the query and the web search occurred.                                                                                                            |
| `domain`               | string        | 查询的领域标签。可能取值："finance"、"music"、"movie"、"sports"、"open"。"Open" 包括不属于前四个领域的任意事实性查询。 / Domain label for the query. Possible values: "finance", "music", "movie", "sports", "open". "Open" includes any factual queries not among the previous four domains. |
| `question_type`        | string        | 查询的类型标签。可能取值包括："simple"、"simple_w_condition"、"comparison"、"aggregation"、"set"、"false_premise"、"post-processing"、"multi-hop"。 / Type label about the query. Possible values include: "simple", "simple_w_condition", "comparison", "aggregation", "set", "false_premise", "post-processing", "multi-hop".      |
| `static_or_dynamic`    | string        | 表示问题答案是否会变化及预期变化速率。可能取值："static"、"slow-changing"、"fast-changing"、"real-time"。 / Indicates whether the answer to a question changes and the expected rate of change. Possible values: "static", "slow-changing", "fast-changing", and "real-time".    |
| `query`                | string        | RAG 需要回答的问题。 / The question for RAG to answer.                                                                                                                                       |
| `answer`               | string        | 问题的金标准答案。 / The gold standard answer to the question.                                                                                                                             |
| `alt_ans`  | list        | 问题的其他有效金标准答案。 / Other valid gold standard answers to the question.                                                                                                                    |
| `split`                | integer       | 数据划分指示，0 表示验证集，1 表示公开测试集。 / Data split indicator, where 0 is for validation and 1 is for the public test.                                                                                         |
| `popularity`                | string       | 问题中提及实体的流行度类别，"head"、"torso"、"tail" 分别对应高、中、低流行度。我们按实体类型用启发式定义流行度，并尽量为每个分桶创建大致相等数量的问题。所有 popularity 标签非空的问题都是知识图谱（KG）问题——答案来自 KG。当 popularity 为空字符串时，表示答案来自网页。 / Popularity category of the entity mentioned in the question, with "head", "torso" and "tail" corresponding to the top, middle, and bottom popularity. We defined popularity based on heuristics for each entity type and created a roughly equal number of questions for each bucket. All questions with popularity labels non-empty are Knowledge Graph (KG) questions - questions with answers coming from the KG. When popularity is an empty string, it means the answer to the question comes from the web.
| `search_results`       | list of JSON  | 每个查询最多包含 `k` 个 HTML 页面（Task #1 为 `k=5`，Task #3 为 `k=50`），包括页面名称、URL、摘要、完整 HTML 与最后修改时间。 / Contains up to `k` HTML pages for each query (`k=5` for Task #1 and `k=50` for Task #3), including page name, URL, snippet, full HTML, and last modified time.         |

### 搜索结果细节 / Search Results Detail

| 键 / Key                  | 类型 / Type   | 描述 / Description                                             |
|----------------------|--------|---------------------------------------------------------|
| `page_name`          | string | 网页名称。 / The name of the webpage.                                |
| `page_url`           | string | 网页 URL。 / The URL of the webpage.                                 |
| `page_snippet`       | string | 描述页面主要内容的短段落。 / A short paragraph describing the major content of the page. |
| `page_result`        | string | 网页的完整 HTML。 / The full HTML of the webpage.                           |
| `page_last_modified` | string | 页面最后修改时间。 / The time when the page was last modified.               |
