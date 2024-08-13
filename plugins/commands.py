from utils import temp_utils
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from script import scripts
from vars import ADMINS
from database.data_base import db
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@Client.on_message(filters.command("start"))
async def start_message(bot, message):
    user = await db.is_user_exist(message.from_user.id)
    if not user:
        await db.new_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    else:
        pass
    btn = [[
            InlineKeyboardButton("About", callback_data="about"),
            InlineKeyboardButton("Souce Code", callback_data="source")
        ],[
            InlineKeyboardButton("Close", callback_data="close"),
            InlineKeyboardButton("Help", callback_data="help")
        ]]
    await message.reply_text(
        text=scripts.START_TXT.format(message.from_user.mention, temp_utils.USER_NAME, temp_utils.BOT_NAME),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(btn)
    )

@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('Logs.txt')
    except Exception as e:
        await message.reply(str(e))

@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def skip_msgs(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ")
        try:
            skip = int(skip)
        except:
            return await message.reply("Skip number should be an integer.")
        await db.update_any(message.from_user.id, 'skip', int(skip))
        await message.reply(f"Successfully set SKIP number as {skip}")
        temp_utils.CURRENT = int(skip)
    else:
        await message.reply("Give me a skip number")

@Client.on_message(filters.command('set_target'))
async def set_target(bot, message):
    content = message.text
    try:
        target_id = content.split(" ", 1)[1]
    except:
        return await message.reply_text(
            text="<b>Hey give a channel ID where I'm admin along with the command !</b>"
        )
    try:
        target_id = int(target_id)
    except:
        return await message.reply_text(
            text="Give me a valid chat ID"
        )
    if target_id and target_id is not None:
        await db.update_any(message.from_user.id, 'target_chat', int(target_id))
        return await message.reply_text(
            text=f"Successfully set target chat ID to {target_id}"
        )
    else:
        return await message.reply_text(
            text="Give me a valid chat ID"
        )


@Client.on_message(filters.text & filters.private)
async def handle_user_input(bot: Client, message):
    user_id = message.from_user.id
    if user_id in temp_utils.UTILS and 'waiting_for' in temp_utils.UTILS[user_id]:
        if temp_utils.UTILS[user_id]['waiting_for'] == 'batch_size':
            try:
                batch_size = int(message.text)
                temp_utils.UTILS[user_id]['batch_size'] = batch_size
                await message.reply_text(f"Batch size set to {batch_size}.")
                if 'previous_message_id' in temp_utils.UTILS[user_id]:
                    await bot.delete_messages(chat_id=user_id, message_ids=temp_utils.UTILS[user_id]['previous_message_id'])
                await send_updated_message(bot, user_id)
            except ValueError:
                await message.reply_text("Invalid input. Please enter a number.")
            finally:
                del temp_utils.UTILS[user_id]['waiting_for']
        elif temp_utils.UTILS[user_id]['waiting_for'] == 'delay':
            try:
                delay = int(message.text)
                temp_utils.UTILS[user_id]['delay'] = delay
                await message.reply_text(f"Delay set to {delay} seconds.")
                if 'previous_message_id' in temp_utils.UTILS[user_id]:
                    await bot.delete_messages(chat_id=user_id, message_ids=temp_utils.UTILS[user_id]['previous_message_id'])
                await send_updated_message(bot, user_id)
            except ValueError:
                await message.reply_text("Invalid input. Please enter a number.")
            finally:
                del temp_utils.UTILS[user_id]['waiting_for']


async def send_updated_message(bot: Client, user_id: int):
    batch_size = temp_utils.UTILS[user_id].get('batch_size', 20)
    delay = temp_utils.UTILS[user_id].get('delay', 30)
    selected_media = temp_utils.UTILS[user_id].get('selected_media', [])

    buttons = [
        [InlineKeyboardButton(f"Batch Size: {batch_size}", callback_data=f"set_batch_size#{user_id}")],
        [InlineKeyboardButton(f"Delay: {delay} seconds", callback_data=f"set_delay#{user_id}")],
        [InlineKeyboardButton("Start Forwarding", callback_data=f"forward#{user_id}")],
        [InlineKeyboardButton("Cancel", callback_data="close")]
    ]

    source_chat = await bot.get_chat(chat_id=temp_utils.UTILS[user_id]['source_chat_id'])
    target_chat = await bot.get_chat(chat_id=temp_utils.UTILS[user_id]['target_chat_id'])
    
    new_message = await bot.send_message(
        chat_id=user_id,
        text=f"Selected media types: {', '.join(selected_media)}\n\n"
             f"Do you want to start forwarding from {source_chat.title} to {target_chat.title}?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    temp_utils.UTILS[user_id]['previous_message_id'] = new_message.message_id
