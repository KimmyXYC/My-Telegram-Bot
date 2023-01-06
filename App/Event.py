from asyncio import sleep


async def Del_Command(bot, message):
    await bot.delete_message(message.chat.id, message.message_id)


async def Del_Message(bot, message):
    if '-sh whois' in message.text or '，sh whois' in message.text or ',sh whois' in message.text:
        await sleep(5)
        await bot.delete_message(message.chat.id, message.message_id)


async def Del_File(bot, message):
    if message.document.file_name == 'output.log':
        await sleep(5)
        await bot.delete_message(message.chat.id, message.message_id)
