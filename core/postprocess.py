"""
改写结果后处理模块
功能：标题优化、导语规范化、正文清理
"""

import re
from typing import Dict, Tuple
from loguru import logger


class RewritePostProcessor:
    """改写结果后处理器"""
    
    def __init__(self):
        """初始化后处理器"""
        logger.info("RewritePostProcessor initialized")
    
    def process(self, title: str, lead: str, body: str, column_id: str) -> Dict[str, str]:
        """
        统一后处理入口
        
        Args:
            title: 原始标题
            lead: 原始导语
            body: 原始正文
            column_id: 栏目ID
            
        Returns:
            处理后的结果字典
        """
        processed_title = self._process_title(title, column_id)
        processed_lead = self._process_lead(lead)
        processed_body = self._process_body(body)
        
        logger.debug(f"Post-processing complete: title={processed_title[:20]}...")
        
        return {
            'title': processed_title,
            'lead': processed_lead,
            'body': processed_body
        }
    
    def _process_title(self, title: str, column_id: str) -> str:
        """
        标题后处理
        
        规则：
        1. 去除感叹号
        2. 经济数据类栏目数字前置
        3. 长度控制（8-15字）
        
        Args:
            title: 原始标题
            column_id: 栏目ID
            
        Returns:
            处理后的标题
        """
        if not title:
            return ""
        
        # 1. 去除感叹号
        title = title.replace('!', '').replace('！', '')
        
        # 2. 数字前置（仅限经济数据类栏目）
        if column_id == 'economic_data':
            title = self._move_number_to_front(title)
        
        # 3. 长度控制
        if len(title) > 15:
            title = title[:15] + '...'
        elif len(title) < 5:
            # 标题过短，记录警告
            logger.warning(f"Title too short: {title}")
        
        return title.strip()
    
    def _move_number_to_front(self, title: str) -> str:
        """
        将标题中的第一个数字移到最前面
        
        示例：
        "山东省烟草销售45.2万箱" -> "45.2万箱：山东省烟草销售创新高"
        
        Args:
            title: 原始标题
            
        Returns:
            数字前置的标题
        """
        # 匹配数字模式：整数/小数 + 可选单位
        pattern = r'(\d+\.?\d*[万亿千百]?[箱元件人%]?)'
        match = re.search(pattern, title)
        
        if match:
            number = match.group(1)
            # 移除原位置的数字
            rest = title.replace(number, '', 1).strip()
            # 移除可能的冒号
            rest = rest.lstrip('：:').strip()
            # 重组：数字 + 冒号 + 其余部分
            title = f"{number}：{rest}"
        
        return title
    
    def _process_lead(self, lead: str) -> str:
        """
        导语后处理
        
        规则：
        1. 字数控制（40-80字）
        2. 标点规范化
        3. 去除多余空格
        
        Args:
            lead: 原始导语
            
        Returns:
            处理后的导语
        """
        if not lead:
            return ""
        
        # 1. 去除多余空格
        lead = ' '.join(lead.split())
        
        # 2. 字数控制
        if len(lead) < 40:
            logger.warning(f"Lead too short ({len(lead)} chars): {lead[:30]}...")
        elif len(lead) > 80:
            # 智能截断：优先在句号处截断
            lead = self._smart_truncate(lead, 80)
        
        # 3. 标点规范化
        lead = self._normalize_punctuation(lead)
        
        return lead.strip()
    
    def _process_body(self, body: str) -> str:
        """
        正文后处理
        
        规则：
        1. 去除空段落
        2. 段落间统一为双换行
        3. 标点规范化
        4. 去除首尾空白
        
        Args:
            body: 原始正文
            
        Returns:
            处理后的正文
        """
        if not body:
            return ""
        
        # 1. 分段并去除空段落
        paragraphs = [p.strip() for p in body.split('\n') if p.strip()]
        
        # 2. 标点规范化
        paragraphs = [self._normalize_punctuation(p) for p in paragraphs]
        
        # 3. 重新组合，段落间双换行
        body = '\n\n'.join(paragraphs)
        
        return body
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """
        智能截断文本
        
        优先在句号、问号、感叹号处截断
        
        Args:
            text: 待截断文本
            max_length: 最大长度
            
        Returns:
            截断后的文本
        """
        if len(text) <= max_length:
            return text
        
        # 在max_length附近查找句号
        truncated = text[:max_length]
        
        # 查找最后一个句号的位置
        last_period = max(
            truncated.rfind('。'),
            truncated.rfind('！'),
            truncated.rfind('？')
        )
        
        if last_period > max_length * 0.7:  # 句号位置不能太靠前
            return truncated[:last_period + 1]
        else:
            # 没有合适的句号，直接截断并加省略号
            return truncated[:max_length - 3] + '...'
    
    def _normalize_punctuation(self, text: str) -> str:
        """
        标点规范化
        
        规则：
        1. 去除重复标点（。。 -> 。）
        2. 统一使用中文标点
        
        Args:
            text: 待处理文本
            
        Returns:
            规范化后的文本
        """
        # 去除重复标点
        text = re.sub(r'。+', '。', text)
        text = re.sub(r'，+', '，', text)
        text = re.sub(r'！+', '！', text)
        text = re.sub(r'？+', '？', text)
        
        # 英文标点转中文（常见情况）
        replacements = {
            ',': '，',
            ';': '；',
            ':': '：',
            '!': '！',
            '?': '？'
        }
        
        for eng, chn in replacements.items():
            # 只替换非URL和非数字上下文中的标点
            # 避免误替换 http://example.com 或 3,000
            text = re.sub(f'(?<![:/\\d]){re.escape(eng)}(?![:/\\d])', chn, text)
        
        return text


# 便捷函数
def postprocess_rewrite(title: str, lead: str, body: str, column_id: str) -> Dict[str, str]:
    """
    快捷后处理函数
    
    Args:
        title: 标题
        lead: 导语
        body: 正文
        column_id: 栏目ID
        
    Returns:
        处理后的结果
    """
    processor = RewritePostProcessor()
    return processor.process(title, lead, body, column_id)
