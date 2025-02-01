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

# Get environment variables with fallback
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Validate required environment variables
if not all([API_ID, API_HASH, BOT_TOKEN]):
    print("Error: Missing required environment variables. Please set API_ID, API_HASH, and BOT_TOKEN")
    sys.exit(1)

# Initialize bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def download_video(url, cmd, name):
    try:
        os.system(cmd)
        return f"{name}.mkv"
    except Exception as e:
        print(e)
        return None

async def send_vid(bot, m, cc, filename, thumb, name, prog):
    try:
        if thumb == "no":
            thumbnail = None
        else:
            thumbnail = thumb
            
        await bot.send_video(
            chat_id=m.chat.id,
            video=filename,
            caption=cc,
            thumb=thumbnail,
            duration=None
        )
        
        if os.path.exists(filename):
            os.remove(filename)
            
    except Exception as e:
        print(e)
        await prog.edit_text(f"Failed to upload: {str(e)}")

@bot.on_message(filters.command("start"))
async def start_message(client, message):
    text = "Hello! I am a TXT Leech Bot.\n\nI can download videos and PDFs from text files containing links.\nSend /help to know more about how to use me."
    await message.reply_text(text)

@bot.on_message(filters.command("help"))
async def help_message(client, message):
    text = "How to use me:\n\n1. Send me a text file (.txt) or document (.doc) containing links\n2. Use /upload command to start downloading\n3. Use /stop to cancel ongoing process\n\nFor support, contact @JOHN_FR34K"
    await message.reply_text(text)

@bot.on_message(filters.command("upload"))
async def upload_file(client, message):
    try:
        if not message.reply_to_message:
            await message.reply_text("Please reply to a text file (.txt) or document (.doc) containing links!")
            return
        
        if not message.reply_to_message.document:
            await message.reply_text("Please reply to a text file (.txt) or document (.doc)!")
            return
            
        file_name = message.reply_to_message.document.file_name.lower()
        if not (file_name.endswith('.txt') or file_name.endswith('.doc')):
            await message.reply_text("Please reply to a text file (.txt) or document (.doc)!")
            return
            
        editable = await message.reply_text("Processing...")
        
        file = await message.reply_to_message.download()
        links = []
        
        with open(file, 'r') as f:
            links = f.read().splitlines()
            
        if not links:
            await editable.edit("No links found in the file!")
            os.remove(file)
            return

        # Show total links and ask for starting number
        await editable.edit(f"**𝕋ᴏᴛᴀʟ ʟɪɴᴋ𝕤 ғᴏᴜɴᴅ ᴀʀᴇ🔗🔗** **{len(links)}**\n\n**𝕊ᴇɴᴅ 𝔽ʀᴏᴍ ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ɪɴɪᴛɪᴀʟ ɪ𝕤** **1**")
        input0: Message = await bot.listen(editable.chat.id)
        raw_text = input0.text
        await input0.delete(True)
        
        # Ask for batch name
        await editable.edit("**Now Please Send Me Your Batch Name**")
        input1: Message = await bot.listen(editable.chat.id)
        raw_text0 = input1.text
        await input1.delete(True)
        
        # Ask for resolution
        await editable.edit("**𝔼ɴᴛᴇʀ ʀᴇ𝕤ᴏʟᴜᴛɪᴏɴ📸**\n144,240,360,480,720,1080 please choose quality")
        input2: Message = await bot.listen(editable.chat.id)
        raw_text2 = input2.text
        await input2.delete(True)
        
        # Set resolution
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
        
        # Ask for caption
        await editable.edit("Now Enter A Caption to add caption on your uploaded file")
        input3: Message = await bot.listen(editable.chat.id)
        raw_text3 = input3.text
        await input3.delete(True)
        highlighter = f"️ ⁪⁬⁮⁮⁮"
        if raw_text3 == 'Robin':
            MR = highlighter 
        else:
            MR = raw_text3
        
        # Ask for thumbnail
        await editable.edit("Now send the Thumb url\nEg » https://graph.org/file/ce1723991756e48c35aa1.jpg \n Or if don't want thumbnail send = no")
        input6 = message = await bot.listen(editable.chat.id)
        raw_text6 = input6.text
        await input6.delete(True)
        
        # Process thumbnail
        thumb = input6.text
        if thumb.startswith("http://") or thumb.startswith("https://"):
            getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
            thumb = "thumb.jpg"
        else:
            thumb = "no"
            
        # Start downloading from the specified index
        try:
            start_index = int(raw_text) - 1
            if start_index < 0:
                start_index = 0
        except ValueError:
            start_index = 0
            
        download_path = os.path.join(os.getcwd(), "downloads", raw_text0)
        os.makedirs(download_path, exist_ok=True)
        
        await editable.edit("Starting download with selected settings...")
        count = start_index + 1
        
        for i, url in enumerate(links[start_index:], start_index + 1):
            try:
                name = f"{str(count).zfill(3)}"
                
                if "drive" in url or ".pdf" in url.lower():
                    cc1 = f'**[📁] Pdf_ID:** {str(count).zfill(3)}. {name}{MR}.pdf \n**𝔹ᴀᴛᴄʜ** » **{raw_text0}**'
                    
                    if "drive" in url:
                        try:
                            ka = await download(url, name)
                            copy = await bot.send_document(chat_id=message.chat.id, document=ka, caption=cc1)
                            count += 1
                            os.remove(ka)
                            time.sleep(1)
                        except FloodWait as e:
                            await message.reply_text(str(e))
                            time.sleep(e.x)
                            continue
                    else:
                        try:
                            cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                            download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                            os.system(download_cmd)
                            copy = await bot.send_document(
                                chat_id=message.chat.id,
                                document=f'{name}.pdf',
                                caption=cc1
                            )
                            count += 1
                            os.remove(f'{name}.pdf')
                        except FloodWait as e:
                            await message.reply_text(str(e))
                            time.sleep(e.x)
                            continue
                else:
                    cc = f'**[📽️] Vid_ID:** {str(count).zfill(3)}. {name}{MR}.mkv\n**𝔹ᴀᴛᴄʜ** » **{raw_text0}**'
                    Show = f"**⥥ 🄳🄾🅆🄽🄻🄾🄰🄳🄸🄽🄶⬇️⬇️... »**\n\n**📝Name »** `{name}\n❄Quality » {raw_text2}`\n\n**🔗URL »** `{url}`"
                    prog = await message.reply_text(Show)
                    
                    cmd = f'yt-dlp -f "b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba" "{url}" -o "{name}.mkv" -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32"'
                    
                    res_file = await download_video(url, cmd, name)
                    if res_file:
                        await prog.delete(True)
                        await send_vid(bot, message, cc, res_file, thumb, name, prog)
                        count += 1
                        time.sleep(1)
                    
            except Exception as e:
                await message.reply_text(
                    f"**downloading Interrupted**\n{str(e)}\n**Name** » {name}\n**Link** » `{url}`"
                )
                continue
                
        await message.reply_text("**𝔻ᴏɴᴇ 𝔹ᴏ𝕤𝕤😎**")
        
        if thumb != "no" and os.path.exists(thumb):
            os.remove(thumb)
        
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

if __name__ == "__main__":
    print("Bot is starting...")
    bot.run()