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
from utils import progress_bar, humanbytes, TimeFormatter

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def process_txt_file(file_path):
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            content = f.read()
        links = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                url_match = re.search(r'https?://[^\s<>"]+|www\.[^\s<>"]+', line)
                if url_match:
                    links.append(url_match.group())
        return links
    except Exception as e:
        print(f"Error processing txt file: {str(e)}")
        return None

async def download_file(url, name):
    try:
        if url.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            response = requests.get(url)
            if response.status_code == 200:
                with open(f"{name}.jpg", "wb") as f:
                    f.write(response.content)
                return f"{name}.jpg"
        else:
            cmd = f'yt-dlp -o "{name}.%(ext)s" "{url}" -R 25 --fragment-retries 25'
            os.system(cmd)
            for file in os.listdir():
                if file.startswith(name):
                    return file
        return None
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return None

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
            msg = await message.reply_text(
                "**Send me a .txt file containing links**\n\n"
                "ℹ️ I'll wait for the file..."
            )
            file_message = await bot.listen(message.chat.id, filters=filters.document)
            if not file_message.document:
                await msg.edit("❌ **Please send a .txt file!**")
                return
            if not file_message.document.file_name.endswith('.txt'):
                await msg.edit("❌ **Only .txt files are supported!**")
                return
            message.reply_to_message = file_message
            await msg.delete()
        
        if not message.reply_to_message.document:
            await message.reply_text("❌ **Please reply to a .txt file!**")
            return
            
        if not message.reply_to_message.document.file_name.endswith('.txt'):
            await message.reply_text("❌ **Only .txt files are supported!**")
            return
            
        editable = await message.reply_text("📥 **Processing .txt file...**")
        
        # Download and process the text file
        file_path = await message.reply_to_message.download()
        links = await process_txt_file(file_path)
        
        if not links:
            await editable.edit("❌ **No valid links found in the file!**")
            os.remove(file_path)
            return

        await editable.edit(f"**𝕋ᴏᴛᴀʟ ʟɪɴᴋ𝕤 ғᴏᴜɴᴅ ᴀʀᴇ🔗🔗** **{len(links)}**\n\n**𝕊ᴇɴᴅ 𝔽ʀᴏᴍ ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ɪɴɪᴛɪᴀʟ ɪ𝕤** **1**")
        input0 = await bot.listen(editable.chat.id)
        raw_text = input0.text
        await input0.delete(True)

        await editable.edit("**Now Please Send Me Your Batch Name**")
        input1 = await bot.listen(editable.chat.id)
        raw_text0 = input1.text
        await input1.delete(True)

        await editable.edit("**𝔼ɴᴛᴇʀ ʀᴇ𝕤ᴏʟᴜᴛɪᴏɴ📸**\n144,240,360,480,720,1080 please choose quality")
        input2 = await bot.listen(editable.chat.id)
        raw_text2 = input2.text
        await input2.delete(True)

        await editable.edit("Now Enter A Caption to add caption on your uploaded file")
        input3 = await bot.listen(editable.chat.id)
        raw_text3 = input3.text
        await input3.delete(True)
        
        highlighter = f"️ ⁪⁬⁮⁮⁮"
        MR = highlighter if raw_text3 == 'Robin' else raw_text3

        await editable.edit("Now send the Thumb url\nEg » https://graph.org/file/ce1723991756e48c35aa1.jpg \nOr if don't want thumbnail send = no")
        input6 = await bot.listen(editable.chat.id)
        raw_text6 = input6.text
        await input6.delete(True)
        await editable.delete()

        thumb = raw_text6
        if thumb.startswith(("http://", "https://")):
            getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
            thumb = "thumb.jpg"
        else:
            thumb = "no"

        count = 1 if len(links) == 1 else int(raw_text)

        for i in range(count-1, len(links)):
            try:
                url = links[i]
                name = f"{str(i+1).zfill(3)}) {raw_text0}"
                
                Show = f"**⥥ 🄳🄾🅆🄽🄻🄾🄰🄳🄸🄽🄶⬇️⬇️... »**\n\n**📝Name »** `{name}\n❄Quality » {raw_text2}`\n\n**🔗URL »** `{url}`"
                prog = await message.reply_text(Show)
                
                file_path = await download_file(url, name)
                
                if file_path:
                    if file_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        cc = f'**[🖼️] Img_ID:** {str(i+1).zfill(3)}. **{name}{MR}**\n**𝔹ᴀᴛᴄʜ** » **{raw_text0}**'
                        await bot.send_photo(
                            chat_id=message.chat.id,
                            photo=file_path,
                            caption=cc
                        )
                    elif file_path.endswith('.pdf'):
                        cc = f'**[📁] Pdf_ID:** {str(i+1).zfill(3)}. **{name}{MR}**\n**𝔹ᴀᴛᴄʜ** » **{raw_text0}**'
                        await bot.send_document(
                            chat_id=message.chat.id,
                            document=file_path,
                            caption=cc
                        )
                    else:
                        cc = f'**[📽️] Vid_ID:** {str(i+1).zfill(3)}. **{name}{MR}**\n**𝔹ᴀᴛᴄʜ** » **{raw_text0}**'
                        await bot.send_video(
                            chat_id=message.chat.id,
                            video=file_path,
                            caption=cc,
                            supports_streaming=True,
                            thumb=thumb if thumb != "no" else None
                        )
                    
                    os.remove(file_path)
                else:
                    await message.reply_text(f"Failed to download: {url}")
                
                await prog.delete()
                time.sleep(1)
                
            except Exception as e:
                await message.reply_text(f"**downloading Failed**\n{str(e)}\n**Name** » {name}\n**Link** » `{url}`")
                continue
                
        if thumb != "no" and os.path.exists(thumb):
            os.remove(thumb)
            
        await message.reply_text("**𝔻ᴏɴᴇ 𝔹ᴏ𝕤𝕤😎**")
                
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

@bot.on_message(filters.command("stop"))
async def stop_process(client, message):
    try:
        os.system("pkill -9 yt-dlp")
        os.system("pkill -9 aria2c")
        await message.reply_text("All processes stopped!")
    except Exception as e:
        await message.reply_text(f"Error stopping processes: {str(e)}")

bot.run()
