# 03 · AutoDL 单卡 24GB 操作手册（主文档）

> 整理日期：2026-08-20  
> **用途**：在 AutoDL 上跑通 CRAG。按本文从上到下做即可，一般**不必**再翻 01/02。  
> 卡型：1 × 24GB（推荐 **RTX 4090**）

---

## 你只需要准备的东西

| 准备项 | 说明 |
|--------|------|
| AutoDL 实例 | 1×24GB GPU，镜像含 **CUDA + Python 3.10** |
| 数据盘空间 | ≥ **50GB**（建议 80GB+） |
| Hugging Face 账号 | 接受 [Llama 3 8B Instruct 条款](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)，并有 Token |
| OpenAI API Key | 本地自动评估要用 |

---

## 步骤 A · 租机与落盘

1. 租用 **RTX 4090 24G**（或同档 24GB），按量计费即可。  
2. 开机后所有内容放在**数据盘**，例如：

```bash
cd /root/autodl-tmp
# 上传或 git clone 本仓库
cd CRAG
```

关机不丢：仓库、权重、数据集都放数据盘，不要只放系统盘。

---

## 步骤 B · 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

`vllm` 安装较慢，可开 AutoDL 学术加速或换镜像源。

---

## 步骤 C · 改成单卡（必做）

编辑将要使用的基线文件（至少改你启用的那一个）：

- `models/vanilla_llama_baseline.py`（默认会用）
- `models/rag_llama_baseline.py`（跑 RAG 时）
- `models/rag_knowledge_graph_baseline.py`（跑 KG 时）

改成：

```python
BATCH_SIZE = 4                      # 或 SUBMISSION_BATCH_SIZE = 4
VLLM_TENSOR_PARALLEL_SIZE = 1       # 单卡必须是 1（默认 4，不改会挂）
VLLM_GPU_MEMORY_UTILIZATION = 0.85  # OOM 再改成 0.7
```

若启动报 Ray 相关错误，把同文件里 `worker_use_ray=True` 改成 `False`。

---

## 步骤 D · 下载数据

```bash
mkdir -p example_data
# 下载 Task1/2 开发集：
# https://github.com/facebookresearch/CRAG/raw/refs/heads/main/data/crag_task_1_and_2_dev_v4.jsonl.bz2?download=
# 放到：
# example_data/dev_data.jsonl.bz2
```

或改 `local_evaluation.py` 里的 `DATASET_PATH` 指向你的文件。

建议先截取少量样本做冒烟，再跑全量。

---

## 步骤 E · 下载模型权重

```bash
pip install "huggingface_hub[hf_transfer]"
huggingface-cli login
# 粘贴 HF Token

HF_HUB_ENABLE_HF_TRANSFER=1 huggingface-cli download \
    meta-llama/Meta-Llama-3-8B-Instruct \
    --local-dir-use-symlinks False \
    --local-dir models/meta-llama/Meta-Llama-3-8B-Instruct \
    --exclude "*.pth"
```

仅当跑 RAG / RAG-KG 时再下：

```bash
HF_HUB_ENABLE_HF_TRANSFER=1 huggingface-cli download \
    sentence-transformers/all-MiniLM-L6-v2 \
    --local-dir-use-symlinks False \
    --local-dir models/sentence-transformers/all-MiniLM-L6-v2 \
    --exclude "*.bin" "*.h5" "*.ot"
```

---

## 步骤 F · 选择模型

编辑 `models/user_config.py`：

```python
# 第一次建议先 DummyModel 冒烟，再改回 InstructModel
from models.vanilla_llama_baseline import InstructModel
UserModel = InstructModel
```

---

## 步骤 G · 环境变量

```bash
export OPENAI_API_KEY=sk-你的密钥
# 可选：
# export EVALUATION_MODEL_NAME=gpt-4-0125-preview
```

Task 2/3 或 RAG-KG 时另开终端：

```bash
cd mock_api
pip install -r requirements.txt
uvicorn server:app --host 127.0.0.1 --port 8000
# 主终端：
export CRAG_MOCK_API_URL=http://127.0.0.1:8000
```

Task 1 + Vanilla/RAG（只用网页检索结果）通常**不需要** Mock API。

---

## 步骤 H · 运行

```bash
cd /root/autodl-tmp/CRAG   # 按你的实际路径
source .venv/bin/activate
python local_evaluation.py
```

成功时日志会出现 `score` / `accuracy` / `hallucination` / `missing`。

---

## Checklist（打勾即可）

- [ ] AutoDL 1×24GB，Python 3.10 + CUDA
- [ ] 代码/数据/权重在数据盘
- [ ] `pip install -r requirements.txt`
- [ ] `VLLM_TENSOR_PARALLEL_SIZE = 1`，`BATCH_SIZE = 4`
- [ ] `example_data/dev_data.jsonl.bz2` 已就绪
- [ ] HF 登录并下载 Llama 3 8B
- [ ] `OPENAI_API_KEY` 已设置
- [ ] `user_config.py` 指向目标模型
- [ ] `python local_evaluation.py`
- [ ] 不用时关机，避免空转计费

---

## 常见问题

| 现象 | 处理 |
|------|------|
| 多卡/并行相关报错 | 确认 `VLLM_TENSOR_PARALLEL_SIZE=1` |
| CUDA OOM | `BATCH_SIZE=1`，`gpu_memory_utilization=0.7` |
| 找不到数据/权重 | 检查路径是否在仓库内相对路径正确 |
| HF 下载慢 | AutoDL 学术加速，或本机下好再上传数据盘 |
| OpenAI 失败 | 检查 Key、余额、出网 |
| 关机后文件没了 | 确认写在 `/root/autodl-tmp` 等数据盘 |

---

## 和官方评测的关系

| | 你现在（AutoDL） | 官方 |
|--|------------------|------|
| GPU | 1×24GB | 4×T4 16GB |
| 参数 | TP=1 | TP=4 |
| 目的 | 开发、跑通、调参 | 对齐提交环境 |

开发阶段用本手册即可；若以后要严格对齐比赛，再租 4×T4 对照。

---

## 还需要看别的文档吗？

| 需求 | 要不要 |
|------|--------|
| 在 AutoDL 跑通基线 | **不用**，跟本文就够 |
| 查字段含义 / Task3 下载细节 | 需要时再看 `docs/dataset.md` |
| 了解三个基线差异 | 需要时再看 `docs/baselines.md` |
| 硬件选型背景 | 可选看 [01-硬件要求.md](./01-硬件要求.md) |
