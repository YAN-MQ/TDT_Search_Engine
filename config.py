"""
配置文件，存储全局设置
"""

# 索引配置
INDEX_PATH = "index_data.pkl"  # 倒排索引保存路径

# 文档集配置
CORPUS_PATH = "tdt3"  # TDT3文档集路径

# 检索配置
TOP_N = 10  # 默认返回的检索结果数量

# 分词和规范化配置
REMOVE_STOPWORDS = True  # 是否移除停用词
CASE_SENSITIVE = False  # 是否区分大小写
REMOVE_PUNCTUATION = True  # 是否移除标点符号
USE_STEMMING = True  # 是否使用词干提取
FILTER_DIGITS = False  # 是否过滤纯数字

# 摘要生成配置
CONTEXT_SIZE = 100  # 摘要上下文大小（字符数）
MAX_SNIPPET_LENGTH = 250  # 摘要最大长度

# 评分配置
# BM25参数
K1 = 1.5
B = 0.75
# 短语匹配加权
PHRASE_BOOST = 2.0

# 输出配置
RESULTS_DIR = "results"  # 查询结果保存目录

# 性能优化配置
# 文档加载和索引构建性能配置
MAX_THREADS = 0  # 最大线程数，0表示自动选择（基于CPU核心数）
BATCH_SIZE = 1000  # 批处理大小
INDEX_BUFFER_SIZE = 100000  # 索引缓冲区大小（条目数）
INDEX_FLUSH_INTERVAL = 30  # 索引缓冲区自动刷新间隔（秒）
