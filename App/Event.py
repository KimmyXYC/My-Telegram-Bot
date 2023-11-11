import telebot
import time
import random
from loguru import logger


async def call_anyone(bot, message):
    anyone_msg = ""
    if "/calldoctor" in message.text:
        anyone_list = ["👨‍⚕️", "👩‍⚕️", "🚑", "🏥", "💊"]
    elif "/callmtf" in message.text:
        anyone_list = ["🏳️‍⚧️", "🍥"]
    elif "/callpolice" in message.text:
        anyone_list = ["🚨", "👮", "🚔", "🚓"]
    max_repeats = 3
    consecutive_count = 0
    for i in range(random.randint(20, 80)):
        emoji = random.choice(anyone_list)
        if emoji == anyone_msg[-1:]:
            consecutive_count += 1
        else:
            consecutive_count = 1
        if consecutive_count > max_repeats:
            emoji = random.choice([e for e in anyone_list if e != emoji])
            consecutive_count = 1
        anyone_msg += emoji
    await bot.reply_to(message, anyone_msg)


async def inline_message(bot, query):
    timestamp = int(time.time())
    photo_result1 = telebot.types.InlineQueryResultPhoto(
        id='1',
        photo_url=f'https://api.mahiron.moe/hangzhou.jpg?time={timestamp}',
        thumbnail_url=f'https://api.mahiron.moe/hangzhou.jpg?time={timestamp}',
        caption='测速地点: 杭州电信'
    )
    photo_result2 = telebot.types.InlineQueryResultPhoto(
        id='2',
        photo_url=f'https://bili.elaina.pub/biliserver/guangzhou.jpg?time={timestamp}',
        thumbnail_url=f'https://bili.elaina.pub/biliserver/guangzhou.jpg?time={timestamp}',
        caption='测速地点: 广州百度云'
    )
    await bot.answer_inline_query(query.id, [photo_result1], cache_time=60)
