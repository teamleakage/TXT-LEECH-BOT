import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess
from pyromod import listen
from subprocess import getstatusoutput
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import m3u8
from Cryptodome.Cipher import AES
import base64
from vars import API_ID, API_HASH, BOT_TOKEN

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start"))
async def start_message(client, message):
    await message.reply_text(
        "Hello! I am a TXT Leech Bot.\n\n"
        "I can download videos from text files containing links.\n"
        "Send /help to know more about how to use me."
    )

@bot.on_message(filters.command("help"))
async def help_message(client, message):
    await message.reply_text(
        "How to use me:\n\n"
        "1. Send me a text file containing video links\n"
        "2. Use /upload command to start downloading\n"
        "3. Use /stop to cancel ongoing process\n\n"
        "For support, contact @JOHN_FR34K"
    )

@bot.on_message(filters.command("upload"))
async def upload_file(client, message):
    try:
        if not message.reply_to_message:
            await message.reply_text(
                "❌ **Please reply to a .txt file containing links!**\n\n"
                "Send me a .txt file which contains links and reply with /upload"
            )
            return
        
        if not message.reply_to_message.document:
            await message.reply_text("❌ **Please send a .txt file!**")
            return
            
        file_name = message.reply_to_message.document.file_name
        if not file_name.endswith('.txt'):
            await message.reply_text("❌ **Only .txt files are supported!**")
            return
            
        editable = await message.reply_text("📥 **Processing .txt file...**")
        
        file_path = await message.reply_to_message.download()
        with open(file_path, 'r') as f:
            links = f.read().splitlines()
            
        if not links:
            await editable.edit("❌ **No links found in the file!**")
            os.remove(file_path)
            return
            
        await editable.edit(f"**𝕋ᴏᴛᴀʟ ʟɪɴᴋ𝕤 ғᴏᴜɴᴅ ᴀʀᴇ🔗🔗** **{len(links)}**\n\n**𝕊ᴇɴᴅ 𝔽ʀᴏᴍ ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ɪɴɪᴛɪᴀʟ ɪ𝕤** **1**")
        input0: Message = await bot.listen(editable.chat.id)
        raw_text = input0.text
        await input0.delete(True)

        await editable.edit("**Now Please Send Me Your Batch Name**")
        input1: Message = await bot.listen(editable.chat.id)
        raw_text0 = input1.text
        await input1.delete(True)

        await editable.edit("**𝔼ɴᴛᴇʀ ʀᴇ𝕤ᴏʟᴜᴛɪᴏɴ📸**\n144,240,360,480,720,1080 please choose quality")
        input2: Message = await bot.listen(editable.chat.id)
        raw_text2 = input2.text
        await input2.delete(True)
        try:
            if raw_text2 == "144":
                res = "256x144"
            elif raw_text2 == "240":
                res = "426x240"
            elif raw_text2 == "360":
                res = "640x360"
            elif raw_text2 == "480":
                res = "854x480"
            elif raw_text2 == "720":
                res = "1280x720"
            elif raw_text2 == "1080":
                res = "1920x1080" 
            else: 
                res = "UN"
        except Exception:
                res = "UN"

        await editable.edit("**Now Enter A Caption to add caption on your uploaded file**")
        input3: Message = await bot.listen(editable.chat.id)
        raw_text3 = input3.text
        await input3.delete(True)
        highlighter = f"️ ⁪⁬⁮⁮⁮"
        if raw_text3 == 'Robin':
            MR = highlighter 
        else:
            MR = raw_text3

        await editable.edit("**Now send the Thumb url**\nEg » https://graph.org/file/ce1723991756e48c35aa1.jpg \n Or if don't want thumbnail send = no")
        input6 = message = await bot.listen(editable.chat.id)
        raw_text6 = input6.text
        await input6.delete(True)
        await editable.delete()

        thumb = input6.text
        if thumb.startswith("http://") or thumb.startswith("https://"):
            getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
            thumb = "thumb.jpg"
        else:
            thumb = "no"

        if len(links) == 1:
            count = 1
        else:
            count = int(raw_text)

        for url in links[count-1:]:
            try:
                name1 = f"{raw_text0} {str(count).zfill(3)}"
                name = f'{str(count).zfill(3)}) {name1}'

                cc = f'**[📽️] Vid_ID:** {str(count).zfill(3)}. **{name1}{MR}.mkv\n**𝔹ᴀᴛᴄʜ** » **{raw_text0}**'
                cc1 = f'**[📁] Pdf_ID:** {str(count).zfill(3)}. {name1}{MR}.pdf \n**𝔹ᴀᴛᴄʜ** » **{raw_text0}**'

                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        copy = await bot.send_document(chat_id=message.chat.id, document=ka, caption=cc1)
                        count += 1
                        os.remove(ka)
                        time.sleep(1)
                    except FloodWait as e:
                        await message.reply_text(str(e))
                        time.sleep(e.x)
                        continue

                elif ".pdf" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=message.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as e:
                        await message.reply_text(str(e))
                        time.sleep(e.x)
                        continue
                else:
                    Show = f"**⥥ 🄳🄾🅆🄽🄻🄾🄰🄳🄸🄽🄶⬇️⬇️... »**\n\n**📝Name »** `{name}\n❄Quality » {raw_text2}`\n\n**🔗URL »** `{url}`"
                    prog = await message.reply_text(Show)
                    
                    if "youtu" in url:
                        if raw_text2 in ["144", "240", "360", "480", "720", "1080"]:
                            ytf = f"'bestvideo[height<={raw_text2}][ext=mp4]+bestaudio[ext=m4a]/best[height<={raw_text2}]/best'"
                        else:
                            ytf = "best"
                    else:
                        if res != "UN":
                            ytf = f"'bestvideo[height<={raw_text2}]+bestaudio/best[height<={raw_text2}]/best'"
                        else:
                            ytf = "best"

                    if "jw-prod" in url:
                        cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
                    else:
                        cmd = f'yt-dlp -f {ytf} "{url}" -o "{name}.mp4"'

                    download_cmd = f"{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args 'aria2c: -x 16 -j 32'"
                    os.system(download_cmd)
                    
                    if os.path.exists(f"{name}.mp4"):
                        await helper.send_vid(bot, message, cc, f"{name}.mp4", thumb, name, prog)
                        count += 1
                    else:
                        await prog.edit(f"❌ Failed to download: {url}")
                    
                    await prog.delete()
                    time.sleep(1)

            except Exception as e:
                await message.reply_text(
                    f"**❌ Downloading Failed**\n{str(e)}\n**Name** » {name}\n**Link** » `{url}`"
                )
                continue

        await message.reply_text("**𝔻ᴏɴᴇ 𝔹ᴏ𝕤𝕤😎**")
        
    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {str(e)}")

@bot.on_message(filters.command("stop"))
async def stop_process(client, message):
    try:
        os.system("pkill -9 yt-dlp")
        os.system("pkill -9 aria2c")
        await message.reply_text("**✅ All processes stopped!**")
    except Exception as e:
        await message.reply_text(f"❌ Error stopping processes: {str(e)}")

bot.run()
