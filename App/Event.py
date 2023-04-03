from asyncio import sleep
from io import BytesIO
from PIL import Image
import requests
import telebot
import time


async def Del_Command(bot, message):
    await bot.delete_message(message.chat.id, message.message_id)


async def InLine_Message(bot, query):
    timestamp = int(time.time())//300
    photo_result1 = telebot.types.InlineQueryResultPhoto(
        id='1',
        photo_url=f'https://api.mahiron.moe/hangzhou.jpg?time={timestamp}',
        thumb_url=f'https://api.mahiron.moe/hangzhou.jpg?time={timestamp}',
        photo_width=1024,
        photo_height=900,
        caption='Location: 杭州电信'
    )
    photo_result2 = telebot.types.InlineQueryResultPhoto(
        id='2',
        photo_url=f'https://bili.elaina.pub/biliserver/guangzhou.jpg?time={timestamp}',
        thumb_url=f'https://bili.elaina.pub/biliserver/guangzhou.jpg?time={timestamp}',
        photo_width=1024,
        photo_height=900,
        caption='Location: 广州百度云'
    )
    await bot.answer_inline_query(query.id, [photo_result1, photo_result2])
