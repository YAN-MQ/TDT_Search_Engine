# TDT3 搜索引擎

基于 Python 的信息检索系统，用于检索 TDT3 语料库中的文档。

## 功能特点

- 建立倒排索引，支持快速检索
- 支持自由文本和短语查询 (使用双引号标识短语)
- 使用 TF-IDF/BM25 文档评分
- 显示包含查询词的文档摘要
- 交互式命令行界面

## 项目结构

```
TDT_Search_Engine/
│
├── main.py                     # 程序入口，处理命令行查询
├── config.py                   # 配置文件（Top-N、路径设置等）
│
├── index/                      # 索引模块
│   ├── indexer.py              # 建立倒排索引
│   └── storage.py              # 存储索引的数据结构
│
├── preprocess/                 # 预处理模块
│   ├── tokenizer.py            # 分词、大小写、去标点处理
│   └── normalizer.py           # 词干提取、数字过滤
│
├── search/                     # 搜索模块
│   ├── query_parser.py         # 解析用户输入（支持短语查询）
│   ├── scorer.py               # 实现 TF-IDF 打分函数
│   └── retriever.py            # 返回 Top-N 结果及摘要
│
├── utils/                      # 工具模块
│   ├── snippet.py              # 从文档中生成查询相关摘要
│   └── file_loader.py          # 加载 TDT3 文档集
│
└── test_queries/               # 测试查询
    └── run_tests.py            # 运行预定义的测试查询
```

## 环境要求

- Python 3.6+
- NLTK (可选，用于改进分词和词干提取)

## 安装

1. 克隆仓库
```bash
git clone https://github.com/yourusername/TDT_Search_Engine.git
cd TDT_Search_Engine
```

2. 安装依赖
```bash
pip install nltk
```

3. 下载 NLTK 资源（可选）
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

## 使用方法

### 构建索引

首先，需要指定 TDT3 语料库路径并构建索引：

```bash
python main.py index --corpus /path/to/TDT3_Corpus --output index_data.pkl
```

### 搜索查询

执行单次查询：

```bash
python main.py search "hurricane george" --index index_data.pkl --top 10
```

对于短语查询，使用双引号：

```bash
python main.py search "\"new york\" bombing" --index index_data.pkl
```

### 交互式模式

启动交互式查询界面：

```bash
python main.py interactive --index index_data.pkl
```

### 运行测试查询

执行预定义的测试查询：

```bash
python test_queries/run_tests.py --index index_data.pkl --docs /path/to/TDT3_Corpus
```

## 配置

可以在 `config.py` 中修改默认配置：

- 索引路径
- 返回结果数量
- 分词和规范化选项
- 评分参数
- 摘要生成参数

## 参考资料

- Manning, C. D., Raghavan, P., & Schütze, H. (2008). Introduction to Information Retrieval. Cambridge University Press.
- TDT3 语料库: https://catalog.ldc.upenn.edu/LDC2001T58 