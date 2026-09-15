# CAMUS 精读 PDF（本地）

对应：
- 精读清单：`docs/工作记录/头脑风暴/20260830-证据效用头脑风暴过程/20260913-CAMUS精读清单.md`
- 创新审查：`…/05-创新性审查.md`

## 文件一览

### ★ / ○ 主线（精读清单）

| 文件 | 论文 | 优先级 |
|------|------|--------|
| `01_AstuteRAG-不完美检索与冲突.pdf` | Astute RAG | ★ |
| `02_IGP-信息增益剪枝.pdf` | IGP | ★ |
| `03_ContextPicker-最小充分子集.pdf` | Context-Picker | ★ |
| `04_InfoGainRAG-文档信息增益.pdf` | InfoGain-RAG | ○ |
| `05_GainRAG-增益对齐选段.pdf` | GainRAG | ○ |
| `06_RECOMP-检索压缩.pdf` | RECOMP | ○ |
| `07_Provence-上下文剪枝.pdf` | Provence | ○ |
| `08_SEALRAG-预算内替换.pdf` | SEAL-RAG | ○ |

### 补齐 `05-创新性审查` 点名

| 文件 | 论文 | 来源 |
|------|------|------|
| `09_CorrectiveRAG-检索纠正.pdf` | Corrective RAG | 从 `docs/论文/` 复制 |
| `10_SelfRAG-检索批判生成.pdf` | Self-RAG | 从 `docs/论文/` 复制 |
| `11_AdaptiveRAG-按复杂度适配检索.pdf` | Adaptive-RAG | 新下 arXiv:2403.14403 |
| `12_LongLLMLingua-长上下文压缩.pdf` | LongLLMLingua | 新下 arXiv:2310.06839 |
| `13_RAGCSM-影响引导上下文选择.pdf` | Influence / RAG-CSM | 新下 arXiv:2509.21359 |
| `14_ZeroRAG-零冗余知识.pdf` | Zero-RAG | 新下 arXiv:2511.00505 |
| `15_QUBO-证据集合选择.pdf` | QUBO Evidence Selection | 新下 arXiv:2607.12334 |
| `16_RobustRALM-NLI滤无关上下文.pdf` | Robust RALM（NLI 滤无关） | 新下 arXiv:2310.01558（Yoran et al., ICLR’24 一类） |

### 仍需谨慎对待

| 文件 | 工作 | 说明 |
|------|------|------|
| `17_CER-因果充分证据集-UNVERIFIED.pdf` | CER | 已下载；出处期刊可疑，**保持 UNVERIFIED**，写 Related Work 前先人工扫一眼 |

## `05` 覆盖结论

已核验表 + CER（未核验）均已本地化到本目录（共 17 个 PDF）。

## 推荐阅读顺序（更新）

```text
1–3   Astute → IGP → Context-Picker     （差界骨架，必做）
13    RAG-CSM（Influence）               （最贴 ΔU；训代理重，一句差界）
14    Zero-RAG                           （检索伤「已会答」题，现象同族）
4+6/7 InfoGain + RECOMP或Provence        （Related Work）
9–11  Corrective / Self-RAG / Adaptive   （扫差界，勿深挖）
12/15/16/5/8  压缩·QUBO·NLI·Gain·SEAL    （一句带过即可）
17    CER（可选扫）                       （仅当要写因果充分集差界时）
```

## 论文解析

精读产出：[`../12-CAMUS精读论文解析.md`](../12-CAMUS精读论文解析.md)（2026-09-13）

### 逐节精读笔记

| 文件 | 说明 |
|------|------|
| [`02_IGP-逐节中英精读笔记.md`](./02_IGP-逐节中英精读笔记.md) | IGP **意译**逐节中英对照（非整篇照搬全文） |
| [`Pareto-frontier读论文笔记.md`](./Pareto-frontier读论文笔记.md) | 读 IGP 收获：质量–成本 **Pareto frontier** 概念 |
