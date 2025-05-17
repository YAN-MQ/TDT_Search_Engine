import os
import time
import concurrent.futures
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict

from .storage import IndexStorage
from preprocess.tokenizer import Tokenizer
from utils.file_loader import DocumentLoader

# 导入配置
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class Indexer:
    """文档索引器，用于构建倒排索引"""

    def __init__(self, storage: IndexStorage, tokenizer: Tokenizer):
        
        self.storage = storage
        self.tokenizer = tokenizer
        self.doc_count = 0
        # 获取环境变量中设置的线程数，如果有
        self.max_threads = int(os.environ.get("INDEXER_THREADS", config.MAX_THREADS))

    def index_document(self, doc_id: str, content: str) -> Dict[str, List[int]]:
       
        # 分词处理
        tokens = self.tokenizer.tokenize(content)
        
        # 记录词项位置
        term_positions = defaultdict(list)
        for position, token in enumerate(tokens):
            term_positions[token].append(position)
            
        return {
            'tokens': tokens,
            'term_positions': term_positions
        }

    def _process_batch(self, doc_batch: Dict[str, str]) -> Dict[str, Any]:
       
        batch_results = {}
        for doc_id, content in doc_batch.items():
            batch_results[doc_id] = self.index_document(doc_id, content)
        return batch_results

    def build_index(self, documents: Dict[str, str], save: bool = True) -> None:
       
        start_time = time.time()
        print(f"开始为{len(documents)}个文档建立索引...")
        
        # 确定批次大小和线程数
        total_docs = len(documents)
        workers = self.max_threads
        if workers <= 0:
            workers = min(os.cpu_count() or 4, 8)  # 限制最大线程数
            
        batch_size = config.BATCH_SIZE
        if batch_size <= 0:
            batch_size = max(10, total_docs // (workers * 2))  # 每个批次的文档数
        
        # 将文档分成批次
        doc_batches = []
        current_batch = {}
        for i, (doc_id, content) in enumerate(documents.items()):
            current_batch[doc_id] = content
            if len(current_batch) >= batch_size or i == total_docs - 1:
                doc_batches.append(current_batch)
                current_batch = {}
                
        print(f"使用{workers}个线程处理，每批{batch_size}个文档，共{len(doc_batches)}批")
        
        # 使用多线程并行处理文档批次
        indexed_docs = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_batch = {executor.submit(self._process_batch, batch): i for i, batch in enumerate(doc_batches)}
            
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_results = future.result()
                
                # 更新索引数据
                for doc_id, result in batch_results.items():
                    tokens = result['tokens']
                    term_positions = result['term_positions']
                    
                    # 更新文档长度
                    self.storage.update_doc_length(doc_id, len(tokens))
                    
                    # 将词项添加到索引
                    for term, positions in term_positions.items():
                        for position in positions:
                            self.storage.add_term(term, doc_id, position)
                
                # 更新进度
                batch_index = future_to_batch[future]
                indexed_docs += len(doc_batches[batch_index])
                self.doc_count = indexed_docs
                self.storage.total_docs = self.doc_count
                
                if indexed_docs % 1000 == 0 or indexed_docs == total_docs:
                    print(f"已索引{indexed_docs}/{total_docs}个文档 ({indexed_docs/total_docs*100:.1f}%)...")
                
        # 保存索引
        if save:
            self.storage.save_index()
            
        end_time = time.time()
        print(f"索引构建完成，共索引{self.doc_count}个文档，用时{end_time - start_time:.2f}秒")
        print(f"词汇表大小: {len(self.storage.vocabulary)}个词项")


def main(corpus_path: str, index_path: str = "index_data.pkl"):
   
    from preprocess.tokenizer import Tokenizer
    from utils.file_loader import DocumentLoader
    
    # 初始化组件
    storage = IndexStorage(index_path)
    tokenizer = Tokenizer()
    indexer = Indexer(storage, tokenizer)
    
    # 加载文档
    loader = DocumentLoader(corpus_path)
    documents = loader.load_documents()
    
    # 构建索引
    indexer.build_index(documents)
    
    print(f"索引已保存到 {index_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        corpus_path = sys.argv[1]
        main(corpus_path)
    else:
        print("请提供语料库路径")
        sys.exit(1) 