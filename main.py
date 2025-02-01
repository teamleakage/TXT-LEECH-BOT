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

async def download_classplus_m3u8(url, name, quality):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://web.classplusapp.com/',
            'Origin': 'https://web.classplusapp.com'
        }

        # First get the master m3u8
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None

        # Parse master playlist
        master = m3u8.loads(response.text)
        
        # Get the highest quality playlist URL that's below or equal to requested quality
        selected_playlist = None
        max_height = 0
        
        for playlist in master.playlists:
            stream_height = playlist.stream_info.resolution[1] if playlist.stream_info.resolution else 0
            if stream_height <= int(quality) and stream_height > max_height:
                max_height = stream_height
                selected_playlist = playlist

        if not selected_playlist:
            selected_playlist = master.playlists[0]  # Fallback to first playlist

        playlist_url = selected_playlist.uri
        if not playlist_url.startswith('http'):
            playlist_url = url.rsplit('/', 1)[0] + '/' + playlist_url

        # Download using ffmpeg directly
        cmd = [
            'ffmpeg',
            '-headers', f'User-Agent: {headers["User-Agent"]}',
            '-headers', f'Referer: {headers["Referer"]}',
            '-headers', f'Origin: {headers["Origin"]}',
            '-i', playlist_url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            f'{name}.mp4'
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
        if os.path.exists(f"{name}.mp4"):
            return f"{name}.mp4"
        return None
        
    except Exception as e:
        print(f"Error downloading Classplus m3u8: {str(e)}")
        return None

async def download_file(url, name, quality):
    try:
        if url.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            response = requests.get(url)
            if response.status_code == 200:
                with open(f"{name}.jpg", "wb") as f:
                    f.write(response.content)
                return f"{name}.jpg"
        elif '.m3u8' in url and 'classplusapp.com' in url:
            return await download_classplus_m3u8(url, name, quality)
        else:
            if quality in ["144", "240", "360", "480", "720", "1080"]:
                ytf = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}]/best'
            else:
                ytf = "best"
                
            cmd = [
                'yt-dlp',
                '-f', ytf,
                '-o', f'{name}.%(ext)s',
                '-R', '25',
                '--fragment-retries', '25',
                '--external-downloader', 'aria2c',
                '--downloader-args', 'aria2c:-x 16 -j 32',
                url
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            for file in os.listdir():
                if file.startswith(name):
                    return file
        return None
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return None

async def send_media_and_reply(bot, message, file_path, caption):
    try:
        start_time = time.time()
        if file_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            await message.reply_photo(
                file_path,
                caption=caption,
                progress=progress_bar,
                progress_args=(message, "Uploading...", start_time)
            )
        else:
            await message.reply_video(
                file_path,
                caption=caption,
                progress=progress_bar,
                progress_args=(message, "Uploading...", start_time)
            )
        return True
    except Exception as e:
        print(f"Error sending media: {str(e)}")
        return False

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
                await msg.edit("❌ **Please send a file!**")
                return
                
            if not file_message.document.file_name.endswith('.txt'):
                await msg.edit("❌ **Only .txt files are supported!**")
                return
                
            message.reply_to_message = file_message
            await msg.delete()
        
        if not message.reply_to_message.document:
            await message.reply_text("❌ **Please send a .txt file!**")
            return
            
        file_name = message.reply_to_message.document.file_name
        if not file_name.endswith('.txt'):
            await message.reply_text("❌ **Only .txt files are supported!**")
            return
            
        editable = await message.reply_text("📥 **Processing .txt file...**")
        
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
        
        await editable.edit("**Now Enter A Caption to add caption on your uploaded file**")
        input3 = await bot.listen(editable.chat.id)
        raw_text3 = input3.text
        await input3.delete(True)
        
        highlighter = f"️ ⁪⁬⁮⁮⁮"
        MR = raw_text3 if raw_text3 != 'Robin' else highlighter

        await editable.edit("**Now send the Thumb url**\nEg » https://graph.org/file/ce1723991756e48c35aa1.jpg \n Or if don't want thumbnail send = no")
        input6 = await bot.listen(editable.chat.id)
        raw_text6 = input6.text
        await input6.delete(True)
        await editable.delete()

        thumb = raw_text6
        if thumb.startswith("http://") or thumb.startswith("https://"):
            getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
            thumb = "thumb.jpg"
        else:
            thumb = "no"

        if len(links) == 1:
            count = 1
        else:
            count = int(raw_text)

        for i, url in enumerate(links[count-1:], count):
            try:
                name1 = f"{raw_text0} {str(i).zfill(3)}"
                name = f'{str(i).zfill(3)}) {name1}'

                if url.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    cc = f'**[📸] Img_ID:** {str(i).zfill(3)}. **{name1}{MR}.jpg\n**𝔹ᴀᴛᴄʜ** » **{raw_text0}**'
                else:
                    cc = f'**[📽️] Vid_ID:** {str(i).zfill(3)}. **{name1}{MR}.mp4\n**𝔹ᴀᴛᴄʜ** » **{raw_text0}**'

                Show = f"**⥥ 🄳🄾🅆🄽🄻🄾🄰🄳🄸🄽🄶⬇️⬇️... »**\n\n**📝Name »** `{name}\n❄Quality » {raw_text2}`\n\n**🔗URL »** `{url}`"
                prog = await message.reply_text(Show)
                
                file_path = await download_file(url, name, raw_text2)
                
                if file_path:
                    success = await send_media_and_reply(bot, message, file_path, cc)
                    if success:
                        os.remove(file_path)
                    else:
                        await prog.edit(f"❌ Failed to upload: {url}")
                else:
                    await prog.edit(f"❌ Failed to download: {url}")
                
                await prog.delete()
                await asyncio.sleep(1)

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
        os.system("pkill -9 ffmpeg")
        await message.reply_text("**✅ All processes stopped!**")
    except Exception as e:
        await message.reply_text(f"❌ Error stopping processes: {str(e)}")

bot.run()
