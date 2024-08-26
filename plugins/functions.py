from utils import temp_utils
from database.data_base import db
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait
from pyrogram import enums
import logging
import asyncio
import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()

async def delete_message_later(bot, chat_id, message_id, delay_seconds):
    await asyncio.sleep(delay_seconds)
    try:
        await bot.delete_messages(chat_id, message_id)
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")

async def start_forward(bot, userid, skip):
    util = temp_utils.UTILS.get(int(userid))
    if util is not None:
        source_chat_id = util.get('source_chat_id')
        last_msg_id = util.get('last_msg_id')
        TARGET_DB = util.get('target_chat_id')
        batch_size = util.get('batch_size', 20)
        delay = util.get('delay', 30)
        selected_media = util.get('selected_media', [])
    else:
        user = await db.get_user(int(userid))
        if user and user['on_process'] and not user['is_complete']:
            source_chat_id = user['source_chat']
            last_msg_id = user['last_msg_id']
            TARGET_DB = user['target_chat']
            batch_size = 20
            delay = 30
            selected_media = []
        else:
            return

    btn = [[
        InlineKeyboardButton("CANCEL", callback_data="cancel_forward")
    ]]
    active_msg = await bot.send_message(
        chat_id=int(userid),
        text="<b>Starting Forward Process...</b>",
        reply_markup=InlineKeyboardMarkup(btn)
    )

    asyncio.create_task(delete_message_later(bot, int(userid), active_msg.id, 30 * 60))

    skipped = int(skip)
    total = 0
    forwarded = 0
    empty = 0
    notmedia = 0
    unsupported = 0
    left = 0
    status = 'Idle'

    async with lock:
        try:
            btn = [[
                InlineKeyboardButton("CANCEL", callback_data="cancel_forward")
            ]]
            status = 'Forwarding...'
            await active_msg.edit(
                text=f"<b>Forwarding on progress...\n\nTotal: {total}\nSkipped: {skipped}\nForwarded: {forwarded}\nEmpty Message: {empty}\nNot Media: {notmedia}\nUnsupported Media: {unsupported}\nMessages Left: {left}\n\nStatus: {status}</b>",
                reply_markup=InlineKeyboardMarkup(btn)
            )
            current = int(skip)
            temp_utils.CANCEL[int(userid)] = False
            await db.update_any(userid, 'on_process', True)
            await db.update_any(userid, 'is_complete', False)

            while True:
                batch_count = 0
                async for msg in bot.iter_messages(source_chat_id, int(last_msg_id), int(skip)):
                    if temp_utils.CANCEL.get(int(userid)):
                        status = 'Cancelled !'
                        await active_msg.edit(f"<b>Successfully Cancelled!\n\nTotal: {total}\nSkipped: {skipped}\nForwarded: {forwarded}\nEmpty Message: {empty}\nNot Media: {notmedia}\nUnsupported Media: {unsupported}\nMessages Left: {left}\n\nStatus: {status}</b>")
                        return

                    total = current
                    left = int(last_msg_id) - int(total)
                    current += 1
                    batch_count += 1

                    if msg.empty:
                        empty += 1
                        continue
                    elif not msg.media:
                        notmedia += 1
                        continue
                    elif msg.media not in [getattr(enums.MessageMediaType, media.upper()) for media in selected_media]:
                        unsupported += 1
                        continue

                    try:
                        await msg.copy(chat_id=int(TARGET_DB), caption="")
                        forwarded += 1
                        await asyncio.sleep(1)
                    except FloodWait as e:
                        btn = [[
                            InlineKeyboardButton("CANCEL", callback_data="cancel_forward")
                        ]]
                        await active_msg.edit(
                            text=f"<b>Got FloodWait.\n\nWaiting for {e.value} seconds.</b>",
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                        await asyncio.sleep(e.value)
                        await msg.copy(chat_id=int(TARGET_DB))
                        forwarded += 1
                        continue

                    if batch_count % batch_size == 0:
                        status = f'Processed {batch_size} messages, sleeping for {delay} seconds.'
                        await active_msg.edit(
                            text=f"<b>Forwarding on progress...\n\nTotal: {total}\nSkipped: {skipped}\nForwarded: {forwarded}\nEmpty Message: {empty}\nNot Media: {notmedia}\nUnsupported Media: {unsupported}\nMessages Left: {left}\n\nStatus: {status}</b>",
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                        asyncio.create_task(delete_message_later(bot, int(userid), new_msg.id, 30 * 60))
                        await asyncio.sleep(delay)
                        batch_count = 0

                if batch_count > 0:
                    status = f'Completed batch of {batch_count} messages.'
                    await active_msg.edit(
                        text=f"<b>Forwarding on progress...\n\nTotal: {total}\nSkipped: {skipped}\nForwarded: {forwarded}\nEmpty Message: {empty}\nNot Media: {notmedia}\nUnsupported Media: {unsupported}\nMessages Left: {left}\n\nStatus: {status}</b>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )

                break

            status = 'Completed !'
        except Exception as e:
            logger.exception(e)
            await active_msg.edit(f'<b>Error:</b> <code>{e}</code>')
            asyncio.create_task(delete_message_later(bot, int(userid), final_msg.id, 30 * 60))
        else:
            await db.update_any(userid, 'on_process', False)
            await db.update_any(userid, 'is_complete', True)
            await active_msg.edit(f"<b>Successfully Completed Forward Process !\n\nTotal: {total}\nSkipped: {skipped}\nForwarded: {forwarded}\nEmpty Message: {empty}\nNot Media: {notmedia}\nUnsupported Media: {unsupported}\nMessages Left: {left}\n\nStatus: {status}</b>")
            asyncio.create_task(delete_message_later(bot, int(userid), final_msg.id, 30 * 60))

async def gather_task(bot, users):
    tasks = []
    for user in users:
        task = asyncio.create_task(start_forward(bot, user['id'], user['fetched']))
        tasks.append(task)
    await asyncio.gather(*tasks)
