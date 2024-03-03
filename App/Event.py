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


async def appellation(bot, message, bot_id):
    bot_member = await bot.get_chat_member(message.chat.id, bot_id)
    if bot_member.status != "administrator" or not bot_member.can_promote_members:
        return
    if message.reply_to_message is None:
        user_id = message.from_user.id
        user_rank = message.from_user.first_name
        if message.from_user.last_name:
            user_rank += f" {message.from_user.last_name}"
    else:
        user_id = message.reply_to_message.from_user.id
        if user_id == bot_id:
            await bot.reply_to(message, "咱不能更改自己的头衔喵")
            return
        user_rank = message.reply_to_message.from_user.first_name
        if message.reply_to_message.from_user.last_name:
            user_rank += f" {message.reply_to_message.from_user.last_name}"
    if len(message.text.split()) != 1:
        user_rank = message.text.split(maxsplit=1)[1]
    user_member = await bot.get_chat_member(message.chat.id, user_id)
    successful_change = True
    if user_member.status == "member":
        await bot.promote_chat_member(message.chat.id, user_id, can_manage_chat=True)
    try:
        await bot.set_chat_administrator_custom_title(message.chat.id, user_id, user_rank)
    except Exception as e:
        logger.error(e)
        successful_change = False
    if message.reply_to_message is None:
        if successful_change:
            await bot.reply_to(message, f"好, 你现在是 {user_rank} 啦")
        else:
            await bot.reply_to(message, f"咱只能更改由咱自己设置的管理员的头衔")
    else:
        if successful_change:
            init_user_mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
            target_user_mention = f"<a href='tg://user?id={user_id}'>{message.reply_to_message.from_user.first_name}</a>"
            await bot.reply_to(message, f"{init_user_mention} 把 {target_user_mention} 变成 {user_rank} !", parse_mode="HTML")
        else:
            await bot.reply_to(message, f"咱只能更改由咱自己设置的管理员的头衔")


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
        photo_url=f'https://api.sayo.ink/biliroaming-speed?time={timestamp}',
        thumbnail_url=f'https://api.sayo.ink/biliroaming-speed?time={timestamp}',
        caption='测速地点: 杭州阿里云'
    )
    await bot.answer_inline_query(query.id, [photo_result1, photo_result2], cache_time=60)
