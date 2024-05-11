import asyncio
import telebot
import re
from loguru import logger
from telebot import util
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from App import Event, PingBot, CmdLockBot, GoodNewsBot, BaiduUwpBot


class BotRunner(object):
    def __init__(self, config, db):
        self.bot = config.bot
        self.proxy = config.proxy
        self.baiduuwp = config.baiduuwp
        self.config = config
        self.db = db
        self.bot_id = int(self.bot.botToken.split(':')[0])
        self.baidubot = BaiduUwpBot.BaiduUwp(config.baiduuwp)

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

        @bot.message_handler(commands=['bd'])
        async def baidu_jx(message):
            if message.chat.id not in self.baiduuwp.members:
                return
            await self.baidubot.start(bot, message)

        @bot.callback_query_handler(func=lambda call: call.data.startswith('bd_'))
        async def handle_baidu_list_callback_query(call):
            await self.baidubot.baidu_list(bot, call)

        @bot.callback_query_handler(func=lambda call: call.data.startswith('bdf_'))
        async def handle_baidu_file_callback_query(call):
            await self.baidubot.baidu_file(bot, call)

        @bot.callback_query_handler(func=lambda call: call.data.startswith('bdAll_dl'))
        async def handle_baidu_all_dl_callback_query(call):
            await self.baidubot.baidu_all_dl(bot, call)

        @bot.callback_query_handler(func=lambda call: call.data.startswith('bdexit'))
        async def handle_baidu_exit_callback_query(call):
            await self.baidubot.baidu_exit(bot, call)

        @bot.message_handler(commands=['t'],chat_types=['group', 'supergroup'])
        async def handle_appellation(message):
            await Event.appellation(bot, message, self.bot_id)

        @bot.message_handler(commands=['td'], chat_types=['group', 'supergroup'])
        async def handle_appellation(message):
            await Event.appellation_demote(bot, message, self.bot_id)

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

        @bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup', 'private'], content_types=['text'])
        async def handle_commands(message):
            if message.text.startswith('/'):
                if message.chat.type in ['group', 'supergroup']:
                    if self.db.exists(str(message.chat.id)):
                        command = re.split(r'[@\s]+', message.text.lower())[0]
                        command = command[1:]
                        lock_cmd_list = self.db.get(str(message.chat.id))
                        if lock_cmd_list is None:
                            lock_cmd_list = []
                        if command in lock_cmd_list:
                            await bot.delete_message(message.chat.id, message.message_id)
            elif message.text.startswith('喜报'):
                await GoodNewsBot.good_news(bot, message, 0)
            elif message.text.startswith('悲报'):
                await GoodNewsBot.good_news(bot, message, 1)
            elif message.text.startswith('通报'):
                await GoodNewsBot.good_news(bot, message, 2)
            elif message.text.startswith('警报'):
                await GoodNewsBot.good_news(bot, message, 3)

        @bot.inline_handler(lambda query: True)
        async def send_photo(query):
            await Event.inline_message(bot, query)

        from telebot import asyncio_filters
        bot.add_custom_filter(asyncio_filters.IsAdminFilter(bot))
        bot.add_custom_filter(asyncio_filters.ChatFilter())
        bot.add_custom_filter(asyncio_filters.StateFilter(bot))

        async def main():
            await asyncio.gather(bot.polling(non_stop=True, allowed_updates=util.update_types))

        asyncio.run(main())
