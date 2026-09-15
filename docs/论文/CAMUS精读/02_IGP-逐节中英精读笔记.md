# IGP 逐节中英对照精读笔记（意译）

> **原文**：Song et al. *Less is More for RAG: Information Gain Pruning for Generator-Aligned Reranking and Evidence Selection*. arXiv:2601.17532 · 本地 PDF：[`02_IGP-信息增益剪枝.pdf`](./02_IGP-信息增益剪枝.pdf)  
> **性质**：逐节**意译/转述**精读笔记，**不是**全文照搬对照译；公式与专名保留英文符号。  
> **用途**：服务 CAMUS Related Work / SAFE-U 差界（效用 ≠ 熵减）。  
> **关联**：[`../12-CAMUS精读论文解析.md`](../12-CAMUS精读论文解析.md) · [精读清单](../../工作记录/头脑风暴/20260830-证据效用头脑风暴过程/20260913-CAMUS精读清单.md)

**阅读约定（每节）：**

| EN（paraphrase） | 中文（意译） |
|------------------|--------------|
| 英文侧用自己的话压缩原文论点 | 中文侧对应意译，可直接贴笔记 |

---

## Meta · 题名与关键词

| EN | 中文 |
|----|------|
| Title idea: under a tight context budget, **less (but better-selected) evidence** can beat dumping more relevant passages. | 题眼：预算紧时，**少而选对的证据**可以胜过堆更多「相关」段。 |
| Keywords: LLMs, RAG, reranking, truncation, model uncertainty. | 关键词：大模型、RAG、重排、截断、模型不确定度。 |

---

## Abstract

| EN | 中文 |
|----|------|
| Budgeted RAG’s hard choice is **which** retrieved passages to inject, not just how to retrieve. | 预算受限 RAG 的核心是**选哪些**检索段注入，而不只是检索本身。 |
| Offline relevance (e.g. NDCG) correlates **weakly** with end-to-end QA F1, and can turn **negative** when multiple passages are injected (redundancy / mild conflict). | 离线相关性（如 NDCG）与端到端 F1 **弱相关**；多段注入时甚至可成**负相关**（冗余 / 轻度冲突）。 |
| **IGP** replaces relevance rerank with a **generator-aligned utility**: score by uncertainty reduction, prune weak/negative-utility passages **before** truncate; budget interface unchanged. | **IGP** 用**对齐生成器的效用**替换相关重排：按不确定度下降打分，在 truncate **前**剪掉弱/负效用段；预算接口不变。 |
| Label-free, training-free; needs step-wise logits / TOPK logprobs. On five ODQA sets, better quality–cost trade-off; in a multi-evidence setting ≈ **+12–20%** relative F1 with ≈ **76–79%** fewer final input tokens vs retriever-only. | 无标签、无训练；只需逐步 logits / TOPK logprob。五套开放域 QA 上质量–成本更优；多证据设定约相对 F1 **+12–20%**，终局输入 token 约少 **76–79%**（相对仅检索基线）。 |

**CAMUS 记一笔：** 认同「相关 ≠ 效用」；分歧在效用定义 = **NU↓**，不是约束覆盖 ΔU。

---

## §1 Introduction

### 1.1 Background

| EN | 中文 |
|----|------|
| LLMs still hallucinate without enough support; RAG grounds them via external evidence. | 证据不足时 LLM 仍会幻觉；RAG 用外部证据锚定。 |
| Deployed stack is often **retrieve → rerank → truncate** under Top-M or token budget. | 落地管线常见：**检索 → 重排 → 截断**（Top-M 或 token 预算）。 |

### 1.2 Motivation

| EN | 中文 |
|----|------|
| Multi-passage injection brings redundancy, ambiguity, conflict → wastes budget and destabilizes answers. | 多段注入带来冗余、歧义、冲突 → 浪费预算、答案不稳。 |
| **Relevance ≠ marginal utility for generation.** Highly relevant text can still contain parallel claims / conditions / contradictions that **spread** the next-token distribution. | **相关 ≠ 对生成的边际效用。** 高相关文本仍可含并列主张/条件/矛盾，使 next-token 分布**摊开**。 |

### 1.3 Contribution 1 — Relevance–Utility Mismatch

| EN | 中文 |
|----|------|
| Empirically: NDCG vs F1 Spearman is weak (TopM=1 ≈ 0.11) and can be **negative** (TopM=5 ≈ −0.54) (Fig.1). | 实证：NDCG 与 F1 的 Spearman 在 TopM=1 约 0.11（弱），TopM=5 可约 **−0.54（负）**（图1）。 |
| Mechanism story: injection reshapes token distributions; bad/redundant evidence increases key-token uncertainty. | 机制叙事：注入改写 token 分布；坏/冗余证据抬高关键 token 不确定度。 |
| Therefore shift objective: **optimize evidence utility for generation** = make the generator more concentrated/stable on key tokens (**reduce uncertainty**). | 因此改目标：**优化对生成的证据效用** = 让生成器在关键 token 上更集中/稳定（**降低不确定度**）。 |

### 1.4 Contribution 2 — IGP

| EN | 中文 |
|----|------|
| Plug-and-play **rerank replacement**: build **Normalized Uncertainty (NU)** from step-wise outputs; **IG = NU(no evidence) − NU(with passage)**; rank by IG; threshold-prune; then original truncate. | 即插即用的**重排替换**：用逐步输出建 **NU**；**IG = 无证据 NU − 有该段 NU**；按 IG 排序；阈值剪枝；再走原 truncate。 |
| Only replaces rerank; no labels / training / weights; black-box logits OK. | 只换 rerank；无标签/训练/权重；黑盒 logits 即可。 |

### 1.5 Contribution 3 — Findings

| EN | 中文 |
|----|------|
| Across benchmarks / retrievers / generator scales: better or equal F1 with lower final context cost → stronger Pareto. | 跨基准/检索器/生成器规模：F1 不降或升，终局上下文成本下降 → Pareto 更好。 |
| Gains driven mainly by **admission control (pruning)**, not reordering alone; strongest under multi-passage budgets. | 增益主要来自**准入控制（剪枝）**，而非单靠重排；多段预算下最明显。 |

### 1.6 Paper map

| EN | 中文 |
|----|------|
| §2 related · §3 method (NU/IG/Alg) · §4 experiments · §5 conclusion/limits. | §2 相关工作 · §3 方法 · §4 实验 · §5 结论与局限。 |

**Fig.2 意：** 左相关重排可能留「高相关但有害」；右 IGP 按「是否帮助答这题」滤弱/负增益段。

---

## §2 Related Work

### 2.0 Framing

| EN | 中文 |
|----|------|
| Practical bottleneck: under budget, pick evidence **most helpful for generation**, not merely most relevant. Three literatures: RAG systems, rerank/selection, LLM uncertainty/hallucination UQ. IGP sits at the intersection. | 实践瓶颈：预算下选**最助生成**的证据，而非最相关。三线：RAG、重排/选证、LLM 不确定度/幻觉。IGP 落在交叉处。 |

### 2.1 RAG

| EN | 中文 |
|----|------|
| Classic RAG + dense retrieval (DPR) + FiD-style multi-evidence fusion. High-recall retrieve + strong reader is common—but under fixed Top-M, “relevant” ≠ better end-to-end. | 经典 RAG + 稠密检索 + FiD 多证据融合。高召回+强阅读器常见——但固定 Top-M 下「相关」≠ 端到端更好。 |

### 2.2 Rerank & evidence selection

| EN | 中文 |
|----|------|
| Cross-encoder / MonoT5 / ColBERT / LLM-as-reranker still mostly optimize **relevance**. Authors argue this misses generator-side marginal utility under multi-injection. | Cross-encoder / MonoT5 / ColBERT / LLM 重排大多仍优化**相关性**。作者认为多段注入下错过了生成器侧边际效用。 |

### 2.3 Uncertainty & hallucination

| EN | 中文 |
|----|------|
| Surveys of white-box (entropy, token probs) and black-box (sampling consistency, semantic entropy) UQ; often used **after** generation for confidence / refusal. | 白盒（熵、token 概率）与黑盒（采样一致性、语义熵）UQ 综述；常用在生成**之后**做置信/拒答。 |

### 2.4 Positioning

| EN | 中文 |
|----|------|
| (1) From relevance → **utility = uncertainty reduction**. (2) Control **earlier** at rerank (admit/prune), not only post-answer diagnosis. (3) Deployment-friendly, black-box, only swaps rerank. | (1) 相关 → **效用=不确定度下降**。(2) 在重排阶段**提前**准入/剪枝，而非仅答后诊断。(3) 易部署、黑盒、只换重排。 |

**CAMUS 记一笔：** 他们把 UQ **前移到选证**——方向对；但仍用熵减当效用。我们要 SAFE-U 打「错得更自信」。

---

## §3 Methodology（核心）

### 3.1 Overview

| EN | 中文 |
|----|------|
| Pipeline becomes **retrieve → IGP → truncate**. Useful evidence should make the model more decisive under a fixed probing protocol. | 管线变为 **retrieve → IGP → truncate**。好证据应在固定探测协议下让模型更「敢下结论」。 |
| Score each candidate by IG; prune if IG < \(T_p\); truncate still decides **how many** (Top-M / token guard B). | 对每段算 IG；IG < \(T_p\) 则剪；**段数**仍由 truncate（Top-M / token 护栏 B）决定。 |

**符号速查（Table 1 浓缩）**

| 符号 | 含义 |
|------|------|
| \(q\) | 问题 |
| \(\mathcal{D}=\{d_i\}\) | 一阶段候选 |
| \(\mathcal{L}\) | IGP 重排+剪枝后的列表 |
| \(\mathcal{S}\) | truncate 后最终注入集 |
| \(\phi\) | 生成器（黑盒） |
| \(K\) | TOPK（算 NU 用） |
| \(M_T\) | 探测 rollout 最大长度 |
| \(\widehat{NU}(q)\) / \(\widehat{NU}(q\|d)\) | 无条件 / 有单段条件的归一化不确定度 |
| \(IG(d,q)\) | 信息增益 / 效用代理 |
| \(T_p\) | 剪枝阈值（准入门槛） |

### 3.2 TOPK Normalized Uncertainty (NU)

| EN | 中文 |
|----|------|
| **Deterministic probing:** greedy decode (temperature 0); stop at EOS or \(M_T\); effective length \(T=\min(M_T,T_{\mathrm{EOS}})\). | **确定性探测：** 贪心解码（温度 0）；EOS 或 \(M_T\) 停；有效长度 \(T=\min(M_T,T_{\mathrm{EOS}})\)。 |
| At each step, keep TOPK tokens, **renormalize** softmax over that set only → TOPK entropy \(\tilde H_t\). | 每步只留 TOPK token，在该集合上**重归一化** → TOPK 熵 \(\tilde H_t\)。 |
| Per-step normalized uncertainty \(\tilde u_t=\tilde H_t/\log K\in[0,1]\). | 逐步归一不确定度 \(\tilde u_t=\tilde H_t/\log K\in[0,1]\)。 |
| Sequence NU = average of \(\tilde u_t\) over \(T\) steps (same idea for conditional \(q\|d\)). | 序列 NU = \(T\) 步 \(\tilde u_t\) 平均（条件 \(q\|d\) 同理）。 |

**直觉：** 只看头部竞争 token 的熵，便于黑盒 TOPK API；用步平均减轻长度差异。

### 3.3 Information Gain (IG)

| EN | 中文 |
|----|------|
| \(IG(d,q;\phi,K)=\widehat{NU}(q)-\widehat{NU}(q\|d)\). | 同上公式。 |
| \(IG>0\): passage makes generation more certain; \(IG<0\): may inject noise/conflict and spread mass. | \(IG>0\)：更笃定；\(IG<0\)：可能噪声/冲突、分布摊开。 |
| Authors stress: this is a **ranking proxy**, **not** unbiased mutual information. Goal = stable relative order under fixed prompt/decode. | 作者强调：这是**排序代理**，**不是**无偏互信息估计。目标是固定协议下相对序稳定。 |
| Intuition: high-utility passages sharpen logits on intended tokens → lower TOPK entropy across key steps; conflicting passages flatten competitors → smaller/negative IG. | 直觉：高效用段拉大正确 token 的 logit 间隔 → 关键步 TOPK 熵↓；冲突段摊平竞争 → IG 小或负。 |

**CAMUS 红旗（F6）：** 「更笃定」可以是**错得更自信**。IGP 正文后文 Limitation 自己也承认——这是 SAFE-U 主打点。

### 3.4 Algorithm（Algorithm 1）

| EN | 中文 |
|----|------|
| 1) Compute baseline \(\nu_0=\widehat{NU}(q)\) once. | 1) 无证据基线 \(\nu_0\) 算一次。 |
| 2) For each \(d_i\) (parallel): \(\nu_i=\widehat{NU}(q\|d_i)\), \(s_i=\nu_0-\nu_i\). | 2) 对每段（可并行）算条件 NU，得分 = 差。 |
| 3) Sort by \(s_i\) descending → list \(\mathcal{L}\). | 3) 按得分降序。 |
| 4) Keep only \(IG\ge T_p\). | 4) 阈值剪枝。 |
| 5) \(\mathcal{S}=\mathrm{Truncate}(\mathcal{L};M,B)\). | 5) 原 truncate 出最终集。 |

**Scope：** IGP 管「谁进、谁排前」；不管最终塞几段（仍是 Top-M）。

### 3.5 Implementation notes

| EN | 中文 |
|----|------|
| Probing uses greedy; **final answer decode** can stay at deployment settings. | 探测用贪心；**终答解码**可维持线上配置。 |
| Larger \(T_p\) = more conservative admission; \(T_p\to-\infty\) ≈ pure IG reorder without prune. | \(T_p\) 越大越保守；\(T_p\to-\infty\) ≈ 只按 IG 重排不剪。 |
| Prefer tune \(M_T\) for ranking stability before \(K\); moderate \(K\) (paper default often \(K=128\), \(M_T=32\)). | 先调 \(M_T\) 稳排序，再调 \(K\)；中等 \(K\) 即可（主设定常 \(K=128\), \(M_T=32\)）。 |
| Cost: \(N+1\) probing rollouts / query; parallelizable; same order as YesNo/QLM LLM scorers. | 成本：每查询 \(N+1\) 次探测；可并行；量级同 YesNo/QLM 类 LLM 打分。 |
| **Single-passage IG vs empty context** — does **not** model pairwise redundancy/complementarity; rely on \(T_p\) + Top-M. | **单段相对空上下文**——不显式建模两段冗余/互补；靠 \(T_p\)+Top-M。 |

**CAMUS 记一笔：** 我们用约束覆盖边际 + 冗余惩罚，正是补「集合交互 / 名单膨胀」；IGP 自己把 set-aware 留到 Future Work。

---

## §4 Experiments

### 4.0 Research Questions

| RQ | EN | 中文 |
|----|----|------|
| RQ1 | Quality–cost frontier vs budgets? | 不同预算下质量–成本前沿？ |
| RQ2 | Gains from reorder vs prune? Sensitivity to \(T_p,K,M_T\)? | 增益来自重排还是剪枝？超参敏感？ |
| RQ3 | Does NDCG predict F1? | NDCG 能否预测 F1？ |
| RQ4 | Robust across retrievers? | 换一阶段检索器还稳吗？ |
| RQ5 | Robust across generator family/scale? | 换生成器族/规模还稳吗？ |

### 4.1 Setup（浓缩）

| EN | 中文 |
|----|------|
| Corpus: FlashRAG Wikipedia 2018-12-20, ~100-word chunks, ~21M passages. | 语料：FlashRAG Wiki 快照，约 100 词切块，约 2100 万段。 |
| Datasets: NQ, TriviaQA, PopQA (test); SQuAD, AmbigQA (dev if no test). | 数据：NQ/TriviaQA/PopQA（test）；SQuAD/AmbigQA（无 test 用 dev）。 |
| Main generator: Qwen2.5-7B-Instruct via vLLM; also Qwen 0.5–7B & Llama-3.x 1B/3B/8B for RQ5. | 主生成器：Qwen2.5-7B-Instruct（vLLM）；RQ5 再扫规模与 Llama 族。 |
| Two prompts: (A) grounded final QA; (B) short neutral probe for NU/IG (uncond: question only; cond: + single Context). | 两套提示：(A) 终答接地；(B) 短中性探测（无条件仅问题；有条件加单段 Context）。 |
| Baselines: BM25 / Contriever retrieve; CE, BGE, YesNo, QLM rerank; **+IG** = IG sort without prune; **IGP(\(T_p\))**. | 基线：BM25/Contriever；CE/BGE/YesNo/QLM；**+IG** 只排序不剪；**IGP(\(T_p\))**。 |
| Metrics: token F1; **TK** = avg final-stage input tokens; **NTE** = relative (F1/TK) vs retriever-only; NDCG only for analysis. | 指标：token F1；**TK** 终局输入 token；**NTE** 相对仅检索的 (F1/TK)；NDCG 仅分析用。 |

### 4.2 Main results (RQ1)

| EN | 中文 |
|----|------|
| **TopM=5:** relevance rerank / YesNo / QLM / **+IG** barely change TK (five slots still filled) → F1 gains tiny. **IGP with threshold** cuts TK a lot and lifts avg F1. | **TopM=5：** 相关重排 / YesNo / QLM / **只 IG 排序**几乎不改 TK（五席仍满）→ F1 增益很小。**带阈值的 IGP** 大幅降 TK 并抬平均 F1。 |
| **TopM=1:** picking the single decisive passage matters; IGP improves F1 and can still lower TK by rejecting ambiguity-inducing passages. | **TopM=1：** 选「一锤定音」段更关键；IGP 抬 F1，并可因拒歧义段而降 TK。 |
| Pareto (Fig.3): IGP shifts upper-left vs BM25+conventional rerankers. | Pareto（图3）：相对 BM25+常规重排，IGP 曲线左上移。 |

> **概念笔记：** [Pareto-frontier读论文笔记.md](./Pareto-frontier读论文笔记.md)（质量–成本前沿怎么读、和 IGP/CAMUS 的关系）

**机制金句（转述）：** 多证据时瓶颈常不是召回，而是**预算下该放谁进来**；剪枝才是主杠杆。

### 4.3 Ablation (RQ2)

| EN | 中文 |
|----|------|
| Pruning threshold \(T_p\) has a stable sweet spot; too aggressive hurts coverage. | \(T_p\) 有稳定甜点；过严伤覆盖。 |
| Larger \(M_T\): gains rise then plateau (need enough steps to average entropy). | \(M_T\) 增大：增益先升后平台（需要足够步数平均熵）。 |
| Very small \(K\) hurts; moderate \(K\) enough. **Prioritize \(M_T\) before \(K\)**. | \(K\) 太小伤性能；中等即可。**先稳 \(M_T\) 再调 \(K\)**。 |

### 4.4 Extra analyses (RQ3–RQ5)

#### RQ3 Relevance ≠ utility

| EN | 中文 |
|----|------|
| Controlled NQ subset with BEIR relevance labels (2724 q): higher NDCG ≠ higher F1; mismatch worse at TopM=5. | 带 BEIR 相关标注的 NQ 子集（2724 题）：NDCG 高 ≠ F1 高；TopM=5 错配更重。 |
| **IGP(0.05) can have lower NDCG but higher F1** than relevance rerankers — smoking gun for mismatch. | **IGP(0.05) 可 NDCG 更低但 F1 更高**——相关–效用错配的直接证据。 |

#### RQ4 Retriever robustness

| EN | 中文 |
|----|------|
| Switch BM25 → Contriever: same qualitative story—IGP still upper-left on Pareto; prune still dominates at TopM=5. | 换 Contriever：故事同质——IGP 仍左上；TopM=5 仍是剪枝主导。 |

#### RQ5 Generator family/scale

| EN | 中文 |
|----|------|
| Under TopM=1 on NQ: **small model + IGP can beat larger model without IGP** (e.g. Qwen1.5B+IGP > Qwen7B w/o IGP in their Fig.7 narrative). | TopM=1、NQ：**小模型+IGP 可胜过无 IGP 的更大模型**（文中图7叙事：如 Qwen1.5B+IGP > Qwen7B 无 IGP）。 |
| w/ IGP curves roughly log-linear in size; gains hold for Qwen2.5 and Llama-3.x. | 有 IGP 时 F1–规模近似 log-linear；两族都有增益。 |

### 4.5 Takeaways（五条）

1. RQ1：剪枝带来质量–成本双赢；只重排不够。  
2. RQ2：主因是准入控制；\(T_p\) 有甜点；\(M_T\) 比 \(K\) 更影响排序稳定。  
3. RQ3：NDCG 弱/负相关 F1 → 相关 ≠ 效用。  
4. RQ4：换检索器仍成立。  
5. RQ5：跨族跨规模；证据准入可补偿部分模型规模。

---

## §5 Conclusion / Practice / Limits

### 5.1–5.2 Findings & deployment

| EN | 中文 |
|----|------|
| Budgeted RAG = **evidence admission-control** under fixed cost. | 预算 RAG = 固定成本下的**证据准入控制**。 |
| Easy A/B: swap only rerank policy; \(T_p\) is the main quality–cost knob. | 易 A/B：只换重排策略；\(T_p\) 是主旋钮。 |
| Works best when candidates are near-paraphrases or differ in conditional/numeric scope (enterprise KB, support, manuals). | 候选近释义或条件/数字范围不一致时最有效（企业知识库、客服、手册）。 |
| Fallbacks: if too few pass \(T_p\), fall back to relevance or disable prune; or enable IGP only when baseline \(\widehat{NU}(q)\) is high. | 回退：通过率过低则退回相关重排/关剪枝；或仅在基线 \(\widehat{NU}(q)\) 高时开 IGP。 |
| Monitor IG distribution drift when corpus/prompt changes. | 语料/提示变更时监控 IG 分布漂移。 |
| Probing costs extra but parallelizable; final TK drop often dominates generation cost. | 探测有额外成本但可并行；终局 TK 下降常主导生成成本。 |

### 5.3 Limitations（对 CAMUS 最重要）

| EN | 中文 |
|----|------|
| Uncertainty reduction **≠ correctness**. Misleading-but-confident evidence can **lower NU**. Treat IG as utility proxy, not truth. Suggest pairing with reliability / consistency / post-check. | 不确定度下降 **≠ 正确性**。误导但自信的证据也能 **降低 NU**。IG 是效用代理不是真值。建议加可靠性/一致性/答后核查。 |
| Single-passage vs empty baseline **misses multi-evidence interactions** (redundancy & complementarity). Future: set-aware / conditional IG / submodular+dedup. | 单段对空基线 **忽略多证据交互**（冗余与互补）。未来：集合感知 / 条件 IG / 次模+去重。 |

**附录 A 插图意（转述）：** 「1GB 有多少 MB」——相关但啰嗦/混单位的 Doc 可能相关分高却让模型更糊；简洁对齐单位体系的 Doc 更「有用」。再证相关 ≠ 效用。

---

## 与 CAMUS 差界卡（写 Related Work 用）

| 轴 | IGP | CAMUS |
|----|-----|-------|
| 问题转向 | 相关 ≠ 生成效用 ✅ 同向 | 同；再加 CRAG 噪声 / `rag_worse` |
| 效用键 | \(\Delta\) 不确定度（熵减 IG） | **约束覆盖边际效用 − 冗余 − 有害代理** |
| 风险 | 误导句可 NU↓（作者自承） | **SAFE-U**：同池对比 IG vs ΔU，盯错误自信 |
| 集合交互 | 单段 vs 空；future work | 贪婪边际 + 早停，显式打冗余/名单 |
| 落地 | 无训、黑盒、\(N+1\) 探测 | 无训规则为主；不必每段 rollout 熵（成本形态不同） |
| 评测舞台 | Wiki ODQA + token F1/TK | CRAG 网页噪声 + accuracy/score/`rag_worse` |

**可粘贴 4 句：**

> IGP 把预算 RAG 改写为「生成器对齐的证据准入」，并用不确定度下降定义效用，实证显示 NDCG 与 F1 在多段预算下可负相关——我们认同「utility ≠ relevance」。  
> 但 IGP 默认「分布更尖 = 更好证据」；其 Limitation 也承认误导证据可降低不确定度。  
> CAMUS 因此拒绝把 utility 等同于 information gain，改用**问题约束覆盖的边际效用**选证，并以 SAFE-U 强制报告 IG 排序在 `rag_worse` 上是否劣于约束 ΔU。  
> 另：IGP 的单段–空上下文打分不显式建模集合冗余；CAMUS 的贪婪 ΔU + 冗余项针对名单膨胀与多句拼装。

---

## 速记一张纸

```text
IGP = retrieve → (按 IG= NU∅−NU|d 排序 + Tp 剪枝) → 原 Top-M truncate
卖点：相关–效用错配；剪枝>重排；降 TK 抬/保 F1；黑盒无训
要命缺口：NU↓ ≠ 答对；单段忽略集合交互
我们：约束 ΔU + SAFE-U 打熵减；CRAG / rag_worse 舞台
```

---

## 源码与数据能否获取（2026-09-14 核验）

**结论：** 官方 **IGP 源码未见公开**；论文用的 **评测集与 Wiki 检索语料可从公开渠道获取**。CAMUS 做 SAFE-U **不必**等官方仓、也不必先搬整库。

### 源代码

| 项 | 状态 |
|----|------|
| PDF / [arXiv:2601.17532](https://arxiv.org/abs/2601.17532) | **无** GitHub / 补充材料 / code 链接 |
| 公开检索（HF Papers、Awesome-RAG 等） | 仅挂论文，**未见**作者官方实现 |
| 性质 | 2026-01 Elsevier preprint，算法写清、代码未放属常见情况 |
| 若需官方实现 | 可邮件作者（文内如一作 `songzhipeng@mail.dlut.edu.cn`、通讯 `hengqi@dlut.edu.cn`） |

**对本项目：** SAFE-U 对照只需自实现「IG = NU∅ − NU\|d → 排序/剪枝」——§3 + Algorithm 1 已够；舞台是 CRAG + 本地 8B，不是复现其 Wiki ODQA 主表。

### 数据集与语料（论文设定，公开）

| 组件 | 能否获取 | 入口 / 说明 |
|------|----------|-------------|
| Wiki 检索语料 | ✅ | FlashRAG：`https://huggingface.co/datasets/RUC-NLPIR/FlashRAG_datasets`（文内脚注：`retrieval-corpus/wiki18_100w.zip`，约 100 词切块、~21M passages） |
| NQ / TriviaQA / PopQA | ✅ | 官方或 HF；常用 test 分割 |
| SQuAD / AmbigQA | ✅ | 无公开 test 时论文用 **dev** |
| 生成器 | ✅（需许可） | Qwen2.5-Instruct、Llama-3.x-Instruct（HF） |
| 重排基线权重/实现 | ✅ | BM25、Contriever、BGE、MS MARCO 微调 MiniLM CE、YesNo/QLM 提示打分等 |

**体积提醒：** Wiki 切块语料与索引很重。若只为 CAMUS 差界，优先在 **本地 CRAG 200 子集** 上跑 IG 排序 vs 约束 ΔU，不必先下载整库。

### 与 FlashRAG 工具包

论文检索语料来自 FlashRAG（Jin et al., 2024）；FlashRAG 本身是模块化 RAG 工具包，**≠ IGP 官方实现**。可用其语料/管线搭脚手架，IGP 模块仍需按论文自写。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-09-14 | 初稿：据 PDF + 本地 `_extract` 意译；非整篇对照全文 |
| 2026-09-14 | 增补「源码与数据能否获取」核验结论 |
