from asyncio import sleep


async def Del_Command(bot, message):
    await bot.delete_message(message.chat.id, message.message_id)
