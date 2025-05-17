# -*- coding: utf-8 -*-
import os
import sys
import argparse
import time
from typing import Dict, List, Any

from index.storage import IndexStorage
from index.indexer import Indexer
from preprocess.tokenizer import Tokenizer
from preprocess.normalizer import Normalizer
from search.query_parser import QueryParser
from search.scorer import TfIdfScorer
from search.retriever import Retriever
from utils.file_loader import DocumentLoader
from utils.snippet import SnippetGenerator
import config


def setup_argparse() -> argparse.ArgumentParser:
    """
    设置命令行参数解析
    
    Returns:
        参数解析器
    """
    parser = argparse.ArgumentParser(description="TDT3搜索引擎")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 索引子命令
    index_parser = subparsers.add_parser("index", help="构建索引")
    index_parser.add_argument("--corpus", default=config.CORPUS_PATH, help="TDT3语料库路径")
    index_parser.add_argument("--output", default=config.INDEX_PATH, help="索引输出路径")
    index_parser.add_argument("--threads", type=int, default=0, help="处理线程数，0表示自动选择")
    
    # 搜索子命令
    search_parser = subparsers.add_parser("search", help="搜索查询")
    search_parser.add_argument("query", nargs='+', help="查询文本")
    search_parser.add_argument("--index", default=config.INDEX_PATH, help="索引文件路径")
    search_parser.add_argument("--top", type=int, default=config.TOP_N, help="返回结果数量")
    search_parser.add_argument("--corpus", default=config.CORPUS_PATH, help="TDT3语料库路径（用于生成摘要）")
    
    # 交互式模式
    interactive_parser = subparsers.add_parser("interactive", help="交互式模式")
    interactive_parser.add_argument("--index", default=config.INDEX_PATH, help="索引文件路径")
    interactive_parser.add_argument("--corpus", default=config.CORPUS_PATH, help="TDT3语料库路径（用于生成摘要）")
    
    return parser


def build_index(corpus_path: str, index_path: str, threads: int = 0) -> None:
    """
    构建索引
    
    Args:
        corpus_path: 语料库路径
        index_path: 索引输出路径
        threads: 处理线程数，0表示自动选择
    """
    start_time = time.time()
    print(f"正在从 {corpus_path} 构建索引...")
    
    # 初始化组件
    storage = IndexStorage(index_path)
    tokenizer = Tokenizer(
        remove_stopwords=config.REMOVE_STOPWORDS,
        case_sensitive=config.CASE_SENSITIVE,
        remove_punctuation=config.REMOVE_PUNCTUATION
    )
    normalizer = Normalizer(
        use_stemming=config.USE_STEMMING,
        filter_digits=config.FILTER_DIGITS
    )
    
    # 加载文档
    print("正在加载文档...")
    loader = DocumentLoader(corpus_path)
    documents = loader.load_documents()
    
    if not documents:
        print("错误: 未能加载任何文档")
        return
    
    # 设置线程数
    if threads > 0:
        os.environ["INDEXER_THREADS"] = str(threads)
    
    # 构建索引
    print(f"开始构建索引，文档数: {len(documents)}")
    indexer = Indexer(storage, tokenizer)
    indexer.build_index(documents)
    
    end_time = time.time()
    total_time = end_time - start_time
    docs_per_second = len(documents) / total_time
    
    print(f"索引构建完成，已保存到 {index_path}")
    print(f"总耗时: {total_time:.2f}秒，平均处理速度: {docs_per_second:.2f}文档/秒")
    print(f"索引大小: {len(storage.vocabulary)}个词项, {storage.total_docs}个文档")


def search(query: str, index_path: str, corpus_path: str = None, top_n: int = 10) -> List[Dict[str, Any]]:
    """
    执行搜索查询
    
    Args:
        query: 查询文本
        index_path: 索引文件路径
        corpus_path: 语料库路径，用于生成摘要
        top_n: 返回结果数量
        
    Returns:
        搜索结果列表
    """
    # 初始化组件
    storage = IndexStorage(index_path)
    if not storage.load_index():
        print(f"错误: 无法加载索引文件 {index_path}")
        return []
        
    tokenizer = Tokenizer(
        remove_stopwords=config.REMOVE_STOPWORDS,
        case_sensitive=config.CASE_SENSITIVE,
        remove_punctuation=config.REMOVE_PUNCTUATION
    )
    query_parser = QueryParser(tokenizer)
    scorer = TfIdfScorer(
        storage, 
        k1=config.K1, 
        b=config.B, 
        phrase_boost=config.PHRASE_BOOST
    )
    
    # 如果提供了语料库路径，创建摘要生成器
    snippet_generator = None
    if corpus_path and os.path.exists(corpus_path):
        # 尝试加载文档内容
        try:
            documents = {}
            loader = DocumentLoader(corpus_path)
            documents = loader.load_documents()
            if documents:
                snippet_generator = SnippetGenerator(
                    documents,
                    context_size=config.CONTEXT_SIZE,
                    max_snippet_length=config.MAX_SNIPPET_LENGTH
                )
        except Exception as e:
            print(f"警告: 无法加载文档内容用于生成摘要: {e}")
    
    # 创建检索器
    retriever = Retriever(storage, query_parser, scorer, snippet_generator)
    
    # 执行搜索
    start_time = time.time()
    results = retriever.search(query, top_n=top_n)
    end_time = time.time()
    
    print(f"找到 {len(results)} 个结果，用时 {end_time - start_time:.4f} 秒")
    
    # 显示结果
    if results:
        formatted_results = retriever.format_results(results)
        print(formatted_results)
    else:
        print("未找到匹配的文档")
        
    return results


def interactive_mode(index_path: str, corpus_path: str = None) -> None:
    """
    交互式查询模式
    
    Args:
        index_path: 索引文件路径
        corpus_path: 语料库路径，用于生成摘要
    """
    print("TDT3搜索引擎 - 交互式模式")
    print("输入查询文本进行搜索，输入'exit'或'quit'退出")
    print("提示: 使用双引号\"phrase\"表示短语查询")
    print("-" * 50)
    
    while True:
        try:
            query = input("\n请输入查询 > ")
            query = query.strip()
            
            if not query:
                continue
                
            if query.lower() in ('exit', 'quit'):
                print("退出程序")
                break
                
            # 执行搜索
            search(query, index_path, corpus_path, config.TOP_N)
                
        except KeyboardInterrupt:
            print("\n程序中断，退出")
            break
        except Exception as e:
            print(f"发生错误: {e}")


def main():
    """主函数"""
    parser = setup_argparse()
    args = parser.parse_args()
    
    if args.command == "index":
        build_index(args.corpus, args.output, args.threads)
        
    elif args.command == "search":
        query = ' '.join(args.query)
        search(query, args.index, args.corpus, args.top)
        
    elif args.command == "interactive":
        interactive_mode(args.index, args.corpus)
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
