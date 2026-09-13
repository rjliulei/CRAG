# CAMUS 是什么（白话说明）

> 写给「名字和公式都看不懂」时读。  
> 正式定义与实验细节：[06-最终研究决策](./20260830-证据效用头脑风暴过程/06-最终研究决策.md) · [研究计划](./20260911-CAMUS研究计划.md) · [第1周步骤](./20260912-CAMUS第1周执行步骤.md)

---

## 一句话

**CAMUS 不是新模型，是「喂给 LLM 之前，换一种挑句子的办法」。**

只改「从检索结果里选哪几句放进 prompt」；后面的 Llama、裁判、数据集都不变。

英文全称：**C**onstraint-**A**ware **M**arginal **U**tility **S**election（约束感知的边际效用选证）。

---

## 原理（为什么要换挑法）

### 被打穿的旧假设

现有 RAG（`rag_llama_baseline.py`）隐含：

```text
相似度高 → 证据好 → 答得对
```

本地 200 子集上实际是：

```text
相似度高 → 只说明主题沾边
         → 仍可能缺约束 / 名单诱导 / 句间冲突
         → 固定 top-20 反而把模型带偏（rag_worse ≈ 25）
```

瓶颈不在「检索不到」，而在 **生成前不会分辨：这段对答对是加分还是减分**。

### CAMUS 换的决策规则

对每个**尚未选中**的候选句，相对**已经选中的集合 \(E\)** 算边际分：

\[
\Delta U(e \mid E, q)
\approx \underbrace{\mathrm{CovGain}}_{\text{新覆盖了几个约束}}
- \lambda\cdot\underbrace{\mathrm{Redundancy}}_{\text{与已选句有多像}}
- \gamma\cdot\underbrace{\mathrm{HarmProxy}}_{\text{有害启发式}}
\]

| 项 | 白话 | MVP 怎么估（规则即可） |
|----|------|------------------------|
| CovGain | 这句有没有**新**满足问题约束？ | 问题抽实体/年份/set 标记；句里命中未覆盖约束 → +1 |
| Redundancy | 和已选句是不是近重复？ | 与 \(E\) 中句的最大 cosine；越高扣越多 |
| HarmProxy | 很像但零增益？像名单罗列？冲突？ | 高 sim 且 CovGain=0；set 题列表诱导等 |

- \(\Delta U\) **大** → 值得加进来  
- \(\Delta U \le \varepsilon\)（或变负）→ **停**，不再硬塞  
- 句数上限 budget \(B\)（如 8），防止无限加  

这叫 **边际效用**：看「再加这一句还值不值」，不是「单独和问题像不像」。

```text
cosine（像不像）  ≠  ΔU（对答对的边际好处）
```

---

## 贪婪挑选具体如何实现

「贪婪」= **每一步只选当前 \(\Delta U\) 最高的那一句**，加进去后重新算剩余句的分，再选下一句；**不回头撤销**已选句。  
不追求全局最优（枚举所有子集太贵），用「一步步取当前最好」近似。

### 输入 / 输出

| | 内容 |
|--|------|
| **输入** | 问题 \(q\)；候选句集合 \(C\)（cosine 之后的相关句，可先保留 ≥20）；每句已有 cosine；预算 \(B\)；阈值 \(\varepsilon,\lambda,\gamma\) |
| **输出** | 选中子集 \(E^*\)（通常 \(|E^*| \le B\)，往往远小于 20） |
| **插入点** | `rag_llama_baseline.py` L323–326：原来 `argsort` 截 top-20 的地方，改成调用本算法 |

### 伪代码（与决议一致）

```text
Input: q, candidates C, cosine_scores, budget B, ε, λ, γ

1.  constraints ← ParseConstraints(q)
    # 例：实体词、年份、是否 set 题

2.  E ← ∅                 # 已选集合，一开始为空

3.  while |E| < B:
      best_e ← null
      best_score ← -∞

      for each e in (C 里还没进 E 的句):
          gain  ← CovGain(e, E, constraints)     # 相对 E 的新增覆盖
          red   ← max cosine(e, e') for e' in E  # E 空则 red=0
          harm  ← HarmProxy(e, q, constraints, gain)
          score ← gain − λ·red − γ·harm

          if score > best_score:
              best_score ← score
              best_e ← e

      if best_e is null or best_score ≤ ε:
          break                 # 早停：再加也不值

      E ← E ∪ {best_e}          # 只加这一句，然后进入下一轮

4.  return E                    # 送去 format_prompts
```

### 逐步小例子（示意）

问题：`2017 年之后的 Pixar 电影有哪些？`  
约束（糙解析）：`{Pixar, 2017+, set题}`  
候选三句（简化）：

| 句 | 内容（摘要） | 与问 cosine |
|----|--------------|-------------|
| A | Toy Story 4 是 Pixar 电影 | 0.82（很高） |
| B | Toy Story 4 于 2019 年上映 | 0.70 |
| C | Pixar 总部在 Emeryville | 0.75 |

**第 1 轮**（\(E=\emptyset\)）：

- A：命中 Pixar，gain=1；red=0；若无年份 → 对「2017+」无增益；harm 可能因「高分但约束不全」略扣  
- B：命中 2019→覆盖 2017+，gain 可能更高  
- C：命中 Pixar，但对答题名单几乎无用  

假设 B 的 \(\Delta U\) 最高 → **选入 B**。

**第 2 轮**（\(E=\{B\}\)）：

- A：相对 B，Pixar 可能仍有一点增益，但与 B 主题重叠 red 升；若像名单诱导则 harm↑  
- C：增益低  

若此时所有剩余句 \(\Delta U \le \varepsilon\) → **停**，只把 `{B}`（或再加一句真正补名单证据的句）送进 prompt，而不是 A+B+C 全塞。

### 和「一次取 top-k」的差别

| | 一次 top-20 / top-8 | 贪婪 CAMUS |
|--|---------------------|------------|
| 排序键 | 只看与**问题**的 cosine | 每步看相对**已选集合**的 ΔU |
| 条数 | 固定 k | 可变；早停 |
| 高分有害句 | 照样进 | \(\Delta U\) 低则进不去或被跳过 |
| 实现复杂度 | \(O(n\log n)\) 排序截断 | 每轮扫剩余候选，约 \(O(B\cdot n)\)（\(n\)=候选数，\(B\) 小） |

**注意：** 若实现时「约束解析为空、Harm=0、只按 cosine 贪婪」，会退化成换皮 top-k——那是 bug，不是 CAMUS。消融时要用 Coverage-only / 完整 CAMUS 对照，证明不是单纯缩小 k。

### 代码落点（Step 2–3）

```text
relevant_chunks, cosine_scores 已算好
        ↓
if RAG_CAMUS:
    retrieval_results = camus_greedy_select(
        query, relevant_chunks, cosine_scores, B, ε, λ, γ
    )
else:
    retrieval_results = top-NUM_CONTEXT_SENTENCES by cosine   # 现状 L323–326
        ↓
batch_retrieval_results.append(retrieval_results)
```

**红线：** `ParseConstraints` / `CovGain` / `Harm` 不得使用标准答案、评测标签、该题历史对错。

---

## 结合现有代码（`rag_llama_baseline.py`）

> **现状（2026-09-13）：** Step 2–3 已落地。`RAG_CAMUS=0` 走原 top-20；`=1` 走 `_camus_select` 贪婪 ΔU。

### 0. 总入口：开关分流

在 `batch_generate_answer` 里，cosine 算完之后：

```python
if camus_cfg["enabled"]:
    retrieval_results = _camus_select(
        queries[_idx], relevant_chunks, cosine_scores, camus_cfg,
        chunk_embeddings=relevant_chunks_embeddings,
    )
else:
    retrieval_results = relevant_chunks[
        (-cosine_scores).argsort()[:NUM_CONTEXT_SENTENCES]  # 固定 top-20
    ]
```

后面 `format_prompts` / Llama **不变**。配置由 `_camus_config()` 运行时读 `.env`（避免 import 早于 `load_dotenv`）。

### 1. 抽约束 `_camus_parse_constraints(query)`

只用问题文本（无 GT）：

| 抽什么 | 产物 | 例子 |
|--------|------|------|
| `after/since … YEAR` | 原子 `year>YEAR` | after 2017 → `year>2017` |
| `before/until … YEAR` | 原子 `year<YEAR` | |
| 大写实体（去掉 What/Which…） | 小写实体串 | Pixar → `pixar` |
| movies/list/members… | `is_set=True` | 名单题 |
| 原子为空 | 去停用词后的实词顶上（最多 8） | 兜底，防 CovGain 恒 0 |

### 2. 一句是否支持某原子 `_camus_atom_supported`

- `year>2017`：句中出现 **大于** 2017 的年份即支持（如 2019）  
- `year<…`：对称  
- 普通原子：子串匹配（`pixar in chunk.lower()`）

### 3. CovGain `_camus_cov_gain`

相对**已选集合**：加这句后新覆盖了几个原子 → 增益。  
已覆盖 `pixar` 后，再来一句只含 Pixar → gain=0。

### 4. Harm `_camus_harm`

- 与问题 cosine > τ 且 gain=0 → +1（高分无覆盖）  
- set 题且名单诱导（逗号≥3 或 including/such as…）→ +1  

### 5. 贪婪主循环 `_camus_select`

```text
pool ← cosine top-40（加速，不全表扫 HTML）
E ← ∅
while |E| < budget:
  对 pool 中未选句:
    red ← max 与已选句的 embedding 余弦
    ΔU ← gain − λ·red − γ·harm
  取 ΔU 最大者；若 ΔU≤ε 则 break
  E ← E ∪ {该句}
若 E 空：兜底 cosine top-1（避免空 references）
RAG_CAMUS_DEBUG=1 时打印 atoms 与每句 ΔU
```

### 6. 与 top-20 对照

| | `else` top-20 | `_camus_select` |
|--|---------------|-----------------|
| 键 | 与问题 cosine | 相对已选的 ΔU |
| 条数 | 固定 20 | ≤ budget，可早停 |
| 高分无覆盖 | 照样进 | harm 拉低 ΔU |

---

## 如何保证约束原子的有效性？

**先说结论：** MVP **不能「保证」原子永远正确**——当前是规则启发式。有效性要靠 **设计约束 + 诊断 + 消融 + 迭代规则** 来**提高并证伪**，而不是一次解析完美。

### 1. 原子无效时会发生什么（必须心里有数）

| 失效模式 | 后果 | 现象 |
|----------|------|------|
| **抽错 / 抽噪**（如问句引导词进实体） | CovGain 指错方向 | 选句怪异；acc 不升 |
| **漏抽关键约束**（时间/实体没抽出） | gain 常为 0 | 退化成 −冗余−harm ≈ 换皮小 k / 乱早停 |
| **匹配过宽**（子串误伤） | 假覆盖，过早停 | 缺关键证据 |
| **匹配过严**（别名、年份表述） | 真证据 gain=0 | 好句被 harm 掉 |
| **用了 GT/标签** | 泄漏 | 实验无效 |

所以：**原子质量 = CAMUS 是否名副其实的前提。**

### 2. 红线（有效性的底线）

1. **只用 query（+ 公开规则）**，禁止标准答案、评测标签、该题历史对错。  
2. **可复现**：同一 query → 同一 atoms（无随机）。  
3. **可打印**：`RAG_CAMUS_DEBUG=1` 能看到 atoms，人工可判「这题约束抽得对不对」。  
4. **可消融**：Coverage-only（γ=0）vs 全 CAMUS vs top-k，证明增益不只来自缩小 k。

### 3. 工程上「提高有效性」的做法（按优先级）

**A. 解析侧（少抽错）**

- 去掉 What/Which/How… 等问句壳（已做）  
- 时间关系写成 `year>/year<`，不要只匹配字面 “2017”（已做 after/before）  
- 控制原子数量与停用词；空原子才用实词兜底，并在 debug 里标 `fallback_tokens`  
- 后续可加：简单别名表、题型模板（comparison / false_premise）专用规则——仍禁止读 GT  

**B. 匹配侧（少假覆盖 / 少漏覆盖）**

- 年份用数值比较，不用子串 “2017”（已做相对年）  
- 实体可改为「词边界」匹配，减轻 `art`∈`Cart` 类误伤  
- 可选：原子加权（时间/实体 > 普通实词），避免兜底实词主导  

**C. 诊断侧（知道哪题原子坏了）**

对 200 子集（尤其 `rag_worse` 25 条）固定抽查表：

| query | atoms | 人工：够不够/有没有噪声 | 选中句是否合理 |
|-------|-------|------------------------|----------------|
| … | … | OK / 漏时间 / 噪实体 | … |

统计：**原子合格率**、**漏约束率**。合格率低 → 先改解析，再谈调 λ/γ。

**D. 实验侧（证明原子在干活）**

| 对照 | 若结果 | 含义 |
|------|--------|------|
| CAMUS vs top-8 | 无差 | 可能原子无效，退化成小 k |
| Coverage-only vs cosine 贪婪 | 无差 | CovGain 没起作用 |
| `RAG_CAMUS_DEBUG` 抽查 | 多数题 atoms 离谱 | 解析未就绪，暂停全量宣称 |

**E. 不做「保证」，做「可证伪」**

研究叙述应写清：

> 约束原子由规则从 query 导出；我们通过 debug 抽查与消融表明 CovGain 驱动选句；原子错误是已知局限，二期可用更好解析器替换而不改 ΔU 框架。

### 4. 和 Step 3 代码的对应

| 有效性手段 | 代码 / 配置 |
|------------|-------------|
| 去问句壳、year>、set 标记 | `_camus_parse_constraints` |
| 相对年匹配 | `_camus_atom_supported` |
| 看每题 atoms | `RAG_CAMUS_DEBUG=1` |
| 防空上下文 | 早停后 cosine top-1 兜底 |
| 泄漏红线 | 函数入参无 GT；评测脚本勿传入 label |

### 5. 一句话

**不能从规则上「保证」原子有效；能保证的是：可检查、不泄漏、能用消融证明「原子驱动的 CovGain」是否真在起作用。原子不合格时，先修解析与匹配，再调 λ/γ。**

---

## 你现在的 RAG 在干嘛

代码：`models/rag_llama_baseline.py`

```text
网页 HTML
  → 切成很多句子
  → MiniLM 算每句和「问题」有多像（余弦相似度）
  → 固定塞进最像的 20 句（top-20）
  → 让 Llama 根据这 20 句答题
```

直觉上「越像越好」。但本地 200 子集上已经看到：**像 ≠ 有用。**

---

## 为什么 top-20 会害人（例子）

问：**「2017 年之后的 Pixar 电影有哪些？」**

可能出现高分句子：

> 「Toy Story 4 是一部 Pixar 电影。」

- 和问题很像（都有 Pixar、电影）→ 余弦分很高  
- 但**没说清**是不是「2017 之后」  
- 再塞一堆同类高分句，模型容易**拼出一个更长的错误名单**

这类题里，Vanilla（不检索）可能答对，加上网页 RAG 反而幻觉 → 就是你们标的 **`rag_worse`（约 25/200）**。  
失败分析里多标成 **过度检索**：材料太多、太「像」，把模型带偏了。

你们试过的 **v1**（分数太低就拒答）压不住，是因为这些有害句分数往往**不低**。

---

## CAMUS 改哪一步

```text
…… MiniLM 算完相似度、排出候选 ……
        ↓
   【CAMUS 贪婪选证】  ← 只改这一步（见上文「贪婪挑选」）
        ↓
   把选中的句子 format 进 prompt
        ↓
   Llama 生成答案
```

| | 现在（baseline） | CAMUS |
|--|------------------|--------|
| 挑句标准 | 和问题越像越好，固定 top-20 | 问：这句对**答对这题**还有没有用？ |
| 怎么加 | 一次拿满 20 句 | **贪婪**：每轮加 ΔU 最大的一句；不够大就**停** |
| 会扔掉什么 | 基本不扔高分句 | 高分但帮不上忙、重复、容易带偏名单的句 |

---

## 名字怎么记

| 字母 | 英文 | 白话 |
|------|------|------|
| **C** | Constraint-Aware | 先看问题要满足哪些**约束**（谁、哪年、集合还是单实体…） |
| **MU** | Marginal Utility | **再加这一句**，对答对有没有**多出来的好处**？还是只是重复/添乱？ |
| **S** | Selection | 按这个「好处」选句，不是按「像不像」选完事 |

---

## 买菜比方

| baseline | CAMUS（贪婪） |
|----------|----------------|
| 货架上「看起来相关」的 20 样全扔进锅 | 每轮只买「当前最缺、最划算」的一样；不够划算就停 |
| 看着像菜就买 | 用不上的不买；容易把汤做糊的坚决不买 |

---

## 和别的东西别混

| 方法 | 管的事 | 一句话 |
|------|--------|--------|
| **CAMUS** | **哪些**句子进 context | 检索还用，但少喂、喂对的（贪婪 + 早停） |
| **W1**（RH-ACS+） | **要不要**用检索 | 发现检索在害人 → 回退闭卷答案 |
| **v1 / v2 拒答** | 答不答得出 | 不确定就说 I don't know |
| **SAFE-U** | 对照实验 | 用「熵减/IG」再选一遍，证明 CAMUS ≠ 熵减换皮 |
| **HOPS** | 可选预剪 | 先砍掉明显有害的集合诱导句；快刀，不当主创新 |

**研究主叙事卖 CAMUS**；W1 可以并行做，但写成另一条贡献，不要糊成「一个方法」。

---

## 你要验证的一句话

> 换掉「固定 top-20 按相似度」，改成「按答题效用贪婪选句并早停」，  
> `rag_worse` 那些题能不能少幻觉一点，  
> 同时别把本来 RAG 能答对的题（`rag_helps`）搞砸。

落地步骤见：[20260912-CAMUS第1周执行步骤.md](./20260912-CAMUS第1周执行步骤.md)。
