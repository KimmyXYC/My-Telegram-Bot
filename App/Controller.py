import asyncio
import telebot
import re
import time
from datetime import datetime, timedelta, timezone
from loguru import logger
from telebot import util, types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_filters import SimpleCustomFilter, AdvancedCustomFilter
from App import Event, PingBot, CmdLockBot, NewsBot


class BotRunner(object):
    def __init__(self, config, db):
        self.bot = config.bot
        self.proxy = config.proxy
        self.config = config
        self.db = db
        self.bot_id = int(self.bot.botToken.split(':')[0])

    def botcreate(self):
        bot = AsyncTeleBot(self.bot.botToken, state_storage=StateMemoryStorage())
        return bot, self.bot

    def run(self):
        logger.success("Bot Start")
        bot, _config = self.botcreate()
        if self.proxy.status:
            from telebot import asyncio_helper
            asyncio_helper.proxy = self.proxy.url
            logger.success("Proxy Set")

        @bot.message_handler(commands=['calldoctor', 'callmtf', 'callpolice'])
        async def call_anyone(message):
            await Event.call_anyone(bot, message)

        @bot.message_handler(commands=['t'], chat_types=['group', 'supergroup'])
        async def handle_appellation(message):
            await Event.appellation(bot, message, self.bot_id)

        @bot.message_handler(commands=['td'], chat_types=['group', 'supergroup'])
        async def handle_appellation(message):
            await Event.appellation_demote(bot, message, self.bot_id)

        @bot.message_handler(commands=["short"])
        async def handle_command(message):
            command_args = message.text.split()
            if len(command_args) == 1:
                await bot.reply_to(message, "格式错误, 格式应为 /short [URL] (short)")
            elif len(command_args) == 2:
                url = command_args[1]
                await Event.shorten_url(bot, message, self.config.shorturl, url)
            elif len(command_args) == 3:
                url = command_args[1]
                short = command_args[2]
                await Event.shorten_url(bot, message, self.config.shorturl, url, short)
            else:
                await bot.reply_to(message, "格式错误, 格式应为 /short [URL] (short)")

        @bot.message_handler(commands=['ip'])
        async def handle_ip(message):
            command_args = message.text.split()
            if len(command_args) == 1:
                await bot.reply_to(message, "格式错误, 格式应为 /ip [IP/Domain]")
            elif len(command_args) == 2:
                await PingBot.handle_ip(bot, message, self.config.ip)
            else:
                await bot.reply_to(message, "格式错误, 格式应为 /ip [IP/Domain]")

        @bot.message_handler(commands=['ip_ali'])
        async def handle_ali_ip(message):
            command_args = message.text.split()
            if len(command_args) == 1:
                await bot.reply_to(message, "格式错误, 格式应为 /ip_ali [IP/Domain]")
            elif len(command_args) == 2:
                await PingBot.handle_ip_ali(bot, message, self.config.ip)
            else:
                await bot.reply_to(message, "格式错误, 格式应为 /ip_ali [IP/Domain]")

        @bot.message_handler(commands=['icp'])
        async def handle_icp(message):
            command_args = message.text.split()
            if len(command_args) == 1:
                await bot.reply_to(message, "格式错误, 格式应为 /icp [Domain]")
            elif len(command_args) == 2:
                await PingBot.handle_icp(bot, message)
            else:
                await bot.reply_to(message, "格式错误, 格式应为 /icp [Domain]")

        @bot.message_handler(commands=['whois'])
        async def handle_whois(message):
            command_args = message.text.split()
            if len(command_args) == 1:
                await bot.reply_to(message, "格式错误, 格式应为 /whois [Domain]")
            elif len(command_args) == 2:
                await PingBot.handle_whois(bot, message)
            else:
                await bot.reply_to(message, "格式错误, 格式应为 /whois [Domain]")

        @bot.message_handler(commands=['dns'])
        async def handle_dns(message):
            command_args = message.text.split()
            if len(command_args) == 1:
                await bot.reply_to(message, "格式错误, 格式应为 /dns [Domain](Record_Type)")
            elif len(command_args) == 2:
                await PingBot.handle_dns(bot, message, "A")
            elif len(command_args) == 3:
                await PingBot.handle_dns(bot, message, command_args[2])
            else:
                await bot.reply_to(message, "格式错误, 格式应为 /dns [Domain](Record_Type)")

        @bot.message_handler(commands=['lock_cmd'])
        async def lock_command(message):
            if message.chat.type in ['group', 'supergroup']:
                bot_member = await bot.get_chat_member(message.chat.id, self.bot_id)
                if bot_member.status == 'administrator' and bot_member.can_delete_messages:
                    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
                    if (chat_member.status == 'administrator' and chat_member.can_delete_messages) \
                            or chat_member.status == 'creator':
                        command_args = message.text.split()
                        if len(command_args) == 1:
                            await bot.reply_to(message, "格式错误, 格式应为 /lock_cmd [CMD]")
                        elif len(command_args) == 2:
                            cmd = command_args[1]
                            await CmdLockBot.lock_command(bot, message, cmd, self.db)
                        else:
                            await bot.reply_to(message, "格式错误, 格式应为 /lock_cmd [CMD]")
                    else:
                        await bot.reply_to(message, "您无权使用此功能")
                else:
                    await bot.reply_to(message, "请先将机器人设置为管理员并赋予删除消息权限")
            else:
                await bot.reply_to(message, "请在群组中使用此功能")

        @bot.message_handler(commands=['unlock_cmd'])
        async def unlock_command(message):
            if message.chat.type in ['group', 'supergroup']:
                chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
                if (chat_member.status == 'administrator' and chat_member.can_delete_messages) \
                        or chat_member.status == 'creator':
                    command_args = message.text.split()
                    if len(command_args) == 1:
                        await bot.reply_to(message, "格式错误, 格式应为 /unlock_cmd [CMD]")
                    elif len(command_args) == 2:
                        cmd = command_args[1]
                        await CmdLockBot.unlock_command(bot, message, cmd, self.db)
                    else:
                        await bot.reply_to(message, "格式错误, 格式应为 /unlock_cmd [CMD]")
                else:
                    await bot.reply_to(message, "您无权使用此功能")
            else:
                await bot.reply_to(message, "请在群组中使用此功能")

        @bot.message_handler(commands=['list_locked_cmd'])
        async def list_locked_command(message):
            if message.chat.type in ['group', 'supergroup']:
                chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
                if (chat_member.status == 'administrator' and chat_member.can_delete_messages) \
                        or chat_member.status == 'creator':
                    await CmdLockBot.list_locked_command(bot, message, self.db)
                else:
                    await bot.reply_to(message, "您无权使用此功能")
            else:
                await bot.reply_to(message, "请在群组中使用此功能")

        @bot.message_handler(starts_with_alarm=True)
        async def handle_specific_start(message):
            type_dict = {"喜报": 0, "悲报": 1, "通报": 2, "警报": 3}
            await NewsBot.good_news(bot, message, type_dict[message.text[:2]])

        @bot.message_handler(command_in_group=True, content_types=['text'])
        async def handle_commands(message):
            if self.db.exists(str(message.chat.id)):
                command = re.split(r'[@\s]+', message.text.lower())[0]
                command = command[1:]
                lock_cmd_list = self.db.get(str(message.chat.id))
                if lock_cmd_list is None:
                    lock_cmd_list = []
                if command in lock_cmd_list:
                    await bot.delete_message(message.chat.id, message.message_id)

        @bot.message_handler(user_id=self.config.xiatou["id"], content_types=['text', 'photo', 'video', 'document'])
        async def handle_xiatou(message):
            count_db = self.db.get("inb")
            if count_db is None:
                count_db = [int(time.time()), 0]
            utc_plus_8 = timezone(timedelta(hours=8))
            db_time = datetime.fromtimestamp(count_db[0]).astimezone(utc_plus_8)
            now_time = datetime.now().astimezone(utc_plus_8)
            if db_time.day != now_time.day:
                count_db = [int(time.time()), 0]
            self.db.set("inb", count_db)
            if await Event.handle_xiatou(bot, message, count_db[1]):
                count_db[1] += 1
                self.db.set("inb", count_db)

        @bot.inline_handler(lambda query: True)
        async def send_photo(query):
            await Event.inline_message(bot, query)

        from telebot import asyncio_filters
        bot.add_custom_filter(asyncio_filters.IsAdminFilter(bot))
        bot.add_custom_filter(asyncio_filters.ChatFilter())
        bot.add_custom_filter(asyncio_filters.StateFilter(bot))
        bot.add_custom_filter(StartsWithFilter())
        bot.add_custom_filter(CommandInChatFilter())
        bot.add_custom_filter(UserFilter())

        async def main():
            await asyncio.gather(bot.polling(non_stop=True, allowed_updates=util.update_types))

        asyncio.run(main())


class StartsWithFilter(SimpleCustomFilter):
    key = 'starts_with_alarm'

    async def check(self, message):
        return message.text.startswith(('喜报', '悲报', '通报', '警报'))


class CommandInChatFilter(SimpleCustomFilter):
    key = 'command_in_group'

    async def check(self, message):
        return message.chat.type in ['group', 'supergroup'] and message.text.startswith('/')


class UserFilter(AdvancedCustomFilter):
    key = 'user_id'

    async def check(self, message, text):
        return message.from_user.id in text
