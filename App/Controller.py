import asyncio
import telebot
from App import Event
from loguru import logger
from telebot import util
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage


class BotRunner(object):
    def __init__(self, config, db):
        self.bot = config.bot
        self.proxy = config.proxy
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

        @bot.message_handler(commands=['calldoctor', 'callmtf'])
        async def call_anyone(message):
            await Event.call_anyone(bot, message)

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
                            await Event.lock_command(bot, message, cmd, self.db)
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
                        await Event.unlock_command(bot, message, cmd, self.db)
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
                    await Event.list_locked_command(bot, message, self.db)
                else:
                    await bot.reply_to(message, "您无权使用此功能")
            else:
                await bot.reply_to(message, "请在群组中使用此功能")

        @bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'], content_types=['text'])
        async def handle_commands(message):
            if message.text.startswith('/'):
                if self.db.exists(str(message.chat.id)):
                    command = message.text.split()[0].lower()
                    command = command[1:]
                    lock_cmd_list = self.db.get(str(message.chat.id))
                    if lock_cmd_list is None:
                        lock_cmd_list = []
                    if command in lock_cmd_list:
                        await bot.delete_message(message.chat.id, message.message_id)

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
