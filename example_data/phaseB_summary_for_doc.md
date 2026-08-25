<!-- auto from error_analysis_phaseB_labeled_heuristic_20260825.json -->

**样本 n=110**（硬例优先队列；启发式 `heuristic_v1`，待人工抽检）

### 细标签占比（110 条）

| 细标签 | n | 占 110 | 与拒答/可信主线 |
|--------|---|--------|-----------------|
| 生成错 | 38 | 34.5% | ✓ 相关 |
| 过度检索 | 25 | 22.7% | ✓ 相关 |
| 缺证据 | 22 | 20.0% | ✓ 相关 |
| 检索有效 | 10 | 9.1% | 对照 |
| 合理拒答 | 9 | 8.2% | 拒答行为 |
| 过早停 | 6 | 5.5% | 拒答行为 |

**主攻相关标签合计**（缺证据/检索未用/过度检索/应拒却答/生成错/查询偏移/冲突）： **85/110 = 77.3%**

**错误态 Top-3**（排除检索有效、合理拒答）：
1. **生成错** — 38 条（41.8% of 91 条错误态）
2. **过度检索** — 25 条（27.5% of 91 条错误态）
3. **缺证据** — 22 条（24.2% of 91 条错误态）

### 桶 × 细标签

| bucket | 细标签 | n |
|--------|--------|---|
| rag_worse_hallucination | 过度检索 | 25 |
| rag_hallucination | 生成错 | 24 |
| both_hallucination | 缺证据 | 16 |
| both_hallucination | 生成错 | 14 |
| rag_helps | 检索有效 | 10 |
| both_missing | 合理拒答 | 9 |
| rag_hallucination | 缺证据 | 6 |
| rag_missing | 过早停 | 5 |
| both_missing | 过早停 | 1 |

### 代表 case（人工 sense-check）

| bucket | 标签 | 题型 | 问题摘要 | 预测摘要 |
|--------|------|------|----------|----------|
| rag_worse_hallucination | 过度检索 | set | what pixar films were released after 2017? | Toy Story 4 (2019), Onward (2020), Soul (2020), Lu |
| both_hallucination | 缺证据 | set | who were the members of the band green day? | Billie Joe Armstrong, Mike Dirnt, Tré Cool, Jason  |
| rag_hallucination | 生成错 | simple | wt what time did the assassination of jesse james by the cow | September 2, 2007. |
| rag_helps | 检索有效 | false_premise | how many times has sunisa lee won the olympic all-around ind | 1 |