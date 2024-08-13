from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import Client, filters
from script import scripts
from utils import temp_utils
import logging
from database.data_base import db
from .functions import start_forward

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

@Client.on_callback_query()
async def query_handler(bot: Client, query: CallbackQuery):
    if query.data == "close":
        await query.message.delete()
    elif query.data == "about":
        btn = [[
            InlineKeyboardButton("Go Back", callback_data="home"),
            InlineKeyboardButton("Close", callback_data="close")
        ]]
        await query.message.edit_text(
            text=scripts.ABOUT_TXT.format(temp_utils.BOT_NAME),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(btn)
        )
    elif query.data == "home":
        btn = [[
            InlineKeyboardButton("About", callback_data="about"),
            InlineKeyboardButton("Source Code", callback_data="source")
        ],[
            InlineKeyboardButton("Close", callback_data="close"),
            InlineKeyboardButton("Help", callback_data="help")
        ]]
        await query.message.edit_text(
            text=scripts.START_TXT.format(query.from_user.mention, temp_utils.USER_NAME, temp_utils.BOT_NAME),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(btn)
        )
    elif query.data == "source":
        btn = [[
            InlineKeyboardButton("Go Back", callback_data="home"),
            InlineKeyboardButton("Close", callback_data="close")
        ]]
        await query.message.edit_text(
            text=scripts.SOURCE_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(btn)
        )
    elif query.data == "cancel_forward":
        temp_utils.CANCEL[int(query.from_user.id)] = True
        await query.answer("Cancelling Process !\n\nIf the bot is sleeping, it will cancel only after the sleeping is over !", show_alert=True)
    elif query.data == "help":
        btn = [[
            InlineKeyboardButton("Go Back", callback_data="home"),
            InlineKeyboardButton("Close", callback_data="close")
        ]]
        await query.message.edit_text(
            text=scripts.HELP_TXT.format(temp_utils.BOT_NAME),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(btn)
        )
    elif query.data.startswith("set_batch_size"):
        user_id = query.data.split("#")[1]
        await query.message.edit_text(
            "Please enter the batch size (number of messages to process at a time):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="close")]])
        )
        temp_utils.UTILS[int(user_id)]['waiting_for'] = 'batch_size'
    elif query.data.startswith("set_delay"):
        user_id = query.data.split("#")[1]
        await query.message.edit_text(
            "Please enter the delay in seconds (time to wait after each batch):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="close")]])
        )
        temp_utils.UTILS[int(user_id)]['waiting_for'] = 'delay'
    elif query.data.startswith("forward"):
        ident, user_id = query.data.split("#")
        if int(query.from_user.id) != int(user_id):
            return await query.answer("You can't touch this!")
        user = await db.get_user(int(user_id))
        await query.message.delete()
        await start_forward(bot, user_id, user['skip'])
    elif query.data.startswith("toggle_media"):
        await toggle_media_type(bot, query)
    elif query.data.startswith("confirm_media"):
        await confirm_media_selection(bot, query)


async def toggle_media_type(bot, callback_query):
    user_id, media_type = callback_query.data.split("#")[1:]
    user_id = int(user_id)
    
    if 'selected_media' not in temp_utils.UTILS[user_id]:
        temp_utils.UTILS[user_id]['selected_media'] = []
    
    if media_type in temp_utils.UTILS[user_id]['selected_media']:
        temp_utils.UTILS[user_id]['selected_media'].remove(media_type)
    else:
        temp_utils.UTILS[user_id]['selected_media'].append(media_type)
    
    media_types = [
        ("Video", "video"),
        ("Audio", "audio"),
        ("Document", "document"),
        ("Image", "photo")
    ]
    
    buttons = []
    for media_name, media_type in media_types:
        if media_type in temp_utils.UTILS[user_id]['selected_media']:
            media_name += " ✅"
        else:
            media_name += " ❌"
        
        buttons.append([InlineKeyboardButton(
            media_name,
            callback_data=f"toggle_media#{user_id}#{media_type}"
        )])
    
    buttons.append([InlineKeyboardButton("Confirm", callback_data=f"confirm_media#{user_id}")])
    
    await callback_query.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def confirm_media_selection(bot, callback_query):
    user_id = callback_query.data.split("#")[1]
    selected_media = temp_utils.UTILS[int(user_id)].get('selected_media', [])
    
    if not selected_media:
        await callback_query.answer("Please select at least one media type.", show_alert=True)
        return
    
    batch_size = temp_utils.UTILS[int(user_id)].get('batch_size', 20)
    delay = temp_utils.UTILS[int(user_id)].get('delay', 30)
    
    buttons = [
        [InlineKeyboardButton(f"Batch Size: {batch_size}", callback_data=f"set_batch_size#{user_id}")],
        [InlineKeyboardButton(f"Delay: {delay} seconds", callback_data=f"set_delay#{user_id}")],
        [InlineKeyboardButton("Start Forwarding", callback_data=f"forward#{user_id}")],
        [InlineKeyboardButton("Cancel", callback_data="close")]
    ]
    
    source_chat = await bot.get_chat(chat_id=temp_utils.UTILS[int(user_id)]['source_chat_id'])
    target_chat = await bot.get_chat(chat_id=temp_utils.UTILS[int(user_id)]['target_chat_id'])
    
    await callback_query.edit_message_text(
        f"Selected media types: {', '.join(selected_media)}\n\n"
        f"Do you want to start forwarding from {source_chat.title} to {target_chat.title}?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
