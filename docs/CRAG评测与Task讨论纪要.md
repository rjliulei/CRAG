# CRAG 评测与 Task 讨论纪要

> 整理日期：2026-08-24  
> 来源：本地跑通 Vanilla / RAG / RAG-KG 过程中的问答讨论  
> **说明**：本文档为讨论沉淀，不替代官方 `docs/dataset.md` 与操作手册。

---

## 1. Task 1 / 2 / 3 与数据文件的关系

### 1.1 没有单独的「Task 1 数据集文件」

| 文件 | 对应任务 | 说明 |
|------|----------|------|
| `crag_task_1_and_2_dev_v4.jsonl.bz2` | Task 1 + Task 2 **混合** | 官方 Task1、Task2 下载链接指向**同一份** |
| `crag_task_1_and_2_dev_v5.jsonl.bz2` | 同上（更新版） | v5 比 v4 多 `popularity` 字段 |
| `crag_task_3_dev_v*.tar.bz2`（分卷） | **Task 3 专用** | 需 `cat` 合并再解压；每问最多 50 页 HTML |

**Task 的区别在「方法/评测环境」，不在「是否换了数据文件」。**

### 1.2 如何在本地近似「只跑 Task 1 类题」

官方用 `popularity` 区分答案来源（**仅 v5 有此字段**）：

| `popularity` | 含义 |
|--------------|------|
| 空字符串 | 答案来自**网页** → Task 1 类题 |
| `head` / `torso` / `tail` | 答案来自 **KG** → Task 2 类题 |

**v4 实测**：2706 条中**无** `popularity` 字段，无法用此字段筛选。

筛 Task 1 子集示例（v5）：

```bash
python3 - <<'PY'
import bz2, json, os
src = "/root/autodl-tmp/20260820-crag/crag_task_1_and_2_dev_v5.jsonl.bz2"
out = "example_data/dev_task1_web_only.jsonl.bz2"
os.makedirs("example_data", exist_ok=True)
n = 0
with bz2.open(src, "rt") as fin, bz2.open(out, "wt") as fout:
    for line in fin:
        if json.loads(line).get("popularity", "") == "":
            fout.write(line if line.endswith("\n") else line + "\n")
            n += 1
print(f"Task1-like: {n} -> {out}")
PY
```

`.env` 中设 `DATASET_PATH=example_data/dev_task1_web_only.jsonl.bz2`，并用 **RAG**（不是 Vanilla）跑。

---

## 2. 为什么作者不拆成三个数据文件？

1. **同一套评测脚手架**：字段、`local_evaluation.py` 完全一致。  
2. **竞赛设计**：选手交**一套代码**，平台按 Task **换评测环境**（是否提供 Mock API、网页页数等），分别计分。  
3. **开发集混合存放**，方便本地开发；论文/榜单再按 Task **拆开报表**。  
4. **正式榜 Phase 2** 用未公开的 private test；开发集不是最终榜数据。

### 竞赛时 Task 怎么分（选手侧）

| Task | 平台给的资源 | Mock API |
|------|-------------|----------|
| Task 1 | 约 5 页网页 | **不提供** `CRAG_MOCK_API_URL` |
| Task 2 | 约 5 页网页 + Mock KG/API | **提供** |
| Task 3 | 最多 50 页 + Mock API | **提供** |

选手**不需要**自己做 Task1 子集文件；**主办方评测端**按 Task 切题、切环境。

---

## 3. 本地三次基线各自评的是什么？

| 基线 | 类名 | 用 `search_results`（网页） | 用 Mock API（KG） | 大致对应 |
|------|------|---------------------------|-------------------|----------|
| Vanilla | `InstructModel` | ❌ | ❌ | 闭卷对照（非官方 Task1 设定） |
| RAG | `RAGModel` | ✅ | ❌ | Task 1 **方法**（在混合集上） |
| RAG-KG | `RAG_KG_Model` | ✅ | ✅ | Task 2 **方法** |

**注意**：`search_results` 是数据里**预缓存的 HTML**，不是 Mock API。

---

## 4. 本地对比 vs 论文对比：是否统一标准？

### 4.1 Vanilla / RAG / RAG-KG 之间（本地）

**可以统一**，需固定：

- 同一 `DATASET_PATH`（v4 或 v5 二选一，勿混用）
- 同一裁判（如 DeepSeek-V3.2）
- 同一 `local_evaluation*.py`

### 4.2 与论文 Table 对比

**不能当作严格复现**，主要差异：

| 维度 | 论文 | 本地（截至 2026-08-24） |
|------|------|-------------------------|
| 生成模型 | Llama **3** 8B | Llama **3.1** 8B |
| 评测集 | public test **1335** | dev 全量 **2706** |
| 裁判 | GPT-3.5 + Llama-70B 双裁判平均 | DeepSeek-V3.2 单裁判 |
| 任务报告 | 按 Task1/2/3 **分开** | 混合集 **一个总分** |

详见：`docs/论文与本地Vanilla结果对比.md`

### 4.3 Vanilla 全量 2706 是否白跑？

**没有白跑。** 这是「整份 Stage1 dev 闭卷基线」，与 RAG/RAG-KG 在同一混合集上对比仍然有效。  
要对齐论文 **Task 1 单行**：额外做 **RAG + v5 网页子集** 即可，不必重跑 Vanilla。

---

## 5. Task 3 要证明什么？

Task 3 在 **50 页噪声网页 + Mock API** 下评测，核心问题是：

> 在更像真实搜索的难条件下，RAG 还能不能**选对信息、少胡编**？

| | Task 1/2 | Task 3 |
|--|----------|--------|
| 网页数 | ~5 | ~50 |
| 噪声 | 较少 | **很多** |

论文现象（Llama-3-8B）：Task 3 accuracy 更高但 hallucination 也更高——页多能捞到信息，也更容易乱答。

**调研定方向阶段**：Task 1/2 + RAG-KG 足够；Task 3 适合研究**去噪、重排序、多页筛选**时再上。

---

## 6. 本机已跑实验与 Mock API 使用情况

| 实验 | 日志 / 目录 | 模型 | 数据 | Mock API |
|------|-------------|------|------|----------|
| Vanilla 全量 | `logs/eval_deepseek_20260821_225909.log` | `InstructModel` | v5，2706 条 | ❌ |
| RAG-KG 试跑 100 条 | `logs/eval_ragkg_20260824_155105.log` | 日志名似 RAG-KG | `dev_subset_100_random` | ⚠️ 不确定是否启了 mock |
| RAG 全量（进行中/近期） | `logs/eval_ragkg_20260824_161203.log` | **`RAGModel`** | v4 全量 | ❌ |

**当前 `user_config.py`**：`UserModel = RAGModel` → **不会**调用 Mock API。

### 跑通 Task 2（RAG-KG）还需

1. `user_config.py` → `RAG_KG_Model`  
2. 另开终端：`cd mock_api && uvicorn server:app --host 127.0.0.1 --port 8000`  
3. `export CRAG_MOCK_API_URL=http://127.0.0.1:8000`

---

## 7. 建议的本地评测顺序（调研用）

1. ✅ Vanilla 全量（闭卷基线）  
2. ➡️ RAG 全量（与 Vanilla 同集对比）  
3. ➡️ RAG-KG 全量 + Mock API（补 Task 2 能力）  
4. 可选：v5 筛 `popularity==""` + RAG（对齐论文 Task 1 口径）  
5. 可选：Task 3 解压后单独评测（噪声/鲁棒性）

---

## 8. 相关文档索引

| 文档 | 内容 |
|------|------|
| [docs/dataset.md](./dataset.md) | 官方数据模式 |
| [docs/论文与本地Vanilla结果对比.md](./论文与本地Vanilla结果对比.md) | 与论文数字对照 |
| [docs/工作记录/04-项目代码解析.md](./工作记录/04-项目代码解析.md) | 端到端代码与完整例子 |
| [docs/工作记录/05-RAG与RAG-KG基线操作手册.md](./工作记录/05-RAG与RAG-KG基线操作手册.md) | RAG / RAG-KG 操作 |
| [docs/工作记录/03-AutoDL单卡24GB操作手册.md](./工作记录/03-AutoDL单卡24GB操作手册.md) | 环境与依赖 |

---

## 9. 本地路径速查

```text
全量 dev（Task1+2 混合）:
  /root/autodl-tmp/20260820-crag/crag_task_1_and_2_dev_v4.jsonl.bz2
  /root/autodl-tmp/20260820-crag/crag_task_1_and_2_dev_v5.jsonl.bz2

100 条随机子集:
  example_data/dev_subset_100_random.jsonl.bz2

裁判 API 落盘（按实验分子目录）:
  api_responses/eval_<模型>_<时间>_<数据集>/
  或 .env 中 EXPERIMENT_NAME=...
```
