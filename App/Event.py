from asyncio import sleep
from io import BytesIO
from PIL import Image
import requests
import telebot
import time


async def Del_Command(bot, message):
    await bot.delete_message(message.chat.id, message.message_id)


async def InLine_Message(bot, query):
    url = "https://api.mahiron.moe/hangzhou.jpg"
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    width, height = img.size
    timestamp = int(time.time())//300
    photo_result = telebot.types.InlineQueryResultPhoto(
        id='1',
        photo_url=f'https://api.mahiron.moe/hangzhou.jpg?time={timestamp}',
        thumb_url=f'https://api.mahiron.moe/hangzhou.jpg?time={timestamp}',
        photo_width=width,
        photo_height=height
    )
    await bot.answer_inline_query(query.id, [photo_result])
