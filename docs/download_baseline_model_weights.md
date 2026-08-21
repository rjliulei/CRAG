### 使用 Hugging Face 设置并下载基线模型权重 / Setting Up and Downloading Baseline Model weights with Hugging Face

本指南说明如何下载（及签入）基线模型所需的模型权重。本仓库 AutoDL 环境默认使用 `Llama-3.1-8B-Instruct` 与 `all-MiniLM-L6-v2`。这些步骤同样适用于 Hugging Face 上的其他模型。

This guide outlines the steps to download (and check in) the model weights required for the baseline models. This AutoDL setup defaults to `Llama-3.1-8B-Instruct` and `all-MiniLM-L6-v2`. The steps should work equally well for other models on Hugging Face.

> **注意 / Note**：请使用新版 CLI 入口 `hf`。旧版 `huggingface-cli` 已弃用，直接调用会失败。 / Use the new `hf` CLI. The legacy `huggingface-cli` is deprecated and no longer works.

#### 前置步骤 / Preliminary Steps：

1. **安装 Hugging Face Hub 包 / Install the Hugging Face Hub Package**：
   
   安装或升级 `huggingface_hub`（会提供 `hf` 命令），在终端运行： / Install or upgrade `huggingface_hub` (which provides the `hf` command) by running:

   ```bash
   pip install -U huggingface_hub
   ```

2. **接受 Llama 使用条款 / Accept the Llama Terms**：
   
   打开 [meta-llama/Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)，同意分享联系方式并接受 License（可能需等待审核）。Llama 3 与 3.1 是**不同门控仓库**，需分别申请。 / Visit [meta-llama/Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct), agree to share contact information and accept the license (approval may take time). Llama 3 and 3.1 are **separate gated repos** and must be requested individually.

3. **创建 Hugging Face CLI Token / Create a Hugging Face CLI Token**：
   
   前往 [Hugging Face Token Settings](https://huggingface.co/settings/tokens) 生成 CLI token，后续认证需要用到。 / Generate a CLI token by navigating to: [Hugging Face Token Settings](https://huggingface.co/settings/tokens). You will need this token for authentication.

#### Hugging Face 认证 / Hugging Face Authentication：

1. **通过 CLI 登录 / Login via CLI**：
   
   使用上一步创建的 token，通过 Hugging Face CLI 进行认证。运行： / Authenticate yourself with the Hugging Face CLI using the token created in the previous step. Run:

   ```bash
   hf auth login
   ```

   按提示输入 token。 / When prompted, enter the token.

#### 模型下载 / Model Downloads：

可选加速（替代已弃用的 `HF_HUB_ENABLE_HF_TRANSFER`）： / Optional speedup (replaces deprecated `HF_HUB_ENABLE_HF_TRANSFER`):

```bash
export HF_XET_HIGH_PERFORMANCE=1
```

1. **下载 Llama-3.1-8B-Instruct 模型 / Download Llama-3.1-8B-Instruct Model**：

   执行以下命令，将模型下载到本地子目录。该命令会排除不必要的文件以节省空间： / Execute the following command to download the model to a local subdirectory. This command excludes unnecessary files to save space:

   ```bash
   hf download \
       meta-llama/Llama-3.1-8B-Instruct \
       --local-dir models/meta-llama/Llama-3.1-8B-Instruct \
       --exclude "*.pth"
   ```

2. **下载 MiniLM-L6-v2 模型（用于句子嵌入） / Download MiniLM-L6-v2 Model (for sentence embeddings)**：

   同样，使用以下命令下载 `sentence-transformers/all-MiniLM-L6-v2` 模型： / Similarly, download the `sentence-transformers/all-MiniLM-L6-v2` model using the following command:

   ```bash
   hf download \
       sentence-transformers/all-MiniLM-L6-v2 \
       --local-dir models/sentence-transformers/all-MiniLM-L6-v2 \
       --exclude "*.bin" "*.h5" "*.ot"
   ```
