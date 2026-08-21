# 03 · AutoDL 单卡 24GB 操作手册（主文档）

> 整理日期：2026-08-21  
> **用途**：在 AutoDL 上跑通 CRAG。按本文从上到下做即可，一般**不必**再翻 01/02。  
> 卡型：1 × 24GB（推荐 **RTX 4090**）  
> **生成模型**：本环境默认使用已获权的 `meta-llama/Llama-3.1-8B-Instruct`（官方示例为 `Meta-Llama-3-8B-Instruct`，二者同为门控，需分别在模型页申请）。

---

## 开机前清单（前置操作）

租机前先把账号与密钥备齐。跑官方 Llama 基线时，**需要注册 Hugging Face 账号**。

### 必做（跑通 Vanilla + 自动评估）


| 准备项                 | 做什么                                                                                                                  | 说明                                 |
| ------------------- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| AutoDL              | 账号有余额；能租 **1×24GB**（推荐 RTX 4090）；镜像含 **CUDA + Python 3.10**                                                          | 算力                                 |
| 数据盘                 | ≥ **50GB**（建议 80GB+）                                                                                                 | 仓库 + 权重 + 数据集                      |
| **Hugging Face 账号** | [注册](https://huggingface.co/join)                                                                                    | 下载 Llama 权重必需                      |
| **接受 Llama 条款**     | 打开 [Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)，同意分享联系方式并接受 License（可能需等待审核） | **只注册不点条款会下不了**；3 与 3.1 需**分别**申请 |
| **HF Access Token** | [Settings → Access Tokens](https://huggingface.co/settings/tokens) 新建（Read 即可），本地 `hf auth login` 粘贴，**勿写入仓库** | 供 `hf auth login`（旧版 `huggingface-cli` 已弃用） |
| **OpenAI API Key**  | 有额度、能调用 GPT                                                                                                          | `local_evaluation.py` 默认用 GPT-4 打分 |


HF 顺序固定：**网页接受条款 → `hf auth login` → 再 `hf download`**。

### 按你要跑的内容再加


| 目标                    | 额外前置                                                     |
| --------------------- | -------------------------------------------------------- |
| 只冒烟 `DummyModel`      | 可不下 Llama、可暂不登 HF；正式打分仍要 OpenAI Key                      |
| **RAG / RAG-KG**      | 再下 `all-MiniLM-L6-v2`（公开模型，一般无需单独条款）                     |
| **Task 2/3 或 RAG-KG** | 启动 Mock API（见步骤 G）                                       |
| 开发集评测                 | 下载 Task1/2 开发集到 `example_data/dev_data.jsonl.bz2`（见步骤 D） |


### 现在还不用

- Meta / Facebook 单独账号（条款在 Hugging Face 模型页上接受即可）
- GitHub 登录（公开仓库 `git clone` 一般够用）
- 多卡或官方 4×T4（当前计划用单卡即可）

### 最短路径

AutoDL 能开机 → HF 注册并**接受 Llama 条款** + 拿到 Token → OpenAI Key 备好 → 从下面步骤 A 做起。

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

### A.1 Cursor / VS Code：Remote-SSH 连接实例

用本机 Cursor（或 VS Code）直接编辑服务器上的代码。实例须**已开机**。

官方参考：[AutoDL · VSCode 远程开发](https://www.autodl.com/docs/vscode/)

#### 1）装插件

扩展里搜索并安装 **Remote - SSH**（Cursor 自带的 Remote SSH 亦可）。

#### 2）从 AutoDL 控制台复制 SSH

形如（端口与主机以控制台为准，**会随关机/重开变化**）：

```text
ssh -p <端口> root@connect.<区域>.seetacloud.com
```

另有登录**密码**（只在登录时输入；**勿写入仓库、勿贴进聊天/文档**）。

#### 3）写入本机 SSH config（推荐）

`Ctrl+Shift+P` → `Remote-SSH: Open SSH Configuration File` → 选本机：

`C:\Users\<你的用户名>\.ssh\config`

追加（端口与主机以控制台为准，**勿把密码写进文件**）：

```ssh-config
Host autodl-crag
    HostName connect.<区域>.seetacloud.com
    User root
    Port <端口>
```

示例：若控制台为 `ssh -p 17947 root@connect.nmb1.seetacloud.com`，则 `HostName` 填 `connect.nmb1.seetacloud.com`，`Port` 填 `17947`。

#### 4）连接并打开项目

1. `Ctrl+Shift+P` → `Remote-SSH: Connect to Host...` → 选 `autodl-crag`
2. 远程系统选 **Linux**
3. 输入 AutoDL 登录密码
4. 左下角出现 `SSH: autodl-crag` 即成功
5. `File` → `Open Folder` → 打开 `/root/autodl-tmp/CRAG`（按实际路径）

本机也可先测通：

```powershell
ssh autodl-crag
```

#### 5）可选：免密登录（少输密码）

本机 PowerShell：

```powershell
# 若还没有密钥
ssh-keygen -t ed25519 -N "" -f $env:USERPROFILE\.ssh\id_ed25519

# 把公钥拷到服务器（-p 后换成你的端口与主机）
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh -p <端口> root@connect.<区域>.seetacloud.com "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

config 增加一行（Windows 路径用正斜杠）：

```ssh-config
    IdentityFile C:/Users/<你的用户名>/.ssh/id_ed25519
```

#### 6）使用注意

| 点 | 说明 |
|----|------|
| 长任务 | 训练/评估不要只靠 Remote 终端裸跑；用 `tmux` / `screen`，避免 SSH 断开就停 |
| 落盘 | 代码与数据放 `/root/autodl-tmp` |
| 解释器 | 远程打开后选 `.venv/bin/python` |
| 安全 | 密码勿提交 Git、勿写入本手册正文 |

---

## 步骤 B · 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

`vllm` 安装较慢、或后续 HF / GitHub 下载慢时，用下面两种办法（可并用）。

### B.1 开 AutoDL 学术加速（GitHub / Hugging Face）

在**终端**执行：

```bash
source /etc/network_turbo
```

主要加速：`github.com`、`huggingface.co` 等。装完或下完建议关掉，避免影响普通外网：

```bash
unset http_proxy && unset https_proxy
```

若在 Jupyter Notebook 里用，先把代理同步进当前 Python 环境：

```python
import subprocess, os
result = subprocess.run(
    'bash -c "source /etc/network_turbo && env | grep proxy"',
    shell=True, capture_output=True, text=True,
)
for line in result.stdout.splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        os.environ[k] = v
```

官方说明：[https://www.autodl.com/docs/network_turbo/](https://www.autodl.com/docs/network_turbo/)

### B.2 换 pip 镜像（装依赖 / vllm 慢）

学术加速主要管 GitHub/HF；**pip 包**更稳的是直接换国内源：

```bash
pip install -U pip
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
```

清华源也可以：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

想长期默认：

```bash
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set global.trusted-host mirrors.aliyun.com
```

### B.3 Hugging Face 权重下载慢（可选）

```bash
# 方案 A：先 source /etc/network_turbo（见 B.1）
# 方案 B：HF 国内镜像
export HF_ENDPOINT=https://hf-mirror.com
```

然后按步骤 E 正常 `hf download ...`。


| 场景                       | 优先做法                                 |
| ------------------------ | ------------------------------------ |
| `pip install` / `vllm` 慢 | **B.2** pip 镜像                       |
| `git clone` / HF 权重慢     | **B.1** 学术加速，或 **B.3** `HF_ENDPOINT` |


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

## 步骤 D · 准备数据（本机已有则上传；否则下载）

全量开发集很大（本机常见体积大致为）：

| 文件 | 大约体积 |
|------|----------|
| Task1/2：`crag_task_1_and_2_dev_v*.jsonl.bz2` | ~700MB |
| Task3：多个 `*.tar.bz2.part*` | 合计约 7–8GB |

仓库里若只有约 2MB 的 `example_data/dev_data.jsonl.bz2`，那是小样本；全量一般在本机 `data/` 目录。

### D.0 网盘会最快吗？

**大文件（尤其 Task3、或本机直连 SSH 慢时）：网盘通常最快且最稳**，也是 AutoDL 官方强烈推荐的方式。  
原因：本机 → 阿里云盘/夸克/百度 → 实例，两端往往都走国内高速链路；直连 `scp` 要经 SSH 隧道，易受运营商与高峰影响。

**不保证绝对第一**：若你本机上行带宽很好、且到该区域 SSH 也很快，传单个 ~700MB 的 Task1/2 时，**FileZilla / scp 直传也可能差不多或略快**（少一次「先传到网盘」）。  
实务建议：

- Task1/2（~700MB）：网盘或 FileZilla/scp 都行；直传方便就直传  
- Task3（多 GB）：优先网盘  
- JupyterLab 网页上传：不推荐大文件  

官方文档：[公网网盘](https://www.autodl.com/docs/netdisk/) · [SCP](https://www.autodl.com/docs/scp/)  
**一律落到数据盘** `/root/autodl-tmp/...`（关机不丢）。

### D.1 本机已有数据 → 上传到 AutoDL

#### 方式 A：公网网盘（大文件首选）

1. 本机把 bz2 / part 文件传到阿里云盘、夸克或百度网盘  
2. 实例开机后打开 **AutoPanel / 公网网盘**，授权后下载到 `/root/autodl-tmp`  
3. 链到仓库路径（或改 `DATASET_PATH`）：

```bash
mkdir -p /root/autodl-tmp/CRAG/example_data
# 以 Task1/2 为例，文件名按你实际上传的为准
ln -sf /root/autodl-tmp/crag_task_1_and_2_dev_v4.jsonl.bz2 \
  /root/autodl-tmp/CRAG/example_data/dev_data.jsonl.bz2
```

#### 方式 B：FileZilla / WinSCP / Xftp（Task1/2 很方便）

用控制台里的 **SSH 主机、端口、密码**，协议选 SFTP，拖到 `/root/autodl-tmp`。

#### 方式 C：本机 scp（命令行）

在**本机**执行（不要在实例里跑）。控制台 SSH 形如 `ssh -p 35394 root@region-x.autodl.com`，注意 scp 用**大写 `-P`**：

```powershell
# Windows PowerShell 示例；端口与主机换成你的
scp -P 35394 "E:\workspace\CRAG\data\crag_task_1_and_2_dev_v4.jsonl.bz2" root@region-x.autodl.com:/root/autodl-tmp/
```

已是 `.bz2` 的不要再 zip 一层。实例需**开机**才能传。

#### Task3 多分片

网盘一次下完各 `part*`，或 scp 逐个上传后在实例合并：

```bash
cd /root/autodl-tmp
cat crag_task_3_dev_v4.tar.bz2.part* > crag_task_3_dev_v4.tar.bz2
tar -xjf crag_task_3_dev_v4.tar.bz2
```

开发阶段建议**先只传 Task1/2 一个 bz2** 跑通，再考虑 Task3。

### D.2 本机没有 → 在实例下载

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

> 新版 CLI 入口是 `hf`（`huggingface-cli` 已弃用，直接调用会失败）。

```bash
pip install -U huggingface_hub
hf auth login
# 粘贴 HF Token

# 可选加速（替代已弃用的 HF_HUB_ENABLE_HF_TRANSFER）
# export HF_XET_HIGH_PERFORMANCE=1

hf download \
    meta-llama/Llama-3.1-8B-Instruct \
    --local-dir models/meta-llama/Llama-3.1-8B-Instruct \
    --exclude "*.pth"
```

三个基线中的 `self.model_name` 已指向上述本地目录。若改用其他权重，同步改路径。

仅当跑 RAG / RAG-KG 时再下：

```bash
hf download \
    sentence-transformers/all-MiniLM-L6-v2 \
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

- （开机前）HF 已注册，并在模型页**接受 Llama 条款**；Token 已备好
- （开机前）OpenAI API Key 已备好
- AutoDL 1×24GB，Python 3.10 + CUDA；代码/数据/权重在数据盘
- （可选）Cursor Remote-SSH 已能连上并打开 `/root/autodl-tmp/CRAG`（见 **A.1**）
- `pip install -r requirements.txt`
- `VLLM_TENSOR_PARALLEL_SIZE = 1`，`BATCH_SIZE = 4`
- `example_data/dev_data.jsonl.bz2` 已就绪
- `hf auth login` 并 `hf download` Llama-3.1-8B-Instruct
- `OPENAI_API_KEY` 已设置
- `user_config.py` 指向目标模型
- `python local_evaluation.py`
- 不用时关机，避免空转计费

---

## 常见问题


| 现象                  | 处理                                          |
| ------------------- | ------------------------------------------- |
| HF 401 / 无法下载 Llama | 见文首**开机前清单**：在 **Llama-3.1** 模型页接受条款并等通过，再 `hf auth login`；Token 与网页须为同一账号 |
| 条款被拒（rejected）     | 换账号或补全联系信息后重新申请；本手册已改用已通过的 `Llama-3.1-8B-Instruct` |
| 多卡/并行相关报错           | 确认 `VLLM_TENSOR_PARALLEL_SIZE=1`            |
| CUDA OOM            | `BATCH_SIZE=1`，`gpu_memory_utilization=0.7` |
| 找不到数据/权重            | 检查路径是否在仓库内相对路径正确                            |
| HF 下载慢              | 见步骤 **B.1 / B.3**；或本机下好再上传数据盘               |
| pip / vllm 安装慢      | 见步骤 **B.2** 换国内镜像                           |
| 开发集很大、本机已有         | 见步骤 **D**；大文件优先网盘，Task1/2 也可用 FileZilla/scp |
| Remote-SSH 连不上         | 实例是否开机；`~/.ssh/config` 的 HostName/Port 是否与控制台一致（重开常变端口）；见 **A.1** |
| OpenAI 失败           | 检查 Key、余额、出网                                |
| 关机后文件没了             | 确认写在 `/root/autodl-tmp` 等数据盘                |


---

## 和官方评测的关系


|     | 你现在（AutoDL） | 官方        |
| --- | ----------- | --------- |
| GPU | 1×24GB      | 4×T4 16GB |
| 参数  | TP=1        | TP=4      |
| 目的  | 开发、跑通、调参    | 对齐提交环境    |


开发阶段用本手册即可；若以后要严格对齐比赛，再租 4×T4 对照。

---

## 还需要看别的文档吗？


| 需求                 | 要不要                            |
| ------------------ | ------------------------------ |
| 在 AutoDL 跑通基线      | **不用**，跟本文就够                   |
| 查字段含义 / Task3 下载细节 | 需要时再看 `docs/dataset.md`        |
| 了解三个基线差异           | 需要时再看 `docs/baselines.md`      |
| 硬件选型背景             | 可选看 [01-硬件要求.md](./01-硬件要求.md) |


