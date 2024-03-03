import re


def escape_md_v2_text(text):
    escape_chars = r'\*_{}\[\]()#+-.!'
    return re.sub(r'(['+escape_chars+'])', r'\\\1', text)


def remove_emoji(string):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # 表情符号
                               u"\U0001F300-\U0001F5FF"  # 符号和标志
                               u"\U0001F680-\U0001F6FF"  # 交通工具
                               u"\U0001F1E0-\U0001F1FF"  # 国旗
                               u"\U00002702-\U000027B0"  # 杂项符号
                               "]+", flags=re.UNICODE)
    text_without_emojis = emoji_pattern.sub(r'', string)
    return text_without_emojis
