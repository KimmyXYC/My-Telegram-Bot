# -*- coding: utf-8 -*-
# @Time: 2024/7/28 19:55
# @FileName: KeyboxBot.py
# @Software: PyCharm
# @GitHub: KimmyXYC
import aiohttp
import json
import tempfile
import xml.etree.ElementTree as ET
from loguru import logger
from cryptography import x509
from cryptography.hazmat.backends import default_backend


async def load_from_url():
    url = "https://android.googleapis.com/attestation/status"

    headers = {
        "Cache-Control": "max-age=0, no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Error fetching data: {response.status}")
            return await response.json()


def parse_certificate(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    pem_certificate = root.find('.//Certificate[@format="pem"]')

    if pem_certificate is not None:
        pem_content = pem_certificate.text.strip()
        return pem_content
    else:
        return None


async def keybox_check(bot, message, document):
    file_info = await bot.get_file(document.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    with tempfile.NamedTemporaryFile(dir="downloads", delete=True) as temp_file:
        temp_file.write(downloaded_file)
        temp_file.flush()
        try:
            pem_certificate = parse_certificate(temp_file.name)
        except Exception as e:
            logger.error(f"[Keybox Check][message.chat.id]: {e}")
            await bot.reply_to(message, e)
            return
    try:
        certificate = x509.load_pem_x509_certificate(
            pem_certificate.encode(),
            default_backend()
        )
    except Exception as e:
        logger.error(f"[Keybox Check][message.chat.id]: {e}")
        await bot.reply_to(message, e)
        return
    serial_number = certificate.serial_number
    serial_number_string = hex(serial_number)[2:].lower()
    reply = f"*Serial number:* `{serial_number_string}`"
    try:
        status_json = await load_from_url()
    except Exception:
        with open("res/json/status.json", 'r', encoding='utf-8') as file:
            status_json = json.load(file)
    status = status_json['entries'].get(serial_number_string, None)
    if status is None:
        reply += "\n✅ Serial number not found in Google's revoked keybox list"
    else:
        reply += f"\n❌ Serial number found in Google's revoked keybox list\n*Reason:* `{status['reason']}`"
    await bot.reply_to(message, reply, parse_mode='Markdown')
