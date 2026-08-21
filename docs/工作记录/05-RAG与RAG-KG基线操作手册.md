# 05 · RAG / RAG-KG 基线操作手册

> **前置**：已按 [03-AutoDL单卡24GB操作手册.md](./03-AutoDL单卡24GB操作手册.md) 跑通 **Vanilla**（环境、Llama 权重、`.env`、tmux、`max_model_len` 等）。  
> **用途**：你自行切换并跑另外两个官方基线——**网页 RAG**、**网页 + Mock KG**。  
> **原理**：[04-项目代码解析.md](./04-项目代码解析.md) §4.2 / §4.3。

---

## 0 · 三个基线对照（先选再跑）

| 基线 | `user_config.py` | 额外权重 | Mock API | 主要用什么信息 | 对应 Task 直觉 |
|------|------------------|----------|----------|----------------|----------------|
| Vanilla | `InstructModel` | 仅 Llama | 不需要 | 问题本身（忽略网页） | Task1 下限 |
| **RAG** | `RAGModel` | Llama + **MiniLM** | **不需要** | 网页 HTML → 切句 → 向量检索 → LLM | Task1 / 网页部分 |
| **RAG-KG** | `RAG_KG_Model` | Llama + MiniLM | **需要** | 网页检索 + Mock KG/API | Task2（示例偏 open/movie） |

同一时刻 **只能启用一个** `UserModel`，且 **同一张 GPU 上不要并行跑两个评测会话**。

---

## 1 · 跑前检查

### 1.1 停掉正在跑的 Vanilla（或其它）评测

```bash
tmux ls
# 若有 crag / 其它评测会话仍占 GPU：
tmux attach -t crag          # 确认是否已结束
# 未结束又要换基线：Ctrl+C 停任务，或
tmux kill-session -t crag

nvidia-smi                   # 显存应接近空闲
```

### 1.2 确认 Llama 权重仍在

```bash
ls models/meta-llama/Llama-3.1-8B-Instruct/*.safetensors | wc -l
# 期望 ≥ 1（完整下载一般为 4 个分片）
```

### 1.3 下载句向量模型（两个基线都要）

```bash
cd /root/autodl-tmp/CRAG
source .venv/bin/activate

# 可选加速：export HF_ENDPOINT=https://hf-mirror.com
hf download \
  sentence-transformers/all-MiniLM-L6-v2 \
  --local-dir models/sentence-transformers/all-MiniLM-L6-v2 \
  --exclude "*.bin" "*.h5" "*.ot"

ls models/sentence-transformers/all-MiniLM-L6-v2/config.json
```

### 1.4 单卡参数（仓库已改好，复查即可）

两个文件里应类似：

```python
VLLM_TENSOR_PARALLEL_SIZE = 1
VLLM_GPU_MEMORY_UTILIZATION = 0.85
VLLM_MAX_MODEL_LEN = 8192
SUBMISSION_BATCH_SIZE = 4
```

路径：

- `models/rag_llama_baseline.py`
- `models/rag_knowledge_graph_baseline.py`

**显存提醒**：vLLM（约 0.85）+ SentenceTransformer（默认也占 CUDA）可能 OOM。若启动或跑批时报 CUDA OOM：

1. 先把 `VLLM_GPU_MEMORY_UTILIZATION` 降到 `0.70`～`0.75`  
2. 仍不够：把 `SUBMISSION_BATCH_SIZE` 改为 `1` 或 `2`  
3. 再不够：临时把 `SentenceTransformer(..., device=...)` 改成 `cpu`（慢但稳）

依赖版本保持与 03 一致：`transformers==4.45.2`，勿升到 5.x。

---

## 2 · 基线 A：网页 RAG（`RAGModel`）

不启 Mock API。数据用 Task1/2 开发集即可（与 Vanilla 相同 `DATASET_PATH`）。

### 2.1 切换模型

编辑 `models/user_config.py`，**只保留** RAG 两行生效：

```python
# from models.vanilla_llama_baseline import InstructModel
# UserModel = InstructModel

from models.rag_llama_baseline import RAGModel
UserModel = RAGModel

# from models.rag_knowledge_graph_baseline import RAG_KG_Model
# UserModel = RAG_KG_Model
```

### 2.2 tmux 跑评估

```bash
cd /root/autodl-tmp/CRAG
tmux new -s crag-rag

# ---- 会话内 ----
source .venv/bin/activate
unset OMP_NUM_THREADS
mkdir -p logs
python local_evaluation_deepseek.py 2>&1 | tee logs/eval_rag_$(date +%Y%m%d_%H%M%S).log
```

一键后台（可选）：

```bash
cd /root/autodl-tmp/CRAG
source .venv/bin/activate
mkdir -p logs
LOG=logs/eval_rag_$(date +%Y%m%d_%H%M%S).log
tmux new-session -d -s crag-rag \
  "source .venv/bin/activate && unset OMP_NUM_THREADS && python local_evaluation_deepseek.py 2>&1 | tee $LOG"
echo "log -> $LOG"
```

回看：`tmux attach -t crag-rag` · 脱离：`Ctrl+b` 再 `d`。

### 2.3 成功时在看什么

- 日志里出现 `Generating predictions`，速度通常 **慢于 Vanilla**（HTML 解析 + 编码 + 检索）  
- 结束有 `score` / `accuracy` / `hallucination` / `missing`  
- 对比 Vanilla 同数据同裁判，看网页检索是否抬分

---

## 3 · 基线 B：网页 + KG（`RAG_KG_Model`）

需要 **两个 tmux 会话**：一个 Mock API，一个评测。

### 3.1 安装并启动 Mock API

```bash
cd /root/autodl-tmp/CRAG
source .venv/bin/activate

# 建议装到同一 venv（或单独 venv 也行，但端口要通）
pip install -r mock_api/requirements.txt \
  -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

tmux new -s crag-mock
# ---- 会话内：必须在 mock_api 目录启动，才能找到 cragkg 数据 ----
cd /root/autodl-tmp/CRAG/mock_api
source ../.venv/bin/activate
uvicorn server:app --host 127.0.0.1 --port 8000
```

另开终端自检：

```bash
curl -s http://127.0.0.1:8000/docs | head -c 200
# 或浏览器 /docs
```

保持该会话常开；评测进程通过 `CRAG_MOCK_API_URL` 访问它。

### 3.2 切换模型

`models/user_config.py`：

```python
# from models.vanilla_llama_baseline import InstructModel
# UserModel = InstructModel

# from models.rag_llama_baseline import RAGModel
# UserModel = RAGModel

from models.rag_knowledge_graph_baseline import RAG_KG_Model
UserModel = RAG_KG_Model
```

### 3.3 tmux 跑评估（带 Mock URL）

```bash
cd /root/autodl-tmp/CRAG
tmux new -s crag-ragkg

# ---- 会话内 ----
source .venv/bin/activate
unset OMP_NUM_THREADS
export CRAG_MOCK_API_URL=http://127.0.0.1:8000
mkdir -p logs
python local_evaluation_deepseek.py 2>&1 | tee logs/eval_ragkg_$(date +%Y%m%d_%H%M%S).log
```

也可把 `CRAG_MOCK_API_URL=http://127.0.0.1:8000` 写进项目根 `.env`（与 Key 一起被 `load_dotenv` 加载）。

### 3.4 示例代码能力边界（预期管理）

当前 `rag_knowledge_graph_baseline.py` 里 **KG 调用主要演示了 `open`（百科）与 `movie`**；finance / music / sports 虽有抽取模板，接 API 未完全铺开。  
因此：把它当 **Task2 骨架与对照实验**，不要默认当成「全领域最优 KG Agent」。

---

## 4 · 推荐跑法（省时间）

| 阶段 | 做什么 | 目的 |
|------|--------|------|
| 冒烟 | `DATASET_PATH=example_data/dev_data.jsonl.bz2`（小样本）各基线跑通 | 验证权重 / Mock / OOM |
| 对照 | 同一全量 Task1/2 开发集，依次 Vanilla → RAG → RAG-KG | 比三种信息源的分数差 |
| Task3 | 另备 Task3 数据（多分片 tar），仍用 RAG-KG + Mock | 更多网页噪声，更难 |

冒烟示例：

```bash
export DATASET_PATH=/root/autodl-tmp/CRAG/example_data/dev_data.jsonl.bz2
python local_evaluation_deepseek.py
```

全量路径仍可用环境变量覆盖（见 `local_evaluation_deepseek.py` 里 `DATASET_PATH`）。

---

## 5 · 会话与日志命名建议

| 用途 | tmux 名 | 日志前缀 |
|------|---------|----------|
| Vanilla | `crag` | `logs/eval_deepseek_*` |
| RAG | `crag-rag` | `logs/eval_rag_*` |
| Mock API | `crag-mock` | （终端输出即可） |
| RAG-KG | `crag-ragkg` | `logs/eval_ragkg_*` |

结束后：

```bash
tmux kill-session -t crag-rag
tmux kill-session -t crag-ragkg
tmux kill-session -t crag-mock   # Mock 不用时再关
```

---

## 6 · Checklist

- [ ] 当前 GPU 上无其它评测占用（`nvidia-smi`）
- [ ] 已下载 `models/sentence-transformers/all-MiniLM-L6-v2`
- [ ] `user_config.py` 只启用目标基线
- [ ] 单卡：`TP=1`，`max_model_len=8192`
- [ ] `.env` 中裁判 Key 可用（DeepSeek / 硅基流动）
- [ ] **RAG-KG**：`crag-mock` 已监听 `127.0.0.1:8000`，且评测侧设置了 `CRAG_MOCK_API_URL`
- [ ] 用 tmux + `tee` 落盘日志
- [ ] 跑完记录三份日志里的 `score` / `accuracy` / `hallucination` / `missing` 便于对比

---

## 7 · 常见问题

| 现象 | 处理 |
|------|------|
| 找不到 MiniLM | 按 §1.3 `hf download`；确认 `config.json` 存在 |
| CUDA OOM（RAG / RAG-KG） | 降 `VLLM_GPU_MEMORY_UTILIZATION`；降 batch；或 embedding 改 CPU |
| Mock 连不上 | 是否在 `mock_api/` 下启动；端口 8000；`curl` 测 `/docs`；检查 `CRAG_MOCK_API_URL` |
| `cragkg` 相关报错 | 工作目录必须是 `mock_api/`；确认 `mock_api/cragkg/{open,movie,...}` 存在 |
| 仍启用了 Vanilla | 检查 `user_config.py` 注释是否只留一个 `UserModel` |
| 与 Vanilla 抢 GPU | `tmux kill-session` 旧会话后再开 |
| 评测很慢 | RAG 要解析 HTML + 句向量，正常；可先小样本冒烟 |
| 依赖冲突 transformers 5.x | `pip install 'transformers==4.45.2' 'sentence-transformers==3.3.1'` |

---

## 8 · 和 03 / 04 的关系

- **环境、tmux、`.env`、裁判、数据盘路径**：一律跟 [03](./03-AutoDL单卡24GB操作手册.md)  
- **三种基线在代码里怎么拼上下文**：看 [04](./04-项目代码解析.md)  
- **本文**：只负责「换基线 →（可选）起 Mock → 开 tmux → 跑通并留日志」
