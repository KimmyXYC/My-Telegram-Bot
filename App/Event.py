import telebot
import time
import random
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


async def handle_icp(bot, message):
    msg = await bot.reply_to(message, f"正在查询域名 {message.text.split()[1]} 备案信息...", disable_web_page_preview=True)
    status, data = icp_record_check(message.text.split()[1])
    if not status:
        await bot.reply_to(message, f"请求失败: `{data}`")
        return
    if data["icp"] == "未备案":
        icp_info = f"""查询目标： `{message.text.split()[1]}`\n备案状态： `{data["icp"]}`\n"""
    else:
        icp_info = f"""查询目标： `{message.text.split()[1]}`\n备案号： `{data["icp"]}`\n备案主体： `{data["unitName"]}`\n备案性质： `{data["natureName"]}`\n备案时间： `{data["auditTime"]}`"""
    await bot.edit_message_text(icp_info, message.chat.id, msg.message_id, parse_mode="MarkdownV2")


async def handle_whois(bot, message):
    msg = await bot.reply_to(message, f"正在查询域名 {message.text.split()[1]} Whois 信息...", disable_web_page_preview=True)
    status, result = whois_check(message.text.split()[1])
    if not status:
        await bot.edit_message_text(f"请求失败: `{result}`", message.chat.id, msg.message_id, parse_mode="MarkdownV2")
        return
    await bot.edit_message_text(f"`{result}`", message.chat.id, msg.message_id, parse_mode="MarkdownV2")


async def handle_dns(bot, message, record_type):
    msg = await bot.reply_to(message, f"DNS lookup {message.text.split()[1]} as {record_type} ...", disable_web_page_preview=True)
    status, result = get_dns_info(message.text.split()[1], record_type)
    if not status:
        await bot.edit_message_text(f"请求失败: `{result}`", message.chat.id, msg.message_id, parse_mode="MarkdownV2")
        return
    dns_info = f"CN:\nTime Consume: {result['86'][0]['answer']['time_consume']}\n"
    dns_info += f"Records: {result['86'][0]['answer']['records']}\n\n"
    dns_info += f"US:\nTime Consume: {result['01'][0]['answer']['time_consume']}\n"
    dns_info += f"Records: {result['01'][0]['answer']['records']}\n\n"
    dns_info += f"HK:\nTime Consume: {result['852'][0]['answer']['time_consume']}\n"
    dns_info += f"Records: {result['852'][0]['answer']['records']}"
    dns_info = f"`{dns_info}`"
    await bot.edit_message_text(dns_info, message.chat.id, msg.message_id, parse_mode="MarkdownV2")


async def handle_ip_ali(bot, message, _config):
    msg = await bot.reply_to(message, f"正在查询 {message.text.split()[1]} ...", disable_web_page_preview=True)
    if not _config.appcode:
        await bot.edit_message_text("未配置阿里云 AppCode", message.chat.id, msg.message_id, parse_mode="MarkdownV2")
        return
    ip_addr, ip_type = check_url(message.text.split()[1])
    _is_url = False
    if ip_type is None:
        ip_addr, ip_type = check_url(ip_addr)
        _is_url = True
    if ip_addr is None:
        await bot.edit_message_text("非法的 IP 地址或域名", message.chat.id, msg.message_id, parse_mode="MarkdownV2")
        return
    elif ip_type == "v4" or ip_type == "v6":
        if ip_type == "v4":
            status, data = ali_ipcity_ip(ip_addr, _config.appcode)
        else:
            status, data = ali_ipcity_ip(ip_addr, _config.appcode, True)
        if not status:
            await bot.edit_message_text(f"请求失败: `{data}`", message.chat.id, msg.message_id, parse_mode="MarkdownV2")
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
            if ip_type == "v4":
                if data["prov"]:
                    ip_info += f"""地区： `{data["country"]} - {data["prov"]} - {data["city"]}`\n"""
                else:
                    ip_info += f"""地区： `{data["country"]}`\n"""
            else:
                if data["province"]:
                    ip_info += f"""地区： `{data["country"]} - {data["province"]} - {data["city"]}`\n"""
                else:
                    ip_info += f"""地区： `{data["country"]}`\n """
            ip_info += f"""经纬度： `{data["lng"]}, {data["lat"]}`\nISP： `{data["isp"]}`\n组织： `{data["owner"]}`\nAS号： `AS{data["asnumber"]}`"""
        await bot.edit_message_text(ip_info, message.chat.id, msg.message_id, parse_mode="MarkdownV2")
    else:
        await bot.edit_message_text("非法的 IP 地址或域名", message.chat.id, msg.message_id, parse_mode="MarkdownV2")


async def handle_ip(bot, message, _config):
    msg = await bot.reply_to(message, f"正在查询 {message.text.split()[1]} ...", disable_web_page_preview=True)
    url = message.text.split()[1]
    status, data = ipapi_ip(url)
    if status:
        if url == data["query"]:
            _is_url = False
        else:
            _is_url = True
        if not data["country"]:
            if _is_url:
                ip_info = f"""查询目标： `{url}`\n解析地址： `{data["query"]}`\n"""
            else:
                ip_info = f"""查询目标： `{url}`\n"""
            status, data = kimmy_ip(data["query"])
            if status:
                ip_info += f"""地区： `{data["country"]}`"""
        else:
            if _is_url:
                ip_info = f"""查询目标： `{url}`\n解析地址： `{data["query"]}`\n"""
            else:
                ip_info = f"""查询目标： `{url}`\n"""
            if data["regionName"]:
                ip_info += f"""地区： `{data["country"]} - {data["regionName"]} - {data["city"]}`\n"""
            else:
                ip_info += f"""地区： `{data["country"]}`\n"""
            ip_info += f"""经纬度： `{data["lon"]}, {data["lat"]}`\nISP： `{data["isp"]}`\n组织： `{data["org"]}`\n`{data["as"]}`"""
        if data["mobile"]:
            ip_info += f"""\n此 IP 可能为**蜂窝移动数据 IP**"""
        if data["proxy"]:
            ip_info += f"""\n此 IP 可能为**代理 IP**"""
        if data["hosting"]:
            ip_info += f"""\n此 IP 可能为**数据中心 IP**"""
        await bot.edit_message_text(ip_info, message.chat.id, msg.message_id, parse_mode="MarkdownV2")
    else:
        if data["message"] == "reserved range":
            if url == data["query"]:
                _is_url = False
            else:
                _is_url = True
            if _is_url:
                ip_info = f"""查询目标： `{message.text.split()[1]}`\n解析地址： `{data["query"]}`\n"""
            else:
                ip_info = f"""查询目标： `{message.text.split()[1]}`\n"""
            status, data = kimmy_ip(data["query"])
            if status:
                ip_info += f"""地区： `{data["country"]}`"""
                await bot.edit_message_text(ip_info, message.chat.id, msg.message_id, parse_mode="MarkdownV2")
            else:
                await bot.edit_message_text(f"请求失败: `{data['error']}`", message.chat.id, msg.message_id, parse_mode="MarkdownV2")
        else:
            await bot.edit_message_text(f"请求失败: `{data['message']}`", message.chat.id, msg.message_id, parse_mode="MarkdownV2")


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
