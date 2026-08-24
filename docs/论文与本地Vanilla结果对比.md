# 论文基线 vs 本地 Vanilla 结果对比

> 本地日志：`logs/eval_deepseek_20260821_225909.log`  
> 论文：[CRAG — Comprehensive RAG Benchmark](https://arxiv.org/pdf/2406.04744)（附录 Table 11；正文 Table 5 为摘录）  
> 日期记录：2026-08-22

## 1. 结论（先看这个）

- 仓库里**没有**内置论文数值；下列论文数字摘自 arXiv PDF 附录 **Table 11**。
- 与论文 **LLM-only · Llama-3-8B Instruct** 相比：本地 **更保守**（missing 更高、hallucination 更低），**score 更好看（≈0 vs −10%）**，但 **accuracy 更低**。
- 因模型版本、题集划分、裁判均不同，**不能当作严格复现**；只适合量级与行为对照。

计分关系（auto-eval）：

```text
score / truthfulnessₐ ≈ accuracy − hallucination
（等价于 score = (2×n_correct + n_miss) / n − 1）
```

## 2. 最可比一行：闭卷 LLM-only

| 项 | 论文 Llama-3-8B Instruct | 本地 Vanilla |
|---|---|---|
| 设置 | LLM only（无检索） | Vanilla（无检索） |
| 生成模型 | Llama **3** 8B Instruct | Llama **3.1** 8B Instruct |
| 评测集 | public test **1335** | 约 **2706**（KDD Stage1：validation + public） |
| 裁判 | ChatGPT (gpt-3.5-turbo) + Llama-3-70B **双裁判平均** | 硅基流动 **DeepSeek-V3.2** 单裁判 |
| accuracy | **23.7%** | **15.8%**（427/2706） |
| hallucination | **33.8%** | **16.0%**（432/2706） |
| missing | **42.6%** | **68.3%**（1847/2706） |
| score / truthfulness | **−10.1%** | **≈ −0.18%（≈0）** |

本地原始汇总：

```text
{'score': -0.0018477457501847594,
 'accuracy': 0.15779748706577976,
 'hallucination': 0.15964523281596452,
 'missing': 0.6825572801182558,
 'n_miss': 1847, 'n_correct': 427, 'n_hallucination': 432, 'total': 2706}
```

## 3. 差异原因

| 因素 | 说明 |
|---|---|
| 拒答策略 | 本地 missing 远高于论文 → 少答少扣分 → score 接近 0；论文 8B 更爱答也更爱幻觉 |
| 模型 | 3 vs 3.1，权重与指令遵循不同 |
| 数据 | 1335 public test vs 2706 Stage1 全集，难度分布可能不同 |
| 裁判 | 双裁判平均 vs DeepSeek 单裁判，边界 case 判定会漂 |
| Prompt | 论文 Appendix A.3.1 与仓库 `vanilla_llama_baseline.py` 系统提示并不保证一字相同 |

## 4. 论文里其它常用对照（勿与本地 8B 硬比）

正文常引用的 **更强** LLM-only（仍是 public test + 双裁判）：

| 模型 | Acc | Hall | Miss | Truthfulness |
|---|---|---|---|---|
| Llama-3-**70B** Instruct | 32.3% | 28.9% | 38.8% | **+3.4%** |
| GPT-4 Turbo | 33.5% | 13.5% | 53.0% | **+20.0%** |

论文摘要量级：多数先进 LLM 闭卷 accuracy ≤34%；朴素加 RAG 大约到 44%；工业 SOTA RAG 无幻觉作答约 63%（Table 6 为人评，口径不同）。

## 5. 全量 RAG 跑完后建议对照（论文 Task 1）

论文 **Task 1 · Llama-3-8B**（朴素网页增强，非本仓库 MiniLM 切句检索）：

| Acc | Hall | Miss | Truthfulness |
|---|---|---|---|
| 28.5% | 45.6% | 25.9% | **−17.1%** |

注意：论文 Task1 多为按检索顺序拼接 snippet；仓库 `RAGModel` 为 HTML 切句 + 向量召回。数字只作方向参考——论文里朴素 RAG 常 **抬 accuracy，同时抬 hallucination**。

| Task | Llama-3-8B Acc | Hall | Miss | Truth |
|---|---|---|---|---|
| LLM only | 23.7 | 33.8 | 42.6 | −10.1 |
| Task 1（web） | 28.5 | 45.6 | 25.9 | −17.1 |
| Task 2（web+KG） | 28.6 | 45.5 | 25.9 | −16.9 |
| Task 3 | 32.1 | 56.3 | 11.6 | −24.1 |

## 6. 如何更接近论文数字（可选）

1. 只用 public test（约 1335），不要混 validation。  
2. 裁判尽量贴近论文（GPT + Llama-3-70B 或至少 GPT 系）。  
3. 对照 Appendix A.3.1 的 Vanilla prompt。  
4. 生成侧改用 Llama-3-8B（非 3.1）若要做严格对照。

日常研发不必强行对齐；**同配置下 Vanilla ↔ RAG ↔ 改方法** 的相对差更重要。
