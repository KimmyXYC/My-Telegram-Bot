import telebot
import time
import random
import requests
from loguru import logger
from Utils.IP import *


async def call_anyone(bot, message):
    anyone_msg = ""
    if "/calldoctor" in message.text:
        anyone_list = ["👨‍⚕️", "👩‍⚕️", "🚑", "🏥", "💊"]
    elif "/callmtf" in message.text:
        anyone_list = ["🏳️‍⚧️", "🍥"]
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


async def handle_ip(bot, message, _config):
    ip_addr, ip_type = check_url(message.text.split()[1])
    _is_url = False
    if ip_type is None:
        ip_addr, ip_type = check_url(ip_addr)
        _is_url = True
    if ip_addr is None:
        await bot.reply_to(message, "格式错误, 格式应为 /ip [ip]")
        return
    elif ip_type == "v4":
        status, data = ali_ipcity_ip(ip_addr, _config.appcode)
        if not status:
            await bot.reply_to(message, f"请求失败: {data}")
            return
        if _is_url:
            ip_info = f"""查询目标： `{message.text.split()[1]}`\n解析地址： `{ip_addr}`\n"""
        else:
            ip_info = f"""查询目标： `{message.text.split()[1]}`\n"""
        if not data["country"]:
            status, data = kimmy_ip(ip_addr)
            if status:
                ip_info += f"""地区： `{data["country"]}`"""
        else:
            if data["prov"]:
                ip_info += f"""地区： `{data["country"]} - {data["prov"]} - {data["city"]}`\n"""
            else:
                ip_info += f"""地区： `{data["country"]}`\n """
            ip_info += f"""经纬度： `{data["lng"]}, {data["lat"]}`\nISP： `{data["isp"]}`\n组织： `{data["owner"]}`\n"""
            status, data = ipapi_ip(ip_addr)
            if status:
                ip_info += f"""`{data["as"]}`"""
        await bot.reply_to(message, f"{ip_info}", parse_mode="Markdown")
    elif ip_type == "v6":
        status, data = ipapi_ip(ip_addr)
        if status:
            if _is_url:
                ip_info = f"""查询目标： `{message.text.split()[1]}`\n解析地址： `{ip_addr}`\n"""
            else:
                ip_info = f"""查询目标： {message.text.split()[1]}\n"""
            if data["regionName"]:
                ip_info += f"""地区： `{data["country"]}` - `{data["regionName"]}` - `{data["city"]}`\n"""
            else:
                ip_info += f"""地区： `{data["country"]}`\n"""
            ip_info += f"""经纬度： `{data["lon"]}, {data["lat"]}`\nISP： `{data["isp"]}`\n组织： `{data["org"]}`\n`{data["as"]}`"""
            await bot.reply_to(message, f"{ip_info}", parse_mode="Markdown")
        else:
            await bot.reply_to(message, f"请求失败: {data}")


async def lock_command(bot, message, cmd, db):
    lock_cmd_list = db.get(str(message.chat.id))
    if lock_cmd_list is None:
        lock_cmd_list = []
    if cmd in lock_cmd_list:
        await bot.reply_to(message, "该命令已被锁定")
    else:
        lock_cmd_list.append(cmd)
        db.set(str(message.chat.id), lock_cmd_list)
        logger.info(f"Lock Command: {cmd} in {message.chat.id}")
        await bot.reply_to(message, f"已锁定命令`{cmd}`", parse_mode='Markdown')


async def unlock_command(bot, message, cmd, db):
    lock_cmd_list = db.get(str(message.chat.id))
    if lock_cmd_list is None:
        lock_cmd_list = []
    if cmd in lock_cmd_list:
        lock_cmd_list.remove(cmd)
        db.set(str(message.chat.id), lock_cmd_list)
        logger.info(f"Unlock Command: {cmd} in {message.chat.id}")
        await bot.reply_to(message, f"已解锁命令`{cmd}`", parse_mode='Markdown')
    else:
        await bot.reply_to(message, "该命令未被锁定")


async def list_locked_command(bot, message, db):
    lock_cmd_list = db.get(str(message.chat.id))
    if lock_cmd_list is None:
        msg = "本群未锁定任何命令"
    else:
        msg = "以下命令在本群中被锁定:\n"
        msg += "\n".join(f"- `{item}`" for item in lock_cmd_list)
    await bot.reply_to(message, msg, parse_mode='Markdown')


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
