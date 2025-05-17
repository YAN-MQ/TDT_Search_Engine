
import re
from typing import List, Tuple, Dict

from preprocess.tokenizer import Tokenizer


class QueryParser:
    """查询解析器，将用户查询解析为自由文本和短语"""

    def __init__(self, tokenizer: Tokenizer):
        
        self.tokenizer = tokenizer
        self.phrase_pattern = re.compile(r'"([^"]*)"')
        
    def parse(self, query_text: str) -> Dict[str, List]:
        
        if not query_text:
            return {'terms': [], 'phrases': []}
        
        # 提取短语
        phrases = []
        for phrase_match in self.phrase_pattern.finditer(query_text):
            phrase = phrase_match.group(1)
            if phrase:
                phrases.append(self.tokenizer.tokenize_phrase(phrase))
                
        # 移除短语部分，处理剩余文本
        free_text = self.phrase_pattern.sub('', query_text)
        terms = self.tokenizer.tokenize_query(free_text)
        
        return {
            'terms': terms,
            'phrases': phrases
        }
        
    def format_query(self, parsed_query: Dict[str, List]) -> str:
      
        result = []
        
        if parsed_query.get('terms'):
            terms_str = ' '.join(parsed_query['terms'])
            result.append(f"自由词项: {terms_str}")
            
        if parsed_query.get('phrases'):
            for i, phrase in enumerate(parsed_query['phrases']):
                phrase_str = ' '.join(phrase)
                result.append(f"短语{i+1}: \"{phrase_str}\"")
                
        return '\n'.join(result) if result else "查询为空"


def is_exact_match(doc_positions: List[int], phrase_length: int) -> bool:
  
    if len(doc_positions) < phrase_length:
        return False
        
    # 排序位置
    doc_positions.sort()
    
    # 检查连续位置
    for i in range(len(doc_positions) - phrase_length + 1):
        if doc_positions[i + phrase_length - 1] - doc_positions[i] == phrase_length - 1:
            return True
            
    return False
