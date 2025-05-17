
import re
import os
from typing import List, Dict, Set, Tuple, Optional


class SnippetGenerator:
    """摘要生成器，根据查询词从文档中生成摘要"""

    def __init__(self, doc_content_provider, context_size: int = 100, 
                 max_snippet_length: int = 250):
      
        self.doc_content_provider = doc_content_provider
        self.context_size = context_size
        self.max_snippet_length = max_snippet_length
        
    def _get_doc_content(self, doc_id: str) -> Optional[str]:
       
        # 如果是字典
        if isinstance(self.doc_content_provider, dict):
            return self.doc_content_provider.get(doc_id)
            
        # 如果是函数
        elif callable(self.doc_content_provider):
            return self.doc_content_provider(doc_id)
            
        return None
        
    def generate_snippet(self, doc_id: str, query_terms: List[str]) -> str:
        
        # 获取文档内容
        content = self._get_doc_content(doc_id)
        if not content:
            return "无法获取文档内容"
            
        # 转换为小写进行匹配
        content_lower = content.lower()
        query_terms_lower = [term.lower() for term in query_terms]
        
        # 查找所有查询词的位置
        positions = []
        for term in query_terms_lower:
            term_pos = 0
            while True:
                term_pos = content_lower.find(term, term_pos)
                if term_pos == -1:
                    break
                positions.append((term_pos, term_pos + len(term)))
                term_pos += 1
                
        # 如果没有找到查询词，返回文档开始部分
        if not positions:
            return content[:self.max_snippet_length] + "..."
            
        # 按位置排序
        positions.sort()
        
        # 合并重叠或临近的位置
        merged_positions = []
        current_start, current_end = positions[0]
        
        for start, end in positions[1:]:
            if start <= current_end + self.context_size:
                # 合并重叠或临近区间
                current_end = max(current_end, end)
            else:
                # 添加当前区间并开始新区间
                merged_positions.append((current_start, current_end))
                current_start, current_end = start, end
                
        merged_positions.append((current_start, current_end))
        
        # 选择最佳的匹配段落
        start, end = merged_positions[0]
        
        # 扩展上下文
        snippet_start = max(0, start - self.context_size)
        snippet_end = min(len(content), end + self.context_size)
        
        # 如果摘要太长，尝试截断
        if snippet_end - snippet_start > self.max_snippet_length:
            # 尝试平衡前后上下文
            half_length = self.max_snippet_length // 2
            term_center = (start + end) // 2
            snippet_start = max(0, term_center - half_length)
            snippet_end = min(len(content), snippet_start + self.max_snippet_length)
            
        # 提取摘要
        snippet = content[snippet_start:snippet_end]
        
        # 添加省略号
        if snippet_start > 0:
            snippet = "..." + snippet
        if snippet_end < len(content):
            snippet = snippet + "..."
            
        return snippet
        
    def highlight_terms(self, snippet: str, query_terms: List[str]) -> str:
      
        highlighted = snippet
        for term in sorted(query_terms, key=len, reverse=True):
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted = pattern.sub(f"<b>{term}</b>", highlighted)
            
        return highlighted


class FileBasedSnippetGenerator(SnippetGenerator):
    """基于文件的摘要生成器，直接从文件读取文档内容"""
    
    def __init__(self, corpus_path: str, context_size: int = 100,
                 max_snippet_length: int = 250):
        
        super().__init__(None, context_size, max_snippet_length)
        self.corpus_path = corpus_path
        self.doc_id_to_file_map = {}
        self._build_file_map()
        
    def _build_file_map(self):
        """建立文档ID到文件路径的映射"""
        print(f"建立文档ID到文件路径的映射...")
        
        if not os.path.exists(self.corpus_path):
            print(f"错误: 语料库路径{self.corpus_path}不存在")
            return
            
        if os.path.isdir(self.corpus_path):
            for root, _, files in os.walk(self.corpus_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    self._process_file(file_path)
                    
        else:
            self._process_file(self.corpus_path)
            
        print(f"映射建立完成，共有{len(self.doc_id_to_file_map)}个文档")
        
    def _process_file(self, file_path: str):
        """处理单个文件，提取文档ID并建立映射"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # 查找<DOC>标签及其ID，修改正则表达式以匹配TDT3语料库的格式
            doc_matches = re.finditer(r'<DOC>.*?<DOCNO>\s*(.*?)\s*</DOCNO>', content, re.DOTALL)
            for match in doc_matches:
                doc_id = match.group(1).strip()
                self.doc_id_to_file_map[doc_id] = file_path
                
        except Exception as e:
            print(f"处理文件{file_path}时出错: {e}")
            
    def _get_doc_content(self, doc_id: str) -> Optional[str]:
       
        if doc_id not in self.doc_id_to_file_map:
            return None
            
        file_path = self.doc_id_to_file_map[doc_id]
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # 提取特定文档ID的内容，修改正则表达式以匹配TDT3语料库的格式
            doc_pattern = re.compile(
                r'<DOC>.*?<DOCNO>\s*' + re.escape(doc_id) + r'\s*</DOCNO>(.*?)</DOC>',
                re.DOTALL
            )
            match = doc_pattern.search(content)
            if match:
                text_pattern = re.compile(r'<TEXT>(.*?)</TEXT>', re.DOTALL)
                text_match = text_pattern.search(match.group(1))
                
                if text_match:
                    # 提取<TEXT>标签中的内容
                    doc_content = text_match.group(1)
                else:
                    # 如果没有<TEXT>标签，使用整个文档内容
                    doc_content = match.group(1)
                    
                # 移除其他可能的XML标签
                doc_content = re.sub(r'<[^>]+>', '', doc_content)
                
                # 规范化空白字符
                doc_content = re.sub(r'\s+', ' ', doc_content)
                
                return doc_content.strip()
                
        except Exception as e:
            print(f"从文件{file_path}获取文档{doc_id}内容时出错: {e}")
            
        return None 