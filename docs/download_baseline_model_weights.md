### 使用 Hugging Face 设置并下载基线模型权重 / Setting Up and Downloading Baseline Model weights with Hugging Face

本指南说明如何下载（及签入）基线模型所需的模型权重。我们将以 `Meta-Llama-3-8B-Instruct` 与 `all-MiniLM-L6-v2` 模型为例。但这些步骤同样适用于 Hugging Face 上的其他模型。

This guide outlines the steps to download (and check in) the models weights required for the baseline models. We will focus on the `Meta-Llama-3-8B-Instruct` and `all-MiniLM-L6-v2` models. But the steps should work equally well for any other models on hugging face.

#### 前置步骤 / Preliminary Steps：

1. **安装 Hugging Face Hub 包 / Install the Hugging Face Hub Package**：
   
   首先安装包含 `hf_transfer` 工具的 `huggingface_hub` 包，在终端运行： / Begin by installing the `huggingface_hub` package, which includes the `hf_transfer` utility, by running the following command in your terminal:

   ```bash
   pip install huggingface_hub[hf_transfer]
   ```

2. **接受 Llama 使用条款 / Accept the Llama Terms**：
   
   你必须访问以下页面并接受 Llama 模型的使用条款： / You must accept the Llama model's terms of use by visiting: [meta-llama/Meta-Llama-3-8B-Instruct Terms](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)。

3. **创建 Hugging Face CLI Token / Create a Hugging Face CLI Token**：
   
   前往 [Hugging Face Token Settings](https://huggingface.co/settings/tokens) 生成 CLI token，后续认证需要用到。 / Generate a CLI token by navigating to: [Hugging Face Token Settings](https://huggingface.co/settings/tokens). You will need this token for authentication.

#### Hugging Face 认证 / Hugging Face Authentication：

1. **通过 CLI 登录 / Login via CLI**：
   
   使用上一步创建的 token，通过 Hugging Face CLI 进行认证。运行： / Authenticate yourself with the Hugging Face CLI using the token created in the previous step. Run:

   ```bash
   huggingface-cli login
   ```

   按提示输入 token。 / When prompted, enter the token.

#### 模型下载 / Model Downloads：

1. **下载 LLaMA-2-7b 模型 / Download LLaMA-2-7b Model**：

   执行以下命令，将 `Meta-Llama-3-8B-Instruct` 模型下载到本地子目录。该命令会排除不必要的文件以节省空间： / Execute the following command to download the `Meta-Llama-3-8B-Instruct` model to a local subdirectory. This command excludes unnecessary files to save space:

   ```bash
   HF_HUB_ENABLE_HF_TRANSFER=1 huggingface-cli download \
       meta-llama/Meta-Llama-3-8B-Instruct \
       --local-dir-use-symlinks False \
       --local-dir models/meta-llama/Meta-Llama-3-8B-Instruct \
       --exclude *.pth # These are alternates to the safetensors hence not needed
   ```

3. **下载 MiniLM-L6-v2 模型（用于句子嵌入） / Download MiniLM-L6-v2 Model (for sentence embeddings)**：

   同样，使用以下命令下载 `sentence-transformers/all-MiniLM-L6-v2` 模型： / Similarly, download the `sentence-transformers/all-MiniLM-L6-v2` model using the following command:

   ```bash
   HF_HUB_ENABLE_HF_TRANSFER=1 huggingface-cli download \
      sentence-transformers/all-MiniLM-L6-v2 \
       --local-dir-use-symlinks False \
       --local-dir models/sentence-transformers/all-MiniLM-L6-v2 \
       --exclude *.bin *.h5 *.ot # These are alternates to the safetensors hence not needed
   ```
