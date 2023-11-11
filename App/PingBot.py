# -*- coding: utf-8 -*-
# @Time: 2023/11/11 18:53 
# @FileName: PingBot.py
# @Software: PyCharm
# @GitHub: KimmyXYC
from Utils.IP import *


async def handle_icp(bot, message):
    msg = await bot.reply_to(message, f"正在查询域名 {message.text.split()[1]} 备案信息...", disable_web_page_preview=True)
    status, data = await icp_record_check(message.text.split()[1])
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
    status, result = await whois_check(message.text.split()[1])
    if not status:
        await bot.edit_message_text(f"请求失败: `{result}`", message.chat.id, msg.message_id, parse_mode="MarkdownV2")
        return
    await bot.edit_message_text(f"`{result}`", message.chat.id, msg.message_id, parse_mode="MarkdownV2")


async def handle_dns(bot, message, record_type):
    msg = await bot.reply_to(message, f"DNS lookup {message.text.split()[1]} as {record_type} ...", disable_web_page_preview=True)
    status, result = await get_dns_info(message.text.split()[1], record_type)
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
            status, data = await ali_ipcity_ip(ip_addr, _config.appcode)
        else:
            status, data = await ali_ipcity_ip(ip_addr, _config.appcode, True)
        if not status:
            await bot.edit_message_text(f"请求失败: `{data}`", message.chat.id, msg.message_id, parse_mode="MarkdownV2")
            return
        if _is_url:
            ip_info = f"""查询目标： `{message.text.split()[1]}`\n解析地址： `{ip_addr}`\n"""
        else:
            ip_info = f"""查询目标： `{message.text.split()[1]}`\n"""
        if not data["country"]:
            status, data = await kimmy_ip(ip_addr)
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
                    ip_info += f"""地区： `{data["country"]}`\n"""
            ip_info += f"""经纬度： `{data["lng"]}, {data["lat"]}`\nISP： `{data["isp"]}`\n组织： `{data["owner"]}`\nAS号： `AS{data["asnumber"]}`"""
        await bot.edit_message_text(ip_info, message.chat.id, msg.message_id, parse_mode="MarkdownV2")
    else:
        await bot.edit_message_text("非法的 IP 地址或域名", message.chat.id, msg.message_id, parse_mode="MarkdownV2")


async def handle_ip(bot, message, _config):
    msg = await bot.reply_to(message, f"正在查询 {message.text.split()[1]} ...", disable_web_page_preview=True)
    url = message.text.split()[1]
    status, data = await ipapi_ip(url)
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
            status, data = await kimmy_ip(data["query"])
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
            status, data = await kimmy_ip(data["query"])
            if status:
                ip_info += f"""地区： `{data["country"]}`"""
                await bot.edit_message_text(ip_info, message.chat.id, msg.message_id, parse_mode="MarkdownV2")
            else:
                await bot.edit_message_text(f"请求失败: `{data['error']}`", message.chat.id, msg.message_id, parse_mode="MarkdownV2")
        else:
            await bot.edit_message_text(f"请求失败: `{data['message']}`", message.chat.id, msg.message_id, parse_mode="MarkdownV2")
