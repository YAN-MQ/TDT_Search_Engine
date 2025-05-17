"""
检索器模块，根据查询返回最相关的文档
"""
import time
from typing import Dict, List, Tuple, Any

from index.storage import IndexStorage
from utils.snippet import SnippetGenerator
from .query_parser import QueryParser
from .scorer import TfIdfScorer


class Retriever:
    """文档检索器，返回与查询最相关的文档"""

    def __init__(self, storage: IndexStorage, query_parser: QueryParser, 
                 scorer: TfIdfScorer, snippet_generator: SnippetGenerator = None):
        """
        初始化检索器
        
        Args:
            storage: 索引存储对象
            query_parser: 查询解析器
            scorer: 文档评分器
            snippet_generator: 摘要生成器
        """
        self.storage = storage
        self.query_parser = query_parser
        self.scorer = scorer
        self.snippet_generator = snippet_generator
        
    def search(self, query_text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        根据查询文本返回最相关的前N个文档
        
        Args:
            query_text: 查询文本
            top_n: 返回文档数量
            
        Returns:
            包含文档ID、得分、摘要的列表
        """
        start_time = time.time()
        
        # 解析查询
        parsed_query = self.query_parser.parse(query_text)
        terms = parsed_query['terms']
        phrases = parsed_query['phrases']
        
        # 如果查询为空，返回空列表
        if not terms and not phrases:
            return []
            
        print(f"查询解析结果: {self.query_parser.format_query(parsed_query)}")
        
        # 找出所有候选文档
        candidate_docs = set()
        
        # 收集所有包含查询词项的文档
        for term in terms:
            term_info = self.storage.get_term_info(term)
            if term_info:
                if not candidate_docs:
                    candidate_docs = set(term_info.keys())
                else:
                    candidate_docs = candidate_docs.union(set(term_info.keys()))
        
        # 收集所有包含短语词项的文档
        for phrase in phrases:
            for term in phrase:
                term_info = self.storage.get_term_info(term)
                if term_info:
                    if not candidate_docs:
                        candidate_docs = set(term_info.keys())
                    else:
                        candidate_docs = candidate_docs.union(set(term_info.keys()))
        
        print(f"找到{len(candidate_docs)}个候选文档")
        
        # 计算每个文档的得分
        doc_scores = []
        for doc_id in candidate_docs:
            score = self.scorer.score_document(terms, phrases, doc_id)
            if score > 0:
                doc_scores.append((doc_id, score))
        
        # 按得分降序排序
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 截取前N个结果
        top_results = doc_scores[:top_n]
        
        # 生成结果列表
        results = []
        for doc_id, score in top_results:
            result = {
                'doc_id': doc_id,
                'score': score
            }
            
            # 如果有摘要生成器，添加摘要
            if self.snippet_generator:
                # 合并所有查询词项
                all_terms = terms.copy()
                for phrase in phrases:
                    all_terms.extend(phrase)
                    
                snippet = self.snippet_generator.generate_snippet(doc_id, all_terms)
                result['snippet'] = snippet
                
            results.append(result)
            
        end_time = time.time()
        print(f"检索完成，用时{end_time - start_time:.4f}秒")
        
        return results
        
    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        格式化搜索结果，用于显示
        
        Args:
            results: 搜索结果列表
            
        Returns:
            格式化的结果字符串
        """
        if not results:
            return "未找到匹配的文档"
            
        # 构建标题行
        header = f"{'排名':<5} | {'得分':<10} | {'文档ID':<15} | 摘要"
        separator = "-" * 100
        
        result_lines = [header, separator]
        
        # 添加每个结果
        for i, result in enumerate(results):
            doc_id = result['doc_id']
            score = result['score']
            snippet = result.get('snippet', '无摘要')
            
            # 限制摘要长度
            if len(snippet) > 60:
                snippet = snippet[:57] + "..."
                
            result_line = f"{i+1:<5} | {score:<10.4f} | {doc_id:<15} | {snippet}"
            result_lines.append(result_line)
            
        return "\n".join(result_lines)
