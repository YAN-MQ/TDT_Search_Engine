import os
import re
import gzip
import time
import concurrent.futures
from typing import Dict, List, Tuple, Set, Optional, Any

# 导入配置
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class DocumentLoader:
  
    def __init__(self, corpus_path: str):
        
        self.corpus_path = corpus_path
        # 预编译正则表达式并使用更高效的模式
        self.doc_pattern = re.compile(r'<DOC>.*?<DOCNO>\s*(.*?)\s*</DOCNO>(.*?)</DOC>', re.DOTALL)
        self.text_pattern = re.compile(r'<TEXT>(.*?)</TEXT>', re.DOTALL)
        # 添加缓存变量
        self._document_cache = {}
        
    def _extract_doc_content(self, doc_text: str) -> str:
      
        # 尝试提取<TEXT>标签中的内容
        text_match = self.text_pattern.search(doc_text)
        if text_match:
            content = text_match.group(1)
        else:
            # 如果没有<TEXT>标签，使用整个文档内容
            content = doc_text
            
        # 移除其他可能的XML标签
        content = re.sub(r'<[^>]+>', ' ', content)
        
        # 规范化空白字符
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
        
    def load_document(self, file_path: str) -> Dict[str, str]:
       
        # 检查缓存
        if file_path in self._document_cache:
            return self._document_cache[file_path]

        try:
            # 尝试作为gzip文件打开
            if file_path.endswith('.gz'):
                with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
            # 提取所有文档
            documents = {}
            for match in self.doc_pattern.finditer(content):
                doc_id = match.group(1).strip()
                doc_text = match.group(2)
                doc_content = self._extract_doc_content(doc_text)
                
                if doc_content:
                    documents[doc_id] = doc_content
            
            # 保存到缓存
            self._document_cache[file_path] = documents        
            return documents
            
        except Exception as e:
            print(f"加载文件{file_path}时出错: {e}")
            return {}
    
    def _process_batch(self, file_paths: List[str]) -> Dict[str, str]:
        
        results = {}
        for file_path in file_paths:
            doc_dict = self.load_document(file_path)
            results.update(doc_dict)
        return results
            
    def load_documents(self) -> Dict[str, str]:
      
        start_time = time.time()
        documents = {}
        
        # 检查语料库路径是否存在
        if not os.path.exists(self.corpus_path):
            print(f"错误: 语料库路径{self.corpus_path}不存在")
            return documents
            
        # 如果是目录，遍历目录下的所有文件
        if os.path.isdir(self.corpus_path):
            print(f"从目录{self.corpus_path}加载文档...")
            
            # 获取所有文件路径
            all_files = []
            for root, _, files in os.walk(self.corpus_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
            
            total_files = len(all_files)
            print(f"发现{total_files}个文件待处理")
            
            # 使用多线程并行处理文件
            # 从配置文件获取线程数和批量大小
            workers = config.MAX_THREADS
            if workers <= 0:
                workers = min(os.cpu_count() or 4, 16)  # 限制最大线程数
                
            batch_size = config.BATCH_SIZE
            if batch_size <= 0:
                batch_size = max(1, total_files // (workers * 4))  # 每个批次的文件数
            
            # 将文件分成批次
            batches = [all_files[i:i+batch_size] for i in range(0, total_files, batch_size)]
            processed_files = 0
            
            print(f"使用{workers}个线程处理，每批{batch_size}个文件，共{len(batches)}批")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_batch = {executor.submit(self._process_batch, batch): i for i, batch in enumerate(batches)}
                
                for future in concurrent.futures.as_completed(future_to_batch):
                    batch_results = future.result()
                    documents.update(batch_results)
                    
                    processed_files += len(batches[future_to_batch[future]])
                    print(f"已处理{processed_files}/{total_files}个文件，当前文档数: {len(documents)}")
        else:
            # 如果是单个文件，直接加载
            print(f"从文件{self.corpus_path}加载文档...")
            documents = self.load_document(self.corpus_path)
            
        end_time = time.time()
        print(f"文档加载完成，共加载{len(documents)}个文档，用时{end_time - start_time:.2f}秒")
        return documents


def extract_tdt_id(text: str) -> Optional[str]:
   
    id_match = re.search(r'<DOCNO\s*=\s*"([^"]+)"', text)
    if id_match:
        return id_match.group(1).strip()
    return None


def main():
    """主函数，用于测试文档加载器"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python file_loader.py <语料库路径>")
        return
        
    corpus_path = sys.argv[1]
    loader = DocumentLoader(corpus_path)
    documents = loader.load_documents()
    
    print(f"共加载{len(documents)}个文档")
    
    # 显示前5个文档的ID和内容摘要
    count = 0
    for doc_id, content in documents.items():
        print(f"文档ID: {doc_id}")
        print(f"内容摘要: {content[:100]}...")
        print("-" * 50)
        
        count += 1
        if count >= 5:
            break


if __name__ == "__main__":
    main()
