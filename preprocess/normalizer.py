
import re
from typing import List, Callable

# 尝试导入nltk词干提取器，如果不存在则提供简单替代
try:
    from nltk.stem import PorterStemmer
    STEMMER_AVAILABLE = True
except ImportError:
    STEMMER_AVAILABLE = False


class Normalizer:
    """文本规范化处理器，提供词干提取和其他文本规范化功能"""

    def __init__(self, use_stemming: bool = True, filter_digits: bool = False):
       
        self.use_stemming = use_stemming and STEMMER_AVAILABLE
        self.filter_digits = filter_digits
        
        # 初始化词干提取器
        if self.use_stemming:
            self.stemmer = PorterStemmer()
            
        # 数字匹配模式
        self.digit_pattern = re.compile(r'^\d+$')
        
    def normalize(self, tokens: List[str]) -> List[str]:
       
        # 过滤纯数字
        if self.filter_digits:
            tokens = [token for token in tokens if not self.digit_pattern.match(token)]
            
        # 应用词干提取
        if self.use_stemming:
            tokens = [self.stemmer.stem(token) for token in tokens]
            
        return tokens
    
    def apply_custom_filter(self, tokens: List[str], filter_func: Callable[[str], bool]) -> List[str]:
       
        return [token for token in tokens if filter_func(token)]
        

class SimpleNormalizer:
    """简单规范化处理器，不依赖nltk"""
    
    def __init__(self, filter_digits: bool = False):
        
        self.filter_digits = filter_digits
        self.digit_pattern = re.compile(r'^\d+$')
        
    def normalize(self, tokens: List[str]) -> List[str]:
        
        # 过滤纯数字
        if self.filter_digits:
            tokens = [token for token in tokens if not self.digit_pattern.match(token)]
            
        return tokens
