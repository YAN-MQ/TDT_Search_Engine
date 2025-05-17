"""
分词器模块，处理文档和查询文本的分词
"""
import re
import string
from typing import List, Set

# 尝试导入nltk，如果不存在则使用基本分词方法
try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
    
    # 确保下载必要的nltk资源
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
        
    STOP_WORDS = set(stopwords.words('english'))
except ImportError:
    NLTK_AVAILABLE = False
    # 简单的停用词列表
    STOP_WORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
        'which', 'this', 'that', 'these', 'those', 'then', 'just', 'so', 'than',
        'such', 'both', 'through', 'about', 'between', 'after', 'before', 'during',
        'in', 'to', 'from', 'of', 'at', 'by', 'for', 'with', 'against', 'on', 'into'
    }


class Tokenizer:
    """文本分词器，负责文档和查询的分词处理"""
    
    def __init__(self, remove_stopwords: bool = True, case_sensitive: bool = False,
                 remove_punctuation: bool = True, min_token_length: int = 2):
        """
        初始化分词器
        
        Args:
            remove_stopwords: 是否移除停用词
            case_sensitive: 是否区分大小写
            remove_punctuation: 是否移除标点符号
            min_token_length: 最小词项长度
        """
        self.remove_stopwords = remove_stopwords
        self.case_sensitive = case_sensitive
        self.remove_punctuation = remove_punctuation
        self.min_token_length = min_token_length
        
        # 编译标点符号移除正则表达式
        self.punctuation_pattern = re.compile(f'[{re.escape(string.punctuation)}]')
        
    def tokenize(self, text: str) -> List[str]:
        """
        对文本进行分词处理
        
        Args:
            text: 输入文本
            
        Returns:
            处理后的词项列表
        """
        if not text:
            return []
        
        # 大小写转换
        if not self.case_sensitive:
            text = text.lower()
        
        # 分词
        if NLTK_AVAILABLE:
            tokens = word_tokenize(text)
        else:
            # 如果没有nltk，使用简单的空格分词
            if self.remove_punctuation:
                text = self.punctuation_pattern.sub(' ', text)
            tokens = text.split()
        
        # 处理标点符号
        if self.remove_punctuation and NLTK_AVAILABLE:
            tokens = [self.punctuation_pattern.sub('', token) for token in tokens]
        
        # 过滤词项
        tokens = [token for token in tokens if token and len(token) >= self.min_token_length]
        
        # 移除停用词
        if self.remove_stopwords:
            tokens = [token for token in tokens if token not in STOP_WORDS]
            
        return tokens

    def tokenize_phrase(self, phrase: str) -> List[str]:
        """
        对短语进行分词处理，保留停用词
        
        Args:
            phrase: 输入短语
            
        Returns:
            处理后的词项列表
        """
        temp_remove_stopwords = self.remove_stopwords
        self.remove_stopwords = False
        tokens = self.tokenize(phrase)
        self.remove_stopwords = temp_remove_stopwords
        return tokens
        
    def tokenize_query(self, query: str) -> List[str]:
        """
        对查询文本进行分词处理
        
        Args:
            query: 查询文本
            
        Returns:
            处理后的词项列表
        """
        # 对查询分词规则可以与文档略有不同
        return self.tokenize(query)
