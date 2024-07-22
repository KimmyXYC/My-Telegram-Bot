import re
import emoji


def escape_md_v2_text(text):
    escape_chars = r'\*_{}\[\]()#+-.!'
    return re.sub(r'(['+escape_chars+'])', r'\\\1', text)


def remove_emoji(string):
    return emoji.replace_emoji(string, replace="")
