import telebot
import time
from loguru import logger
from Utils.Parameter import get_parameter, save_config


async def lock_command(bot, message, cmd):
    lock_cmd_list = get_parameter(message.chat.id)
    if cmd in lock_cmd_list:
        await bot.reply_to(message, "该命令已被锁定")
    else:
        lock_cmd_list.append(cmd)
        save_config(message.chat.id, lock_cmd_list)
        logger.info(f"Lock Command: {cmd} in {message.chat.id}")
        await bot.reply_to(message, f"已锁定命令`{cmd}`", parse_mode='Markdown')


async def unlock_command(bot, message, cmd):
    lock_cmd_list = get_parameter(message.chat.id)
    if cmd in lock_cmd_list:
        lock_cmd_list.remove(cmd)
        save_config(str(message.chat.id), lock_cmd_list)
        logger.info(f"Unlock Command: {cmd} in {message.chat.id}")
        await bot.reply_to(message, f"已解锁命令`{cmd}`", parse_mode='Markdown')
    else:
        await bot.reply_to(message, "该命令未被锁定")


async def handle_command(bot, message, cmd):
    lock_cmd_list = get_parameter(message.chat.id)
    if lock_cmd_list is None:
        lock_cmd_list = []
    if cmd in lock_cmd_list:
        await bot.delete_message(message.chat.id, message.message_id)


async def inline_message(bot, query):
    timestamp = int(time.time()) // 300
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
    await bot.answer_inline_query(query.id, [photo_result1, photo_result2])
