import asyncio
import telebot
from App import Event
from loguru import logger
from telebot import util
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage


class BotRunner(object):
    def __init__(self, config):
        self.bot = config.bot
        self.proxy = config.proxy

    def botcreate(self):
        bot = AsyncTeleBot(self.bot.botToken, state_storage=StateMemoryStorage())
        return bot, self.bot

    def run(self):
        # print(self.bot)
        logger.success("Bot Start")
        bot, _config = self.botcreate()
        if self.proxy.status:
            from telebot import asyncio_helper
            asyncio_helper.proxy = self.proxy.url
            logger.success("Proxy Set")

        @bot.message_handler(commands=["q", 'qs'])
        async def delete_command(message):
            await Event.Del_Command(bot, message)

        @bot.message_handler(content_types=['text'])
        async def delete_message(message):
            await Event.Del_Message(bot, message)

        @bot.message_handler(content_types=['document'])
        async def delete_file(message):
            await Event.Del_File(bot, message)

        from telebot import asyncio_filters
        bot.add_custom_filter(asyncio_filters.IsAdminFilter(bot))
        bot.add_custom_filter(asyncio_filters.ChatFilter())
        bot.add_custom_filter(asyncio_filters.StateFilter(bot))

        async def main():
            await asyncio.gather(bot.polling(non_stop=True, allowed_updates=util.update_types))

        asyncio.run(main())
