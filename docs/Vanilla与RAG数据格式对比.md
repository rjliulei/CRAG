# Vanilla（Llama）与 RAG 数据格式对照

> 说明：磁盘上的评测 jsonl **同一份**；差别在「是否使用 `search_results`」以及「最终拼进 Llama 的 prompt」。  
> 代码：`models/vanilla_llama_baseline.py`、`models/rag_llama_baseline.py`；模式见 `docs/dataset.md`。

---

## 1. 数据集单条（jsonl，两种基线共用）

示例字段（摘自 `example_data/dev_data.jsonl` 一类开发集）：

```json
{
  "interaction_id": "3dbed55e-66a3-4dcd-907d-096f49387e41",
  "query": "is microsoft office 2019 available in a greater number of languages than microsoft office 2013?",
  "query_time": "02/28/2024, 10:04:54 PT",
  "domain": "open",
  "question_type": "comparison",
  "static_or_dynamic": "static",
  "answer": "yes",
  "alternative_answers": "[]",
  "split": 1,
  "search_results": [
    {
      "page_name": "Office 2019 vs. Office 2016, Q&A: ...",
      "page_url": "https://...",
      "page_snippet": "摘要短文本...",
      "page_result": "<!doctype html>...完整 HTML...",
      "page_last_modified": ""
    }
  ]
}
```

| 字段 | 含义 |
|------|------|
| `interaction_id` | 样本唯一 ID |
| `query` / `query_time` | 问题与提问时间 |
| `domain` / `question_type` / `static_or_dynamic` | 元数据（分析用；基线生成可不读） |
| `answer` / `alternative_answers` | 金标（生成阶段模型可不读；打分用） |
| `search_results` | 预缓存网页列表（非评测时现场搜索） |

`search_results[]` 单页字段：

| 键 | 含义 |
|----|------|
| `page_name` | 标题 |
| `page_url` | URL |
| `page_snippet` | 摘要 |
| `page_result` | **完整 HTML**（RAG 主要用这个） |
| `page_last_modified` | 最后修改时间（可为空） |

Task 1/2 通常每问约 **5** 页（从 top-10 随机抽取）；Task 3 可达约 **50** 页。网页是官方事先用搜索 API（如 Brave）抓取后写入数据集的，本地评测只读文件。

---

## 2. 评测传给模型的 batch（接口相同）

`local_evaluation` / `load_data_in_batches` 组装的字典：

```python
batch = {
    "interaction_id": [str, ...],           # 长度 = batch_size
    "query":          [str, ...],
    "query_time":     [str, ...],
    "search_results": [ [page_dict, ...], ... ],  # 每问一个页面列表
    "answer":         [str, ...],           # 生成阶段可选不用；打分用
}
```

Vanilla 与 RAG 的 `batch_generate_answer(batch)` **签名相同**；差异在函数内部是否消费 `search_results`。

---

## 3. Vanilla（Llama only）实际格式

### 3.1 使用的字段

| 使用 | 忽略 |
|------|------|
| `query`、`query_time` | `search_results`（读入变量但**不参与** prompt） |

### 3.2 进入 Llama 的 chat 内容

```text
[system]
You are provided with a question and various references. Your task is to answer
the question succinctly, using the fewest words possible. If the references do
not contain the necessary information to answer the question, respond with
'I don't know'.

[user]
Current Time: 02/28/2024, 10:04:54 PT
Question: is microsoft office 2019 ...?
```

要点：没有 `# References` 块；所谓 “references” 在 Vanilla 路径下实际为空，模型主要靠参数记忆 + 时间戳。

### 3.3 输出

`List[str]`，每问一条短答；生成侧常用 `max_tokens=50`（评测侧另有约 75 token 截断约定）。

---

## 4. RAG 实际格式

### 4.1 使用的字段

| 使用 | 说明 |
|------|------|
| `query`、`query_time` | 同 Vanilla |
| `search_results[].page_result` | HTML → 抽文本 → 切句 → 向量检索 |
| `page_snippet` / `page_url` 等 | 官方基线里**基本不用** |

另需模型权重：`Llama-3.1-8B-Instruct`（生成）+ `all-MiniLM-L6-v2`（句向量检索）。

### 4.2 中间数据形态（检索管道）

```text
page_result (HTML)
  → BeautifulSoup 纯文本
  → BlingFire 按句切分（单句最长约 1000 字符）
  → MiniLM 编码句子与 query（归一化向量）
  → 余弦相似度 Top-K（默认 NUM_CONTEXT_SENTENCES = 20）
  → 拼成引用字符串，总长截断约 MAX_CONTEXT_REFERENCES_LENGTH = 4000 字符
```

中间结果概念上是：

```python
# 每个 interaction_id 对应
retrieval_results: List[str]  # 约 ≤20 个相关句子
```

### 4.3 进入 Llama 的 chat 内容

```text
[system]
You are provided with a question and various references. Your task is to answer
the question succinctly, using the fewest words possible. If the references do
not contain the necessary information to answer the question, respond with
'I don't know'. There is no need to explain the reasoning behind your answers.

[user]
# References 
- <检索到的句子1>
- <检索到的句子2>
- ...
------

Using only the references listed above, answer the following question: 
Current Time: 02/28/2024, 10:04:54 PT
Question: is microsoft office 2019 ...?
```

要点：Llama **应只依据** `# References` 作答；证据不足则 `I don't know`。

### 4.4 输出

与 Vanilla 相同：`List[str]` 短答。

---

## 5. 差异分析

| 维度 | Vanilla | RAG |
|------|---------|-----|
| 磁盘数据文件 | 同一 jsonl | 同一 jsonl |
| 是否用网页 | **否** | **是**（预缓存 HTML，非现场上网） |
| 核心网页字段 | — | `page_result` |
| 额外模型 | 无 | MiniLM（检索） |
| Prompt 证据区 | 无 | `# References` 短句列表 |
| 回答依据 | 参数知识 + 时间 | 提示要求：**仅引用句** |
| 接口 batch 形状 | 相同 | 相同 |
| 输出形态 | 短文本答案 | 短文本答案 |

**一句话：** 数据格式在文件层相同；RAG 多了「HTML → 句子 → 向量召回 → 写入 prompt」的管道，因此 Llama 看到的 user 消息从「只有问题」变成「证据 + 问题」。

---

## 6. 相关文档

- 数据集模式：`docs/dataset.md`
- 流水线与三基线：`docs/工作记录/04-项目代码解析.md` §4
- 跑 RAG 操作：`docs/工作记录/05-RAG与RAG-KG基线操作手册.md`
