# CAMUS 精读：论文解析

**解读日期**：2026-09-13  
**PDF 目录**：[`CAMUS精读/`](./CAMUS精读/)（01–17）  
**对照清单**：[20260913-CAMUS精读清单.md](../工作记录/头脑风暴/20260830-证据效用头脑风暴过程/20260913-CAMUS精读清单.md)  
**创新审查**：[05-创新性审查.md](../工作记录/头脑风暴/20260830-证据效用头脑风暴过程/05-创新性审查.md)  
**本地主线**：CAMUS = 生成前 **约束覆盖边际效用** 选证（≠ cosine / ≠ 熵减 IG / ≠ RL 最小充分集）

每篇统一四行：

```text
设定 / 方法 / 没覆盖我们 / 我们可增量
```

---

## 〇、为何读、读什么

| 本地证据 | 文献要回答的问题 |
|----------|------------------|
| `rag_worse≈25`：Vanilla 对、RAG 幻觉 | 不完美检索如何伤「已会答」题？ |
| cosine/`max_score` 与对错脱钩 | relevance ≠ answer utility？ |
| 固定 top-20 | 如何选 / 何时停，而不是堆相关句？ |
| SAFE-U 主张 | **熵减 IG** 是否可能 ≠ 正确性？ |

**差界三轴（写 Related Work 钉死）：**

1. ≠ 固定 top-k / cosine / MMR  
2. ≠ 熵减 / Document Information Gain（IGP、InfoGain-RAG…）  
3. ≠ RL / 重训选择器（Context-Picker、RAG-CSM…）

### 差界三轴 · 通俗说明

审稿人问「这不就是××吗」时，钉死三句：**我们选证据的标准，跟这三类都不一样。**

同一道题想：*「2017 年之后的皮克斯电影有哪些？」* 检索出 20 句，混着相关但害人的（如把 Toy Story 4 塞进来）。

| 轴 | 别人怎么选 | 问题在哪 | CAMUS 差在哪 | 一句话 |
|----|------------|----------|--------------|--------|
| **1** ≠ top-k / cosine / MMR | 谁跟问题「长得像」就留谁，前 10/20 全塞 | 像 ≠ 有用；噪声句也可以很像，照样带偏 | 不按「像不像」堆句，看是否**盖住问题硬约束**（年份、名单边界等） | **相关分排序 ≠ 答题有没有用** |
| **2** ≠ 熵减 / IG（IGP 等） | 加这句话后模型「更笃定」（熵↓ / IG↑）→ 当好证据 | 误导句也能让模型**错得更自信** | 用约束覆盖 ΔU，不是「慌不慌」；**SAFE-U** 同池对比 IG vs ΔU | **模型更自信 ≠ 答案更对** |
| **3** ≠ RL / 重训选择器（Context-Picker 等） | 也要「少而够」子集，但用 RL / LOO **训选证模型** | 要训练、多前向；8B 无训、周内难落地 | 同样反对固定 Top-K，落地为**无训练贪婪 ΔU + 早停** | **最小充分可同想，落地是规则不是再训 picker** |

**记忆锚：** 轴1 → 朴素 RAG/重排；轴2 → **IGP**；轴3 → **Context-Picker**。  
Astute 偏「答时如何融合内外知识」，不是这三轴里的「选句标准」——另写干预点不同即可（见下 #1）。

白话版亦见：[CAMUS是什么-白话说明 · 差界三轴](../工作记录/头脑风暴/CAMUS是什么-白话说明.md#差界三轴写-related-work用)。

---

# ★ 必读（差界骨架）

## #1 · Astute RAG — 不完美检索与知识冲突

**原文**：Wang et al. *ASTUTE RAG: Overcoming Imperfect Retrieval Augmentation and Knowledge Conflicts for LLMs*. ACL 2025 / arXiv:2410.07176  
**本地**：`01_AstuteRAG-不完美检索与冲突.pdf`（同 `11_AstuteRAG-…`）

### 设定

不完美检索（无关 / 误导 / 恶意）几乎不可避免；**LLM 内部知识 vs 外部检索**冲突是 post-retrieval 瓶颈。最坏情况下，朴素 RAG 可劣于无检索。

### 方法

1. 自适应引出内部知识；  
2. **源感知**迭代整合内外段落（一致合并、冲突分开、滤无关）；  
3. 按可靠性定最终答案。  
训练无关、偏 **生成阶段知识整合 / 通道路由**，不是句级选证排序。

### 没覆盖我们

- 不定义「约束覆盖 ΔU」，也不在 MiniLM top-N 上做早停选句。  
- 主叙事是 **内部↔外部冲突消解**，不是 CRAG 嘈杂 HTML 上 cosine 高分句的 **负答题效用**。  
- 不对比「熵减 vs 正确性」。

### 我们可增量

用同一现象（检索伤人 / `rag_worse`）作动机，但贡献落在 **答前选证 + 边际效用早停**；明确 **不做** Astute 式闭卷融合主贡献（与轨 A W1 叙事分开）。

### 差界 3–5 句（可直接贴 Related Work）

Astute RAG 证明不完美检索与内外知识冲突会严重损害 RAG，并通过源感知整合在最坏情况下追平甚至超过无检索 LLM。我们的设定共享「检索可伤害原本可答的问题」，但干预点不同：CAMUS 只改生成前喂给模型的证据集合，用约束覆盖的边际效用做贪婪选择与早停，而不是迭代融合内部生成段落与外部页。因此我们不对齐 Astute 的「知识整合器」叙事，而把 `rag_worse` 解释为 **高相似噪声句 / 集合交互进入 context** 的结果。实验上我们用 CRAG 网页子集与桶级流转表验证选证，而非强调与闭卷答案的多轮巩固。

---

## #2 · IGP — Information Gain Pruning（撞车最高）

**原文**：Song et al. *Less is More for RAG: Information Gain Pruning…*. arXiv:2601.17532  
**本地**：`02_IGP-信息增益剪枝.pdf`

### 设定

预算受限的 retrieve→rerank→truncate；**NDCG 等相关性与端到端 F1 弱相关，多段注入时甚至负相关**（与我们 cosine 脱钩一致）。

### 方法

- 用生成器逐步输出构造 **归一化不确定度 NU**；  
- **IG = 注入该 passage 后 NU 的下降**；  
- 按 IG 重排，阈值剪掉弱/负效用段，再 truncate。  
- **无标签、无训练、只需 top-k logprob**；不改预算接口。

### 没覆盖我们

- 效用 = **不确定度下降**，不是约束覆盖，也不是「答对概率」。  
- 未针对 **F6：有害证据提高错误自信**（NU↓ 但答案更错）做证伪。  
- 非 CRAG 嘈杂网页 / `rag_worse` 桶叙事。

### 我们可增量（SAFE-U 核心）

主张并实验：**答对效用 ≠ 熵减**。同一候选池上对比 IG 排序 vs 约束 ΔU；若 `rag_worse` 上 IG 救助弱于 CAMUS，则差界成立。

### 差界 3–5 句

IGP 将证据效用操作化为生成器不确定度的降低，并显示相关性排序在多证据预算下可伤害端到端质量——这一点我们认同。但 IGP 默认「更尖的生成分布 = 更好证据」；在网页噪声与名单膨胀设定下，误导句也可降低熵、提高错误自信。CAMUS 因此采用 **约束覆盖边际效用 − 冗余 − 有害代理** 作为选证键，并以 SAFE-U 对照强制报告 IG 排序在 `rag_worse` 上是否劣于约束 ΔU。换言之，我们保留「utility ≠ relevance」的转向，但拒绝把 utility 等同于 information gain。

---

## #3 · Context-Picker — RL 最小充分子集

**原文**：Zhu et al. *Context-Picker: Dynamic Context Selection Using Multi-stage RL*. arXiv:2512.14465  
**本地**：`03_ContextPicker-最小充分子集.pdf`

### 设定

长上下文 QA：Top-K 增大 recall 不单调提升 accuracy；问题应是 **子集选择**，不是固定深度排序。

### 方法

- 目标：学到 **可变长度的最小充分证据集**；  
- 两阶段 RL：先召回、再剪冗余；  
- 离线用生成器–裁判 + **Leave-One-Out** 挖最小充分集作稠密监督。

### 没覆盖我们

- 需要 **训练 RL 策略 + LOO 蒸馏**，48h / 竞赛时延不友好。  
- 充分性由「答对/可答」裁判定义，不是显式 **query 约束原子覆盖**。  
- 非 CRAG HTML 噪声与 `rag_worse` 流转表。

### 我们可增量

共享「最小充分 / 可变 |E|」表述，但落地为 **training-free 贪婪 ΔÛ**；用规则 CovGain 近似充分性，保留可部署性。

### 差界 3–5 句

Context-Picker 将上下文选择表述为最小充分子集，并用两阶段 RL 与 LOO 蒸馏学习「选哪些、选多少」。我们同样反对固定 Top-K，但采用无训练的约束边际效用贪婪与早停，避免策略训练与多前向 LOO 成本。充分性在我们这里优先操作化为 **问题约束原子的覆盖增益**，以便在无裁判标签的推理路径上运行，并用 CRAG 子集上的 `rag_worse`/`rag_helps` 流转检验副作用。因此 CAMUS 是「最小充分」思想的 **规则可部署实例**，而非 RL 选择器复现。

---

# ○ 紧接（Related Work / 消融叙事）

## #4 · InfoGain-RAG — Document Information Gain

**原文**：Wang et al. EMNLP 2025 · **本地**：`04_InfoGainRAG-….pdf`

| | |
|--|--|
| **设定** | 难判断检索文档是否真正帮助「正确答案」生成 |
| **方法** | **DIG** = 有/无该文档时 LLM **生成置信**之差；用 DIG 训专用 reranker 过滤/排序 |
| **没覆盖我们** | 仍是置信/信息增益族；需训练；非约束覆盖；非 `rag_worse` |
| **可增量** | 与 IGP 并列支撑 SAFE-U：「增益」文献已挤，我们必须钉 **约束 ΔU ≠ DIG/IG** |

---

## #5 · GainRAG — 增益对齐选段

**原文**：ACL 2025 · **本地**：`05_GainRAG-….pdf`

| | |
|--|--|
| **设定** | 段落对生成的「gain」与偏好对齐 |
| **方法** | 学 gain/偏好信号做选段（扫方法节即可） |
| **没覆盖我们** | 非规则约束边际；训练依赖 |
| **可增量** | Related Work 一句：效用定义不同（偏好/gain vs CovGain−Harm） |

---

## #6 · RECOMP — 检索压缩

**原文**：ICLR 2024 / arXiv:2310.04408 · **本地**：`06_RECOMP-….pdf`

| | |
|--|--|
| **设定** | 检索文档过长、贵 |
| **方法** | 压成摘要或抽句子再增强 |
| **没覆盖我们** | 优化「相关可压内容」，不显式惩罚负效用/约束缺口 |
| **可增量** | 消融对照：压缩/抽句 ≠ 约束边际选证 |

---

## #7 · Provence — 现代上下文剪枝

**原文**：ICLR 2025 / arXiv:2501.16214 · **本地**：`07_Provence-….pdf`

| | |
|--|--|
| **设定** | 跨域、变长上下文上剪枝器泛化不足 |
| **方法** | 高效句级剪枝（常与重排统一） |
| **没覆盖我们** | 仍偏 **相关性/可答支持的剪枝**，不是约束 ΔU 与有害代理 |
| **可增量** | 「动态 k / 剪枝」基线族；准则换成 CAMUS 分数 |

---

## #8 · SEAL-RAG — 预算内替换

**原文**：arXiv:2512.10787 · **本地**：`08_SEALRAG-….pdf`

| | |
|--|--|
| **设定** | 固定预算下低效用段占位 |
| **方法** | **training-free**：「替换，不要只追加」控制器 |
| **没覆盖我们** | 非约束覆盖主目标 |
| **可增量** | 一句区分：我们允许 ΔU≤0 **永不加入**；SEAL 强调预算内置换策略 |

---

# 补齐 `05` 点名（扫读）

## #9 · Corrective RAG（Yan）

**本地**：`09_CorrectiveRAG-….pdf` · arXiv:2401.15884  

检索质量评估 → Correct / Incorrect / Ambiguous；可触发 **web 再检索** + decompose-then-recompose。  
**差界**：我们无 web；只在已有 HTML 候选上做页内效用选择。**勿与 CRAG Benchmark 简称混淆。**

## #10 · Self-RAG

**本地**：`10_SelfRAG-….pdf`  

Reflection tokens：要不要检索、是否支持。偏 **训练侧批判生成**。  
**差界**：我们不主打生成后反思 token；主刀在答前选证。

## #11 · Adaptive-RAG

**本地**：`11_AdaptiveRAG-….pdf` · arXiv:2403.14403  

按问题复杂度路由：无检索 / 单步 / 多步。  
**差界**：改的是检索深度策略，不是证据集合的约束 ΔU；QAP 若只改 k 会被打成此类。

## #12 · LongLLMLingua

**本地**：`12_LongLLMLingua-….pdf` · arXiv:2310.06839  

按困惑度等做 **提示压缩**，提高信息密度。  
**差界**：压缩密度 ≠ 答题正效用 / 有害识别。

## #13 · RAG-CSM（Influence Guided）★紧接必扫

**本地**：`13_RAGCSM-….pdf` · arXiv:2509.21359 · NeurIPS 2025  

| | |
|--|--|
| **设定** | 噪声上下文；query/list/generator 单维指标不够 |
| **方法** | **CI value** = 去掉该上下文后效用下降（leave-one-out 影响）；正 CI 保留；训 **CSM** 代理以免推理要标签与多次前向 |
| **没覆盖我们** | 需训代理；效用常 EM/F1（训练可见标签）；非约束原子；算力重 |
| **可增量** | 形式最贴「边际效用」；我们用 **可计算的 CovGain−Harm 代理** 换可部署，并承认 CI/CSM 是学习版上界叙事 |

**一句差界**：RAG-CSM 学的是生成质量意义下的上下文影响；CAMUS 在无 CSM 训练预算下用约束覆盖近似边际贡献，并显式加入有害启发式以打 `rag_worse`。

## #14 · Zero-RAG

**本地**：`14_ZeroRAG-….pdf` · arXiv:2511.00505  

| | |
|--|--|
| **设定** | 语料与 LLM 知识冗余；**对已掌握题加冗余检索会掉点**（≈我们的 `rag_worse` 现象同族） |
| **方法** | Mastery-Score 剪语料 + Query Router + Noise-Tolerant Tuning |
| **没覆盖我们** | 主攻 **语料剪枝与路由**，不是单题 top-N 句级约束选证 |
| **可增量** | 动机可引「检索可伤害已会答」；方法落点不同（库级 vs 题级 context） |

## #15 · QUBO Evidence Selection

**本地**：`15_QUBO-….pdf` · arXiv:2607.12334  

把证据选择写成 QUBO：相关、需求覆盖、支持、冗余、互补、紧凑；求解器选子集。  
**差界**：目标式接近 set-level U(E)；我们用 **贪婪规则** 而非量子/Ising 求解器；设定 HotpotQA 非 CRAG 网页。

## #16 · Robust RALM（NLI 滤无关）

**本地**：`16_RobustRALM-….pdf` · arXiv:2310.01558（Yoran et al.）  

NLI 滤掉与 QA 无关段落；或训模型在无关上下文下稳健。  
**差界**：滤的是「无关」，难打「相关但缺约束 / 负效用」；作组件级对照即可。

## #17 · CER（UNVERIFIED）

**本地**：`17_CER-…-UNVERIFIED.pdf`  

摘要称：反事实删改监督 + 因果重排 + 最小充分集搜索。  
**警告**：发表渠道可疑，**勿当高置信先验**；若写 Related Work，仅作「因果充分集」方向一句，并标注未核验。  
与 CAMUS：同「充分/必要」语汇，但我们不依赖其监督管线。

---

## 总表：与 CAMUS 的距离

| # | 论文 | 距 CAMUS | 用途 |
|---|------|----------|------|
| 1 | Astute | 近（现象）/ 远（方法） | 动机；避融合叙事 |
| 2 | IGP | **最近撞车** | SAFE-U 对照 |
| 3 | Context-Picker | 近（MSE）/ 远（RL） | 最小充分差界 |
| 4 | InfoGain-RAG | 撞车族 | 与 IGP 一起 |
| 5 | GainRAG | 中 | 效用定义一句 |
| 6 | RECOMP | 中 | 压缩对照 |
| 7 | Provence | 中 | 剪枝对照 |
| 8 | SEAL-RAG | 中 | 替换 vs 拒加 |
| 9 | Corrective | 远 | 无 web |
| 10 | Self-RAG | 远 | 非反思主刀 |
| 11 | Adaptive-RAG | 中 | 反 QAP 换皮 |
| 12 | LongLLMLingua | 远 | 压缩≠效用 |
| 13 | RAG-CSM | **近（ΔU 形式）** | 学习版对照 |
| 14 | Zero-RAG | 近（现象） | 伤已会答题 |
| 15 | QUBO | 近（集合目标） | set-level 一句 |
| 16 | Robust RALM | 远 | NLI 组件 |
| 17 | CER | ? | UNVERIFIED |

---

## Related Work 骨架（可改数后贴开题）

> Retrieval quality and end-to-end utility can diverge under multi-evidence budgets (IGP; our cosine diagnostics). Robust RAG either consolidates internal/external knowledge (Astute), compresses or prunes by relevance (RECOMP, Provence), filters by NLI (Robust RALM), routes by complexity (Adaptive-RAG), or learns set policies (Context-Picker, RAG-CSM, InfoGain-RAG). These lines do not jointly (i) operate as training-free selection on noisy web snippets, (ii) define utility as **constraint-coverage marginal gain minus harm**, and (iii) evaluate with a **Vanilla-correct / RAG-wrong** bucket. We propose CAMUS for this gap, and use SAFE-U to test that uncertainty reduction is an inadequate surrogate for answer utility on retrieval-harm cases.

---

## 贡献句（读后修订稿）

在 CRAG 嘈杂网页设定下，语义相似度高的句子仍可能具有负的答题效用（`rag_worse`）。既有工作或用知识整合（Astute）、或用熵减/置信增益（IGP / InfoGain）、或用 RL/影响模型学最小充分集（Context-Picker / RAG-CSM）。**CAMUS** 以 **约束覆盖的边际效用**（而非 cosine / 熵减）在生成前做证据选择与早停；**SAFE-U** 用于证伪「不确定度下降 = 有用证据」。

---

## 勾选（对应清单 §4）

- [x] Astute 差界 3–5 句  
- [x] IGP 差界 3–5 句  
- [x] Context-Picker 差界 3–5 句  
- [x] ○ 区 + `05` 补齐篇目扫完并入 Related Work 草稿  
- [ ] （并行）CAMUS 第 1 周：200 子集四指标 + 流转表反写本文数字  

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-09-13 | 首版：基于 `CAMUS精读/` 01–17 PDF 抽取精读/扫读 |
