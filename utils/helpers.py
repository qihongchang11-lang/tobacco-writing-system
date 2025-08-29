"""
工具函数模块
提供系统通用的工具函数
"""

import re
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

def generate_id() -> str:
    """生成唯一ID"""
    return str(uuid.uuid4())

def generate_hash(content: str) -> str:
    """生成内容hash值"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def clean_text(text: str) -> str:
    """清理文本内容"""
    if not text:
        return ""
    
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 移除特殊字符（保留中文标点）
    text = re.sub(r'[^\u4e00-\u9fff\w\s\.,;:!?()【】《》""''、。，；：！？（）\-]', '', text)
    
    return text

def split_into_paragraphs(text: str) -> List[str]:
    """将文本按段落分割"""
    if not text:
        return []
    
    # 按换行符分割，过滤空行
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    
    return paragraphs

def extract_title_and_content(text: str) -> tuple[Optional[str], str]:
    """提取标题和正文"""
    if not text:
        return None, ""
    
    lines = text.strip().split('\n')
    if not lines:
        return None, ""
    
    # 假设第一行是标题
    first_line = lines[0].strip()
    
    # 如果第一行很短且不包含句号，可能是标题
    if len(first_line) < 50 and '。' not in first_line:
        title = first_line
        content = '\n'.join(lines[1:]).strip()
    else:
        title = None
        content = text
    
    return title, content

def count_words(text: str) -> int:
    """统计字数（中文字符数）"""
    if not text:
        return 0
    
    # 匹配中文字符
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    return len(chinese_chars)

def calculate_processing_time(start_time: datetime, end_time: Optional[datetime] = None) -> float:
    """计算处理时间（秒）"""
    if end_time is None:
        end_time = datetime.now(timezone.utc)
    
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    
    return (end_time - start_time).total_seconds()

def validate_article_content(content: str, min_length: int = 100) -> tuple[bool, str]:
    """验证文章内容"""
    if not content or not content.strip():
        return False, "文章内容不能为空"
    
    word_count = count_words(content)
    if word_count < min_length:
        return False, f"文章内容太短，至少需要{min_length}字，当前{word_count}字"
    
    return True, "验证通过"

def format_confidence_score(score: float) -> str:
    """格式化置信度分数显示"""
    return f"{score:.1%}"

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def safe_filename(filename: str) -> str:
    """生成安全的文件名"""
    # 移除或替换不安全字符
    safe_chars = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # 限制长度
    if len(safe_chars) > 100:
        name, ext = safe_chars.rsplit('.', 1) if '.' in safe_chars else (safe_chars, '')
        safe_chars = name[:95] + ('.' + ext if ext else '')
    
    return safe_chars

def ensure_file_extension(filename: str, extension: str) -> str:
    """确保文件有正确的扩展名"""
    if not extension.startswith('.'):
        extension = '.' + extension
    
    if not filename.lower().endswith(extension.lower()):
        filename += extension
    
    return filename

class Timer:
    """计时器上下文管理器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed = None
    
    def __enter__(self):
        self.start_time = datetime.now(timezone.utc)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now(timezone.utc)
        self.elapsed = calculate_processing_time(self.start_time, self.end_time)
    
    def get_elapsed(self) -> float:
        """获取已消耗时间"""
        if self.elapsed is not None:
            return self.elapsed
        elif self.start_time is not None:
            return calculate_processing_time(self.start_time)
        else:
            return 0.0

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """重试装饰器，带指数退避"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
            
        return wrapper
    return decorator