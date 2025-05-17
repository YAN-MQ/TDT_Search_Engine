import os
import re

def fix_relative_imports(filepath):
    """修复文件中的相对导入"""
    try:
        # 读取文件内容
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换相对导入 (..package_name -> package_name)
        modified_content = re.sub(r'from \.\.([\w.]+) import', r'from \1 import', content)
        
        # 如果内容有变化，保存文件
        if content != modified_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"已修复相对导入: {filepath}")
            return True
        else:
            print(f"无需修复: {filepath}")
            return False
    except Exception as e:
        print(f"处理文件时出错 ({filepath}): {e}")
        return False

def process_directory(directory):
    """处理目录中的所有.py文件"""
    fixed_count = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                print(f"\n检查文件: {filepath}")
                if fix_relative_imports(filepath):
                    fixed_count += 1
    
    print(f"\n处理完成: {fixed_count} 个文件的导入已修复")

def fix_specific_files():
    """修复特定的已知问题文件"""
    files_to_fix = [
        'search/query_parser.py',
        'search/retriever.py',
        'search/scorer.py'
    ]
    
    fixed_count = 0
    for file in files_to_fix:
        if os.path.exists(file):
            print(f"\n检查特定文件: {file}")
            if fix_relative_imports(file):
                fixed_count += 1
    
    print(f"\n特定文件处理完成: {fixed_count} 个文件的导入已修复")

if __name__ == "__main__":
    # 首先修复特定的已知问题文件
    fix_specific_files()
    
    # 然后处理所有文件
    process_directory('.') 