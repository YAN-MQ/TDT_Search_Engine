"""
文本规范化模块，提供词干提取和额外文本处理
"""
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
        """
        初始化规范化处理器
        
        Args:
            use_stemming: 是否使用词干提取
            filter_digits: 是否过滤纯数字词项
        """
        self.use_stemming = use_stemming and STEMMER_AVAILABLE
        self.filter_digits = filter_digits
        
        # 初始化词干提取器
        if self.use_stemming:
            self.stemmer = PorterStemmer()
            
        # 数字匹配模式
        self.digit_pattern = re.compile(r'^\d+$')
        
    def normalize(self, tokens: List[str]) -> List[str]:
        """
        对词项列表进行规范化处理
        
        Args:
            tokens: 输入词项列表
            
        Returns:
            规范化后的词项列表
        """
        # 过滤纯数字
        if self.filter_digits:
            tokens = [token for token in tokens if not self.digit_pattern.match(token)]
            
        # 应用词干提取
        if self.use_stemming:
            tokens = [self.stemmer.stem(token) for token in tokens]
            
        return tokens
    
    def apply_custom_filter(self, tokens: List[str], filter_func: Callable[[str], bool]) -> List[str]:
        """
        应用自定义过滤函数
        
        Args:
            tokens: 输入词项列表
            filter_func: 过滤函数，返回True表示保留该词项
            
        Returns:
            过滤后的词项列表
        """
        return [token for token in tokens if filter_func(token)]
        

class SimpleNormalizer:
    """简单规范化处理器，不依赖nltk"""
    
    def __init__(self, filter_digits: bool = False):
        """
        初始化简单规范化处理器
        
        Args:
            filter_digits: 是否过滤纯数字词项
        """
        self.filter_digits = filter_digits
        self.digit_pattern = re.compile(r'^\d+$')
        
    def normalize(self, tokens: List[str]) -> List[str]:
        """
        对词项列表进行简单规范化处理
        
        Args:
            tokens: 输入词项列表
            
        Returns:
            规范化后的词项列表
        """
        # 过滤纯数字
        if self.filter_digits:
            tokens = [token for token in tokens if not self.digit_pattern.match(token)]
            
        return tokens
