# -*- coding: utf-8 -*-
# @Time： 2023/7/2 14:05 
# @FileName: Parameter.py
# @Software： PyCharm
# @GitHub: KimmyXYC
import json
import pathlib
from loguru import logger


def get_parameter(parameter):
    parameter = str(parameter)
    cmd_dict = get_dict_file()
    return cmd_dict.get(parameter, [])


def get_dict_file():
    with open((str(pathlib.Path.cwd()) + "/Config/lock_cmd.json"), 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        data = dict(data)
        json_file.close()
    return data


def save_config(group_id, value):
    with open((str(pathlib.Path.cwd()) + "/Config/lock_cmd.json"), 'r+', encoding='utf-8') as json_file:
        data = json.load(json_file)
        data = dict(data)
        group_id = str(group_id)
        data[group_id] = value
        json_file.seek(0)
        json.dump(data, json_file, ensure_ascii=False, indent=2)
        json_file.truncate()
        json_file.close()
