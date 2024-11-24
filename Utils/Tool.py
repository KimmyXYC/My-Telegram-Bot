import re
import emoji
import pandas as pd


def escape_md_v2_text(text):
    escape_chars = r'\*_{}\[\]()#+-.!'
    return re.sub(r'(['+escape_chars+'])', r'\\\1', text)


def remove_emoji(string):
    return emoji.replace_emoji(string, replace="")


def get_csv_data_list():
    df = pd.read_csv('res/csv/data.csv', encoding='utf-8')

    country_list = df['Country'].tolist()
    weight_list = df['Weight'].tolist()

    return country_list, weight_list
