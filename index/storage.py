"""
存储倒排索引的数据结构
"""
import json
import pickle
import os
import time
import threading
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional, Any

# 导入配置
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class IndexStorage:
    """用于存储和管理倒排索引的类"""

    def __init__(self, index_path: str = "index_data.pkl"):
        """
        初始化存储类
        
        Args:
            index_path: 索引文件存储路径
        """
        self.index_path = index_path
        self.index = {}  # 倒排索引: term -> {docID: {tf, positions}}
        self.doc_lengths = {}  # 文档长度: docID -> length
        self.total_docs = 0  # 文档总数
        self.vocabulary = set()  # 词汇表
        
        # 添加写入缓冲区和锁
        self._write_buffer = defaultdict(lambda: defaultdict(lambda: {"tf": 0, "positions": []}))
        self._buffer_size = 0
        self._buffer_lock = threading.Lock()
        self._max_buffer_size = config.INDEX_BUFFER_SIZE  # 从配置读取缓冲区大小
        self._last_flush_time = time.time()
        self._flush_interval = config.INDEX_FLUSH_INTERVAL  # 从配置读取刷新间隔

    def add_term(self, term: str, doc_id: str, position: int) -> None:
        """
        向索引中添加一个词项
        
        Args:
            term: 词项
            doc_id: 文档ID
            position: 词项在文档中的位置
        """
        # 添加到写入缓冲区
        with self._buffer_lock:
            self._write_buffer[term][doc_id]["tf"] += 1
            self._write_buffer[term][doc_id]["positions"].append(position)
            self._buffer_size += 1
            
            # 如果缓冲区满或者距离上次刷新时间过长，则刷新到主索引
            current_time = time.time()
            if (self._buffer_size >= self._max_buffer_size or 
                current_time - self._last_flush_time >= self._flush_interval):
                self._flush_buffer()

    def _flush_buffer(self) -> None:
        """将缓冲区中的数据刷新到主索引"""
        for term, docs in self._write_buffer.items():
            if term not in self.index:
                self.index[term] = {}
                self.vocabulary.add(term)
                
            for doc_id, data in docs.items():
                if doc_id not in self.index[term]:
                    self.index[term][doc_id] = {"tf": 0, "positions": []}
                    
                self.index[term][doc_id]["tf"] += data["tf"]
                self.index[term][doc_id]["positions"].extend(data["positions"])
                
        # 清空缓冲区
        self._write_buffer.clear()
        self._buffer_size = 0
        self._last_flush_time = time.time()

    def update_doc_length(self, doc_id: str, length: int) -> None:
        """
        更新文档长度信息
        
        Args:
            doc_id: 文档ID
            length: 文档中的词项数量
        """
        self.doc_lengths[doc_id] = length

    def get_term_info(self, term: str) -> Dict[str, Dict[str, Any]]:
        """
        获取词项的索引信息
        
        Args:
            term: 要查询的词项
            
        Returns:
            包含词项的倒排索引信息的字典
        """
        # 确保所有数据都已刷新到主索引
        with self._buffer_lock:
            if term in self._write_buffer:
                self._flush_buffer()
                
        if term in self.index:
            return self.index[term]
        return {}

    def get_docs_with_terms(self, terms: List[str]) -> Set[str]:
        """
        获取包含所有给定词项的文档ID集合
        
        Args:
            terms: 词项列表
            
        Returns:
            包含所有词项的文档ID集合
        """
        # 先刷新缓冲区
        flush_needed = False
        with self._buffer_lock:
            for term in terms:
                if term in self._write_buffer:
                    flush_needed = True
                    break
            
            if flush_needed:
                self._flush_buffer()
                
        if not terms:
            return set()
            
        docs = set()
        first = True
        
        for term in terms:
            if term in self.index:
                if first:
                    docs = set(self.index[term].keys())
                    first = False
                else:
                    docs = docs.intersection(set(self.index[term].keys()))
            else:
                return set()  # 如果有一个词项不存在，则返回空集
                
        return docs

    def get_doc_frequency(self, term: str) -> int:
        """
        获取词项的文档频率
        
        Args:
            term: 词项
            
        Returns:
            包含该词项的文档数量
        """
        # 确保所有数据都已刷新到主索引
        with self._buffer_lock:
            if term in self._write_buffer:
                self._flush_buffer()
                
        if term in self.index:
            return len(self.index[term])
        return 0

    def save_index(self) -> None:
        """将索引保存到文件"""
        # 确保所有缓冲区数据都已刷新
        with self._buffer_lock:
            if self._buffer_size > 0:
                self._flush_buffer()
        
        # 创建目录（如果不存在）
        index_dir = os.path.dirname(self.index_path)
        if index_dir and not os.path.exists(index_dir):
            os.makedirs(index_dir)
            
        print(f"正在保存索引到 {self.index_path}...")
        start_time = time.time()
        
        with open(self.index_path, 'wb') as f:
            data = {
                'index': self.index,
                'doc_lengths': self.doc_lengths,
                'total_docs': self.total_docs,
                'vocabulary': self.vocabulary
            }
            pickle.dump(data, f)
            
        end_time = time.time()
        print(f"索引已保存，用时 {end_time - start_time:.2f} 秒")
            
    def load_index(self) -> bool:
        """
        从文件加载索引
        
        Returns:
            加载是否成功
        """
        if not os.path.exists(self.index_path):
            return False
            
        print(f"正在加载索引 {self.index_path}...")
        start_time = time.time()
        
        try:
            with open(self.index_path, 'rb') as f:
                data = pickle.load(f)
                self.index = data['index']
                self.doc_lengths = data['doc_lengths']
                self.total_docs = data['total_docs']
                self.vocabulary = data['vocabulary']
                
            end_time = time.time()
            print(f"索引加载完成，包含 {len(self.vocabulary)} 个词项，{self.total_docs} 个文档，用时 {end_time - start_time:.2f} 秒")
            return True
        except (FileNotFoundError, KeyError) as e:
            print(f"加载索引失败: {e}")
            return False

    def get_term_positions(self, term: str, doc_id: str) -> List[int]:
        """
        获取指定词项在指定文档中的位置列表
        
        Args:
            term: 词项
            doc_id: 文档ID
            
        Returns:
            位置列表
        """
        # 确保所有数据都已刷新到主索引
        with self._buffer_lock:
            if term in self._write_buffer and doc_id in self._write_buffer[term]:
                self._flush_buffer()
                
        if term in self.index and doc_id in self.index[term]:
            return self.index[term][doc_id]["positions"]
        return []

    def batch_add_terms(self, term_doc_positions: Dict[str, Dict[str, List[int]]]) -> None:
        """
        批量添加词项
        
        Args:
            term_doc_positions: 格式为 {term: {doc_id: [positions]}}
        """
        with self._buffer_lock:
            for term, doc_data in term_doc_positions.items():
                for doc_id, positions in doc_data.items():
                    for position in positions:
                        self._write_buffer[term][doc_id]["tf"] += 1
                        self._write_buffer[term][doc_id]["positions"].append(position)
                        self._buffer_size += 1
                        
            # 如果缓冲区满，则刷新到主索引
            if self._buffer_size >= self._max_buffer_size:
                self._flush_buffer()
