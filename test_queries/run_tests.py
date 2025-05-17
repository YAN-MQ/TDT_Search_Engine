
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from index.storage import IndexStorage
from preprocess.tokenizer import Tokenizer
from search.query_parser import QueryParser
from search.scorer import TfIdfScorer
from search.retriever import Retriever
from utils.snippet import SnippetGenerator


# 预定义的测试查询
TEST_QUERIES = [
    "hurricane george",
    "Clinton Lewinsky scandal",
    "\"new york\" bombing",
    "middle east peace process",
    "Asian financial crisis"
]


def save_results_to_file(query: str, results: List[Dict[str, Any]], output_dir: str = "results"):
   
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 为查询生成文件名（替换非法字符）
    filename = query.replace('"', '').replace(' ', '_').lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"{filename}_{timestamp}.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"查询: {query}\n")
        f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"结果数量: {len(results)}\n")
        f.write("-" * 80 + "\n\n")
        
        for i, result in enumerate(results):
            f.write(f"[{i+1}] 文档ID: {result['doc_id']}\n")
            f.write(f"    得分: {result['score']:.4f}\n")
            if 'snippet' in result:
                f.write(f"    摘要: {result['snippet']}\n")
            f.write("\n")
            
    print(f"查询结果已保存到 {output_file}")


def run_test_queries(index_path: str, documents: Dict[str, str] = None, 
                    top_n: int = 10, output_dir: str = "results"):
    
    print(f"加载索引 {index_path}...")
    
    # 初始化组件
    storage = IndexStorage(index_path)
    if not storage.load_index():
        print(f"错误: 无法加载索引文件 {index_path}")
        return
        
    print(f"索引加载完成，包含 {storage.total_docs} 个文档和 {len(storage.vocabulary)} 个词项")
    
    tokenizer = Tokenizer()
    query_parser = QueryParser(tokenizer)
    scorer = TfIdfScorer(storage)
    
    # 如果提供了文档集合，创建摘要生成器
    snippet_generator = None
    if documents:
        snippet_generator = SnippetGenerator(documents)
        
    retriever = Retriever(storage, query_parser, scorer, snippet_generator)
    
    # 运行每个测试查询
    for i, query in enumerate(TEST_QUERIES):
        print(f"\n执行查询 {i+1}/{len(TEST_QUERIES)}: {query}")
        
        start_time = time.time()
        results = retriever.search(query, top_n=top_n)
        end_time = time.time()
        
        print(f"找到 {len(results)} 个结果，用时 {end_time - start_time:.4f} 秒")
        
        # 显示结果
        formatted_results = retriever.format_results(results)
        print(formatted_results)
        
        # 保存结果到文件
        save_results_to_file(query, results, output_dir)
        
        print(f"查询 {i+1} 完成")
        
    print("\n所有测试查询执行完毕")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="运行预定义的测试查询")
    parser.add_argument("--index", required=True, help="索引文件路径")
    parser.add_argument("--docs", help="文档集合路径，用于生成摘要")
    parser.add_argument("--top", type=int, default=10, help="返回结果数量")
    parser.add_argument("--out", default="results", help="输出结果目录")
    
    args = parser.parse_args()
    
    # 如果提供了文档路径，加载文档
    documents = None
    if args.docs:
        from utils.file_loader import DocumentLoader
        print(f"从 {args.docs} 加载文档...")
        loader = DocumentLoader(args.docs)
        documents = loader.load_documents()
        
    # 运行测试查询
    run_test_queries(args.index, documents, args.top, args.out)


if __name__ == "__main__":
    main()
