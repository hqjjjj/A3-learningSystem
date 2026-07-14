# backend/agents/agent_source/security_utils.py
import os
from pathlib import Path

# 敏感词文件路径
SENSITIVE_WORDS_FILE = Path(__file__).parent / "sensitive_words.txt"

# 默认列表
DEFAULT_WORDS = [
    "色情", "暴力", "恐怖", "毒品", "赌博",
    "邪教", "反动", "分裂", "颠覆", "攻击",
    "辱骂", "歧视", "仇恨", "恐吓", "威胁"
]

def load_sensitive_words():
    """从文本文件加载敏感词，每行一个词，忽略空行和首尾空白"""
    words = []
    if SENSITIVE_WORDS_FILE.exists():
        try:
            with open(SENSITIVE_WORDS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word:  # 非空行
                        words.append(word)
        except Exception:
            # 读取失败则使用默认列表
            words = DEFAULT_WORDS.copy()
    else:
        words = DEFAULT_WORDS.copy()
        try:
            with open(SENSITIVE_WORDS_FILE, 'w', encoding='utf-8') as f:
                for w in words:
                    f.write(w + '\n')
        except Exception:
            pass 
    return words


SENSITIVE_WORDS = load_sensitive_words()

def contains_sensitive(text: str) -> bool:
    """检查文本是否包含敏感词"""
    if not isinstance(text, str):
        return False
    for word in SENSITIVE_WORDS:
        if word in text:
            return True
    return False

def filter_sensitive_fields(obj):
    """
    递归过滤字典中特定字段的敏感词：
    检查内容型字段：content, html_content, question, analysis, description, explanation
    若包含敏感词，替换为安全提示
    """
    TARGET_FIELDS = {"content", "html_content", "question", "analysis", "description", "explanation"}

    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            if key in TARGET_FIELDS and isinstance(value, str):
                if contains_sensitive(value):
                    new_dict[key] = "内容安全审核未通过，该部分已被屏蔽。"
                else:
                    new_dict[key] = value
            else:
                new_dict[key] = filter_sensitive_fields(value)
        return new_dict
    elif isinstance(obj, list):
        return [filter_sensitive_fields(item) for item in obj]
    else:
        return obj