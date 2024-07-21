import telebot
import time
import json
import random
import aiohttp
from loguru import logger
from Utils.Tool import remove_emoji


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


async def shorten_url(bot, message, config, url, short=""):
    server = config["server"]
    if server == "":
        logger.error(f"User ID: {message.chat.id}  Backend Address Not Set")
        await bot.reply_to(
            message,
            f"生成失败, 后端地址未设置",
            disable_web_page_preview=True,
        )
    else:
        if url.startswith("https://") or url.startswith("http://"):
            if short:
                params = {'url': url, 'short': short, 'encode': 'json'}
            else:
                params = {'url': url, 'encode': 'json'}
            try:
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(server, params=params) as response:
                        if 'application/json' in response.headers['content-type']:
                            json_data = await response.json()
                        else:
                            text_data = await response.text()
                            json_data = json.loads(text_data)
                _info = "短链接: "
                if json_data["code"] == 0:
                    _url = json_data['url']
                    _status = True
                else:
                    _url = json_data['msg']
                    _status = False
                if _status:
                    logger.success(f"User ID: {message.chat.id}  Get Short URL: {_url}")
                    await bot.reply_to(
                        message,
                        f"{_info}`{_url}`",
                        disable_web_page_preview=True,
                        parse_mode="Markdown",
                    )
                else:
                    logger.error(f"User ID: {message.chat.id}  Can't Get Short URL: {_url}")
                    await bot.reply_to(
                        message,
                        f"生成失败: {_url}",
                        disable_web_page_preview=True,
                    )
            except Exception as e:
                logger.error(f"User ID: {message.chat.id}  Can't Get Short URL: {e}")
                await bot.reply_to(
                    message,
                    f"生成失败, 请检查后端地址是否有效: {e}",
                    disable_web_page_preview=True,
                )
        else:
            logger.error(f"User ID: {message.chat.id}  Not Effective URL")
            await bot.reply_to(
                message,
                f"非法的网址",
                disable_web_page_preview=True,
            )


async def appellation(bot, message, bot_id):
    bot_member = await bot.get_chat_member(message.chat.id, bot_id)
    if bot_member.status != "administrator" or not bot_member.can_promote_members:
        return
    if message.reply_to_message is None:
        if message.from_user.username == "GroupAnonymousBot":
            await bot.reply_to(message, "咱不能更改匿名管理员的头衔喵")
            return
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
    if user_member.status == "creator":
        await bot.reply_to(message, "咱不能对群主使用喵")
        return
    if user_member.status == "member":
        try:
            await bot.promote_chat_member(message.chat.id, user_id, can_manage_chat=True)
        except Exception as e:
            logger.error(e)
            error_message = str(e)
            start_index = error_message.find("Bad Request: ")
            if start_index != -1:
                error_message = error_message[start_index + len("Bad Request: "):]
                await bot.reply_to(message, f"失败了喵: {error_message}")
            return
    user_rank = remove_emoji(user_rank)
    try:
        await bot.set_chat_administrator_custom_title(message.chat.id, user_id, user_rank)
    except Exception as e:
        logger.error(e)
        error_message = str(e)
        if ("not enough rights to change custom title of the user" in error_message
                or " only creator can edit their custom title" in error_message):
            await bot.reply_to(message, f"咱只能更改由咱自己设置的管理员的头衔")
        else:
            start_index = error_message.find("Bad Request: ")
            if start_index != -1:
                error_message = error_message[start_index + len("Bad Request: "):]
                await bot.reply_to(message, f"失败了喵: {error_message}")
        return

    if message.reply_to_message is None:
        await bot.reply_to(message, f"好, 你现在是 {user_rank} 啦")
    else:
        init_user_mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
        target_user_mention = f"<a href='tg://user?id={user_id}'>{message.reply_to_message.from_user.first_name}</a>"
        await bot.reply_to(message, f"{init_user_mention} 把 {target_user_mention} 变成 {user_rank} !", parse_mode="HTML")


async def appellation_demote(bot, message, bot_id):
    bot_member = await bot.get_chat_member(message.chat.id, bot_id)
    if bot_member.status != "administrator" or not bot_member.can_promote_members:
        return
    if message.reply_to_message is None:
        user_id = message.from_user.id
        user_member = await bot.get_chat_member(message.chat.id, user_id)
        if user_member.status == "creator":
            await bot.reply_to(message, "咱不能对群主使用喵")
            return
        if message.from_user.username == "GroupAnonymousBot":
            await bot.reply_to(message, "咱不能更改匿名管理员的头衔喵")
            return
        try:
            await bot.promote_chat_member(message.chat.id, user_id, can_manage_chat=False)
            await bot.reply_to(message, "好, 你现在没有头衔啦")
        except Exception as e:
            logger.error(e)
            error_message = str(e)
            if "CHAT_ADMIN_REQUIRED" in error_message:
                await bot.reply_to(message, "咱只能更改由咱自己设置的管理员的头衔喵")
            else:
                start_index = error_message.find("Bad Request: ")
                if start_index != -1:
                    error_message = error_message[start_index + len("Bad Request: "):]
                    await bot.reply_to(message, f"失败了喵: {error_message}")
            return
    else:
        user_id = message.reply_to_message.from_user.id
        if user_id == bot_id:
            await bot.reply_to(message, "咱不能更改自己的头衔喵")
            return
        from_user_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if ((from_user_member.status != "administrator" or not from_user_member.can_promote_members)
                and from_user_member.status != "creator"):
            await bot.reply_to(message, "你没有增加管理员的权限喵")
            return
        user_member = await bot.get_chat_member(message.chat.id, user_id)
        if user_member.status == "creator":
            await bot.reply_to(message, "咱不能对群主使用喵")
            return
        try:
            await bot.promote_chat_member(message.chat.id, user_id, can_manage_chat=False)
            init_user_mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
            target_user_mention = f"<a href='tg://user?id={user_id}'>{message.reply_to_message.from_user.first_name}</a>"
            await bot.reply_to(message, f"{init_user_mention} 把 {target_user_mention} 变成 RBQ!", parse_mode="HTML")
        except Exception as e:
            logger.error(e)
            error_message = str(e)
            if "CHAT_ADMIN_REQUIRED" in error_message:
                await bot.reply_to(message, "咱只能更改由咱自己设置的管理员的头衔喵")
            else:
                start_index = error_message.find("Bad Request: ")
                if start_index != -1:
                    error_message = error_message[start_index + len("Bad Request: "):]
                    await bot.reply_to(message, f"失败了喵: {error_message}")


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
