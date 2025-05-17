import os
import chardet

def check_and_fix_file(filepath):
    """检查文件编码并尝试修复编码问题"""
    try:
        # 以二进制模式读取文件内容
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # 检查是否包含空字节
        if b'\x00' in content:
            print(f"发现空字节 ({filepath})")
            # 移除空字节
            content = content.replace(b'\x00', b'')
            
            # 检测编码
            result = chardet.detect(content)
            encoding = result['encoding']
            confidence = result['confidence']
            print(f"检测到编码: {encoding} (置信度: {confidence})")
            
            # 尝试解码然后重新编码为UTF-8
            try:
                decoded = content.decode(encoding or 'utf-8', errors='replace')
                
                # 重写文件
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(decoded)
                print(f"已修复: {filepath}")
                return True
            except Exception as e:
                print(f"解码失败 ({filepath}): {e}")
                return False
        else:
            print(f"文件正常 ({filepath})")
            return True
    except Exception as e:
        print(f"处理文件时出错 ({filepath}): {e}")
        return False

def process_directory(directory):
    """处理目录中的所有.py文件"""
    success_count = 0
    failed_count = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                print(f"\n检查文件: {filepath}")
                if check_and_fix_file(filepath):
                    success_count += 1
                else:
                    failed_count += 1
    
    print(f"\n处理完成: {success_count} 个文件修复成功, {failed_count} 个文件失败")

if __name__ == "__main__":
    # 处理当前目录及其子目录
    process_directory('.') 