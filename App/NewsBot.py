# -*- coding: utf-8 -*-
# @Time: 2023/11/11 20:13 
# @FileName: NewsBot.py
# @Software: PyCharm
# @GitHub: KimmyXYC
import textwrap
from PIL import Image, ImageDraw, ImageFont
from loguru import logger


async def good_news(bot, message, news_type):
    if news_type == 0:
        pic_dir = "res/pic/xibao.png"
        fill = "red"
        shadow_color = (255, 251, 3)
        size = 65
        wrap_width = 15
    elif news_type == 1:
        pic_dir = "res/pic/beibao.png"
        fill = (50, 50, 50)
        shadow_color = "grey"
        size = 65
        wrap_width = 14
    elif news_type == 2:
        pic_dir = "res/pic/tongbao.png"
        fill = "white"
        shadow_color = None
        size = 100
        wrap_width = 10
    elif news_type == 3:
        pic_dir = "res/pic/jingbao.png"
        fill = "white"
        shadow_color = None
        size = 90
        wrap_width = 10
    else:
        await bot.reply_to(message, "发生未知错误")
        return
    img = Image.open(pic_dir)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('res/font/MiSans-Semibold.ttf', size)
    text = message.text[2:]
    if text.startswith(" "):
        text = text[1:]
    if text != "":
        wrapped_lines = textwrap.wrap(text, width=wrap_width)
        wrapped_text = '\n'.join(wrapped_lines)
        num_lines = len(wrapped_lines)
        text_width = draw.textlength(wrapped_lines[0], font)
        text_height = size * num_lines
    else:
        return
    position = ((img.width - text_width) / 2, (img.height - text_height) / 2)
    shadow_offset = (3, 3)
    if shadow_color is not None:
        draw.text((position[0] + shadow_offset[0], position[1] + shadow_offset[1]), wrapped_text, font=font,
                  fill=shadow_color, align="center")
    draw.text(position, wrapped_text, font=font, fill=fill, align="center")
    await bot.send_photo(message.chat.id, img)
