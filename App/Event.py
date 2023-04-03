from asyncio import sleep
from io import BytesIO
from PIL import Image
import requests
import telebot


async def Del_Command(bot, message):
    await bot.delete_message(message.chat.id, message.message_id)


async def InLine_Message(bot, query):
    url = "https://api.mahiron.moe/hangzhou.jpg"
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    width, height = img.size
    photo_result = telebot.types.InlineQueryResultPhoto(
        id='1',
        photo_url='https://api.mahiron.moe/hangzhou.jpg',
        thumb_url='https://api.mahiron.moe/hangzhou.jpg',
        photo_width=width,
        photo_height=height
    )
    await bot.answer_inline_query(query.id, [photo_result])
