
import math
from typing import Dict, List, Set, Tuple

from index.storage import IndexStorage
from .query_parser import is_exact_match


class TfIdfScorer:
    """TF-IDF评分器，计算查询与文档的相关性"""

    def __init__(self, storage: IndexStorage, k1: float = 1.5, b: float = 0.75, 
                 phrase_boost: float = 2.0):
      
        self.storage = storage
        self.k1 = k1
        self.b = b
        self.phrase_boost = phrase_boost
        
        # 计算平均文档长度
        self.avg_doc_length = 0
        if self.storage.doc_lengths:
            self.avg_doc_length = sum(self.storage.doc_lengths.values()) / len(self.storage.doc_lengths)
    
    def _calc_idf(self, term: str) -> float:
      
        df = self.storage.get_doc_frequency(term)
        if df == 0:
            return 0
            
        # 添加平滑处理
        n = self.storage.total_docs
        return math.log((n - df + 0.5) / (df + 0.5) + 1)
        
    def _calc_tf_score(self, term: str, doc_id: str) -> float:
       
        term_info = self.storage.get_term_info(term)
        if not term_info or doc_id not in term_info:
            return 0
            
        tf = term_info[doc_id]['tf']
        
        # 基本TF-IDF
        # return tf * self._calc_idf(term)
        
        # 使用BM25公式
        doc_len = self.storage.doc_lengths.get(doc_id, self.avg_doc_length)
        numerator = tf * (self.k1 + 1)
        denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
        
        return numerator / denominator if denominator != 0 else 0
        
    def score_term(self, term: str, doc_id: str) -> float:
        
        tf_score = self._calc_tf_score(term, doc_id)
        idf = self._calc_idf(term)
        return tf_score * idf
        
    def score_document(self, terms: List[str], phrases: List[List[str]], doc_id: str) -> float:
      
        score = 0.0
        
        # 计算自由词项得分
        for term in terms:
            score += self.score_term(term, doc_id)
            
        # 计算短语得分（带加权）
        for phrase in phrases:
            if not phrase:
                continue
                
            # 单独计算短语中每个词项的得分
            phrase_score = 0.0
            for term in phrase:
                phrase_score += self.score_term(term, doc_id)
                
            # 检查是否存在精确短语匹配
            first_term = phrase[0]
            if first_term in self.storage.index and doc_id in self.storage.index[first_term]:
                # 收集第一个词项的位置
                positions = []
                for i in range(1, len(phrase)):
                    if i < len(phrase):
                        term = phrase[i]
                        if term in self.storage.index and doc_id in self.storage.index[term]:
                            # 对位置加上偏移量，使其与第一个词的位置可比较
                            pos_with_offset = [p + i for p in self.storage.index[term][doc_id]['positions']]
                            positions.extend(pos_with_offset)
                
                # 检查是否有精确匹配
                if is_exact_match(positions, len(phrase)):
                    phrase_score *= self.phrase_boost
                    
            score += phrase_score
            
        return score


class BooleanScorer:
    """布尔评分器，实现简单的布尔检索"""
    
    def __init__(self, storage: IndexStorage):
        
        self.storage = storage
        
    def score_document(self, terms: List[str], phrases: List[List[str]], doc_id: str) -> float:
       
        # 检查所有词项是否都在文档中出现
        for term in terms:
            term_info = self.storage.get_term_info(term)
            if not term_info or doc_id not in term_info:
                return 0.0
                
        # 检查所有短语是否都在文档中出现
        for phrase in phrases:
            if not phrase:
                continue
                
            # 检查所有词项是否在文档中
            phrase_terms_present = True
            for term in phrase:
                term_info = self.storage.get_term_info(term)
                if not term_info or doc_id not in term_info:
                    phrase_terms_present = False
                    break
                    
            if not phrase_terms_present:
                return 0.0
                
            # 检查是否有精确短语匹配
            first_term = phrase[0]
            if first_term in self.storage.index and doc_id in self.storage.index[first_term]:
                positions = []
                for i in range(1, len(phrase)):
                    if i < len(phrase):
                        term = phrase[i]
                        if term in self.storage.index and doc_id in self.storage.index[term]:
                            pos_with_offset = [p + i for p in self.storage.index[term][doc_id]['positions']]
                            positions.extend(pos_with_offset)
                
                if not is_exact_match(positions, len(phrase)):
                    return 0.0
                    
        # 所有条件都满足
        return 1.0
