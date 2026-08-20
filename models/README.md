# 编写自定义模型指南 / Guide to Writing Your Own Models

## 模型基类 / Model Base Class

你的模型应遵循 [dummy_model.py](dummy_model.py) 中 `DummyModel` 类的格式。我们提供示例模型 `dummy_model.py`，用于说明自定义模型的结构。关键的是，你的模型类必须实现 `batch_generate_answer` 方法。

Your models should follow the format from the `DummyModel` class found in [dummy_model.py](dummy_model.py). We provide the example model, `dummy_model.py`, to illustrate the structure your own model. Crucially, your model class must implement the `batch_generate_answer` method.

## 选择使用哪个模型 / Selecting which model to use

为确保模型被正确识别与调用，请按照内联注释中的说明，在 [`user_config.py`](user_config.py) 文件中指定你的模型类名。

To ensure your model is recognized and utilized correctly, please specify your model class name in the [`user_config.py`](user_config.py) file, by following the instructions in the inline comments.

## 模型输入与输出 / Model Inputs and Outputs

### 输入 / Inputs

你的模型将收到一批输入查询，形式为字典，包含以下键： / Your model will receive a batch of input queries as a dictionary, where the dictionary has the following keys:

```
    - 'query' (List[str]): 用户查询列表。 / List of user queries.
    - 'search_results' (List[List[Dict]]): 搜索结果列表的列表，每个对应一个查询。 / List of search result lists, each corresponding to a query.
    - 'query_time' (List[str]): 时间戳列表（字符串形式），每个对应查询发生的时间。 / List of timestamps (represented as a string), each corresponding to when a query was made.
```

### 输出 / Outputs

模型的 `batch_generate_answer` 函数输出应为输入批次中所有查询的字符串回答列表。

The output from your model's `batch_generate_answer` function should be a list of string responses for all the queries in the input batch.
