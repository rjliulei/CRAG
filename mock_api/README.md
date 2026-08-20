# 综合 RAG 基准（CRAG）模拟 API / Comprehensive RAG Benchmark (CRAG) Mock API

## 前置要求 / Prerequisites

在开始设置与使用 CRAG Mock API 之前，请确保系统已安装并配置以下内容： / Before diving into the setup and usage of the CRAG Mock API, ensure you have the following prerequisites installed and set up on your system:
- Git（用于克隆仓库） / Git (for cloning the repository)
- Python 3.10

## 安装指南 / Installation Guide

### 环境设置 / Setting Up Your Environment

首先使用 Git 将仓库克隆到本地。然后进入仓库目录并安装必要依赖： / First, clone the repository to your local machine using Git. Then, navigate to the repository directory and install the necessary dependencies:

```
cd mock_api
pip install -r requirements.txt
```

## 运行 API 服务器 / Running the API Server

使用以下 Uvicorn 命令在本地启动 API 服务器。这将启动一个快速的异步服务器来处理 API 请求。 / To launch the API server on your local machine, use the following Uvicorn command. This starts a fast, asynchronous server to handle API requests.

```
uvicorn server:app --reload
```

访问 API 文档并在 `http://127.0.0.1:8000/docs` 测试接口。 / Access the API documentation and test the endpoints at `http://127.0.0.1:8000/docs`.

如需自定义服务器配置，可按如下方式指定主机与端口： / For custom server configurations, specify the host and port as follows:

```
uvicorn server:app --reload --host [HOST] --port [PORT]
```

## 系统要求 / System Requirements

- **支持的操作系统 / Supported OS**：Linux、Windows、macOS
- **Python 版本 / Python Version**：3.10
- 完整的 Python 包依赖列表见 `requirements.txt`。 / See `requirements.txt` for a complete list of Python package dependencies.

## Python API 封装 / Python API Wrapper

对于 Python 开发者，[/mock_api/apiwrapper/pycragapi.py](/mock_api/apiwrapper/pycragapi.py) 提供了便捷的 API 交互方式。使用示例见 [/mock_api/apiwrapper/example_call.ipynb](/mock_api/apiwrapper/example_call.ipynb)，展示如何高效地将 API 集成到开发流程中。

For Python developers, the [/mock_api/apiwrapper/pycragapi.py](/mock_api/apiwrapper/pycragapi.py) provides a convenient way to interact with the API. An example usage is demonstrated in [/mock_api/apiwrapper/example_call.ipynb](/mock_api/apiwrapper/example_call.ipynb), showcasing how to efficiently integrate the API into your development workflow.
