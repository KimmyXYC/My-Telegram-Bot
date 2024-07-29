import telebot
import time
import json
import random
import re
import aiohttp
import psutil
import platform
from loguru import logger


async def handle_info(bot, message):
    os_info = platform.platform()
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    swap_info = psutil.swap_memory()
    disk_info = psutil.disk_usage('/')
    net_io = psutil.net_io_counters()
    load_avg = psutil.getloadavg()

    info_message = (
        f"*Operating System:* `{os_info}`\n"
        f"*CPU Usage:* `{cpu_usage}%`\n"
        f"*Memory Usage:* `{memory_info.percent}% (Total: {memory_info.total / (1024 ** 3):.2f} GB, "
        f"Used: {memory_info.used / (1024 ** 3):.2f} GB)`\n"
        f"*Swap Usage:* `{swap_info.percent}% (Total: {swap_info.total / (1024 ** 3):.2f} GB, "
        f"Used: {swap_info.used / (1024 ** 3):.2f} GB)`\n"
        f"*Disk Usage:* `{disk_info.percent}% (Total: {disk_info.total / (1024 ** 3):.2f} GB, "
        f"Used: {disk_info.used / (1024 ** 3):.2f} GB)`\n"
        f"*Network I/O:* `Sent: {net_io.bytes_sent / (1024 ** 2):.2f} MB, "
        f"Received: {net_io.bytes_recv / (1024 ** 2):.2f} MB`\n"
        f"*Load Average:* `1 min: {load_avg[0]:.2f}, 5 min: {load_avg[1]:.2f}, 15 min: {load_avg[2]:.2f}`"
    )

    await bot.reply_to(message, info_message, parse_mode='Markdown')


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
        logger.error(f"[Short URL][{message.chat.id}]: Backend Address Not Set")
        await bot.reply_to(
            message,
            f"生成失败, 后端地址未设置",
            disable_web_page_preview=True,
        )
    else:
        if not (url.startswith("https://") or url.startswith("http://")):
            url = "http://" + url
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
                if json_data["code"] == 0:
                    _url = json_data['url']
                    _status = True
                else:
                    _url = json_data['msg']
                    _status = False
                if _status:
                    logger.success(f"[Short URL][{message.chat.id}]: Get Short URL: {_url}")
                    await bot.reply_to(
                        message,
                        f"短链接: `{_url}`",
                        disable_web_page_preview=True,
                        parse_mode="Markdown",
                    )
                else:
                    logger.error(f"[Short URL][{message.chat.id}]: Can't Get Short URL: {_url}")
                    await bot.reply_to(
                        message,
                        f"生成失败: `{_url}`",
                        disable_web_page_preview=True,
                        parse_mode="Markdown",
                    )
            except Exception as e:
                logger.error(f"[Short URL][{message.chat.id}]: Can't Get Short URL: {e}")
                await bot.reply_to(
                    message,
                    f"生成失败, 请检查后端地址是否有效: `{e}`",
                    disable_web_page_preview=True,
                    parse_mode="Markdown",
                )


async def handle_xiatou(bot, message, count, config):
    if message.content_type == 'text':
        text_content = message.text
    else:
        text_content = message.caption
        if text_content is None:
            return False
    pattern = r"(?:舔|嗦|啃|舔舐|舔舔|舔舐|吻|嘬)(?:(?:萝莉|幼女|云漓|克拉拉|小格雷修)(?:的)?(?:脚|jio|足|狱卒|嫩足|脚丫子|脚丫|脚趾头|玉足|裸足))|(?:萝莉|幼女|云漓|克拉拉|小格雷修)\s*(?:脚|jio|足|狱卒|嫩足|脚丫子|脚丫|脚趾头|玉足|裸足)\s*(?:给我|放进|想|感觉|看着)|.*(?:jio|狱卒|玉足|脚丫|脚丫子|脚趾|脚趾头|嫩足|裸足|小脚|小足|脚板|脚掌|脚背|足尖|脚丫丫).*|(?: .*放我嘴里.*)"
    if re.search(pattern, text_content, re.IGNORECASE):
        logger.info(f"[XiaTou][{message.chat.id}]: {text_content}")
        logger.success(f"[XiaTou][{message.chat.id}]: Regular Match Success")
        await bot.reply_to(message, f"#下头\ninb 老师，这是你今天第 {count+1} 次下头")
        return True
    else:
        pattern = r".*(?:脚|足|萝莉).*"
        if re.search(pattern, text_content, re.IGNORECASE):
            url = f"https://api.cloudflare.com/client/v4/accounts/{config['cloudflare_account_id']}/ai/run/@cf/qwen/qwen1.5-14b-chat-awq"
            headers = {
                "Authorization": f"Bearer {config['cloudflare_auth_token']}"
            }
            data = {
                "messages": [
                    {
                        "role": "system",
                        "content": "下面我将给你一些句子，你需要判断是否让人感到吃惊/恶心，如果感到，则回答true，否则回答false。例子：“现在 还有云漓的玉足可以舔”“算了 我还是去舔萝莉玉足吧”。你应该回答：true"
                    },
                    {
                        "role": "user",
                        "content": message.text
                    }
                ]
            }
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    response_json = await response.json()
            if response_json["result"]["response"] == "true":
                logger.info(f"[XiaTou][{message.chat.id}]: {text_content}")
                logger.success(f"[XiaTou][{message.chat.id}]: AI Match Success")
                await bot.reply_to(message, f"#下头\ninb 老师，这是你今天第 {count+1} 次下头")
                return True
    return False


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
