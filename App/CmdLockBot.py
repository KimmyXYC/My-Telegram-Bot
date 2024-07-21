# -*- coding: utf-8 -*-
# @Time: 2023/11/11 18:59 
# @FileName: CmdLockBot.py
# @Software: PyCharm
# @GitHub: KimmyXYC
from loguru import logger


async def lock_command(bot, message, cmd, db):
    lock_cmd_list = db.get(str(message.chat.id))
    if lock_cmd_list is None:
        lock_cmd_list = []
    if cmd in lock_cmd_list:
        await bot.reply_to(message, "该命令已被锁定")
    else:
        lock_cmd_list.append(cmd)
        db.set(str(message.chat.id), lock_cmd_list)
        logger.info(f"[CMD Lock][{message.chat.id}] Lock: {cmd}")
        await bot.reply_to(message, f"已锁定命令 `{cmd}` ", parse_mode='Markdown')


async def unlock_command(bot, message, cmd, db):
    lock_cmd_list = db.get(str(message.chat.id))
    if lock_cmd_list is None:
        lock_cmd_list = []
    if cmd in lock_cmd_list:
        lock_cmd_list.remove(cmd)
        db.set(str(message.chat.id), lock_cmd_list)
        logger.info(f"[CMD Lock][{message.chat.id}] Unlock: {cmd}")
        await bot.reply_to(message, f"已解锁命令 `{cmd}` ", parse_mode='Markdown')
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
