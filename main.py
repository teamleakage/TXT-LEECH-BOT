import os
import re
import sys
import json
import time
import asyncio
import logging
import requests
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import m3u8
from Cryptodome.Cipher import AES
import base64
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get environment variables with fallback
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Initialize bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Constants
SUPPORTED_FORMATS = ['.txt', '.doc', '.docx']
MAX_RETRIES = 3
RETRY_DELAY = 5
CHUNK_SIZE = 2048

class DownloadError(Exception):
    """Custom exception for download errors"""
    pass

async def process_url(url, raw_text2):
    """Process and transform URLs based on their type"""
    try:
        if isinstance(url, (list, tuple)) and len(url) > 1:
            V = url[1].replace("file/d/","uc?export=download&id=") \
                  .replace("www.youtube-nocookie.com/embed", "youtu.be") \
                  .replace("?modestbranding=1", "") \
                  .replace("/view?usp=sharing","")
            url = "https://" + V
        
        if "visionias" in url:
            async with ClientSession() as session:
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Pragma': 'no-cache',
                    'Referer': 'http://www.visionias.in/',
                    'Sec-Fetch-Dest': 'iframe',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'cross-site',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
                    'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-platform': '"Android"'
                }
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        raise DownloadError(f"Failed to fetch VisionIAS URL: {resp.status}")
                    text = await resp.text()
                    match = re.search(r"(https://.*?playlist.m3u8.*?)\"", text)
                    if not match:
                        raise DownloadError("Failed to extract m3u8 URL from VisionIAS page")
                    url = match.group(1)
        
        elif 'videos.classplusapp' in url:
            headers = {
                'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30.hM33P2ai6ivdzxPPfm01LAd4JWv-vnrSxGXqvCirCSpUfhhofpeqyeHPxtstXwe0'
            }
            response = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers=headers)
            if response.status_code != 200:
                raise DownloadError(f"Failed to fetch Classplus URL: {response.status_code}")
            url = response.json()['url']
        
        elif '/master.mpd' in url:
            id = url.split("/")[-2]
            url = f"https://d26g5bnklkwsh4.cloudfront.net/{id}/master.m3u8"
        
        # Determine format based on URL type
        if "youtu" in url:
            ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
        else:
            ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
            
        return url, ytf
    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}")
        raise

async def download_video(url, cmd, name, retries=MAX_RETRIES):
    """Download video with retry mechanism"""
    for attempt in range(retries):
        try:
            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            elif "m3u8" in url:
                cmd = f'yt-dlp -f "best" "{url}" -o "{name}.mp4"'
                
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise DownloadError(f"Download failed: {stderr.decode()}")
            
            if os.path.exists(f"{name}.mp4"):
                return f"{name}.mp4"
            elif os.path.exists(f"{name}.mkv"):
                return f"{name}.mkv"
                
            raise DownloadError("Output file not found")
            
        except Exception as e:
            logger.error(f"Download attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                raise
    
    return None

@bot.on_message(filters.command("start"))
async def start_message(client, message):
    await message.reply_text(
        "**Welcome to Video Downloader Bot!**\n\n"
        "I can download videos from text files containing links.\n"
        "Supported file formats: TXT, DOC, DOCX\n\n"
        "Send /help to know more about how to use me."
    )

@bot.on_message(filters.command("help"))
async def help_message(client, message):
    await message.reply_text(
        "**How to use me:**\n\n"
        "1. Send me a text file containing video links\n"
        "2. Reply to the file with /upload command\n"
        "3. Follow the prompts to select:\n"
        "   - Starting point\n"
        "   - Batch name\n"
        "   - Video quality\n"
        "   - Caption\n"
        "   - Thumbnail\n\n"
        "4. Use /stop to cancel ongoing process\n\n"
        "**Supported Platforms:**\n"
        "- YouTube\n"
        "- VisionIAS\n"
        "- Classplus\n"
        "- Direct video links\n"
        "- M3U8 streams"
    )

@bot.on_message(filters.command("upload"))
async def upload_file(client, message):
    try:
        if not message.reply_to_message:
            await message.reply_text("Please reply to a file containing links!")
            return
        
        if not message.reply_to_message.document:
            await message.reply_text("Please reply to a document!")
            return
        
        file_name = message.reply_to_message.document.file_name
        if not any(file_name.lower().endswith(fmt) for fmt in SUPPORTED_FORMATS):
            await message.reply_text(f"Please send a supported file format: {', '.join(SUPPORTED_FORMATS)}")
            return
        
        msg = await message.reply_text("Processing file...")
        file = await message.reply_to_message.download()
        
        with open(file, 'r') as f:
            links = f.read().splitlines()
        
        if not links:
            await msg.edit("No links found in the file!")
            os.remove(file)
            return
        
        await msg.edit(f"**𝕋ᴏᴛᴀʟ ʟɪɴᴋ𝕤 ғᴏᴜɴᴅ ᴀʀᴇ🔗🔗** **{len(links)}**\n\n**𝕊ᴇɴᴅ 𝔽ʀᴏᴍ ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ɪɴɪᴛɪᴀʟ ɪ𝕤** **1**")
        input0: Message = await bot.listen(msg.chat.id)
        raw_text = input0.text
        await input0.delete(True)
        
        await msg.edit("**Now Please Send Me Your Batch Name**")
        input1: Message = await bot.listen(msg.chat.id)
        raw_text0 = input1.text
        await input1.delete(True)
        
        await msg.edit("**𝔼ɴᴛᴇʀ ʀᴇ𝕤ᴏʟᴜᴛɪᴏɴ📸**\n144,240,360,480,720,1080")
        input2: Message = await bot.listen(msg.chat.id)
        raw_text2 = input2.text
        await input2.delete(True)
        
        resolutions = {'144': '256x144', '240': '426x240', '360': '640x360',
                      '480': '854x480', '720': '1280x720', '1080': '1920x1080'}
        res = resolutions.get(raw_text2, 'UN')
        
        await msg.edit("**Enter caption for your files**")
        input3: Message = await bot.listen(msg.chat.id)
        raw_text3 = input3.text
        await input3.delete(True)
        
        MR = raw_text3 if raw_text3 != 'Robin' else '️ ⁪⁬⁮⁮⁮'
        
        await msg.edit("**Send thumbnail URL or 'no' for no thumbnail**\nExample: https://example.com/thumb.jpg")
        input6: Message = await bot.listen(msg.chat.id)
        thumb = input6.text
        await input6.delete(True)
        
        if thumb.startswith(("http://", "https://")):
            getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
            thumb = "thumb.jpg"
        else:
            thumb = "no"
        
        await msg.delete()
        
        count = int(raw_text)
        for i in range(count - 1, len(links)):
            try:
                url, ytf = await process_url(links[i], raw_text2)
                name1 = links[i][0] if isinstance(links[i], (list, tuple)) else url.split('/')[-1]
                name1 = re.sub(r'[^\w\s-]', '', name1)[:60]
                name = f'{str(count).zfill(3)}) {name1}'
                
                prog = await message.reply_text(
                    f"**⥥ 🄳🄾🅆🄽🄻🄾🄰🄳🄸🄽🄶⬇️⬇️... »**\n\n"
                    f"**📝Name »** `{name}\n❄Quality » {raw_text2}`\n\n"
                    f"**🔗URL »** `{url}`"
                )
                
                res_file = await download_video(url, ytf, name)
                if res_file:
                    cc = f'**[📽️] Vid_ID:** {str(count).zfill(3)}. {name1}{MR}.mkv\n**𝔹ᴀᴛᴄʜ** » **{raw_text0}**'
                    await prog.delete()
                    await send_vid(bot, message, cc, res_file, thumb, name, prog)
                    count += 1
                    await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing link {i}: {str(e)}")
                await message.reply_text(
                    f"**Download Interrupted**\n{str(e)}\n"
                    f"**Name** » {name}\n**Link** » `{url}`"
                )
                continue
        
        await message.reply_text("**𝔻ᴏɴᴇ 𝔹ᴏ𝕤𝕤😎**")
        
    except Exception as e:
        logger.error(f"Main error: {str(e)}")
        await message.reply_text(f"An error occurred: {str(e)}")

@bot.on_message(filters.command("stop"))
async def stop_process(client, message):
    try:
        os.system("pkill -9 yt-dlp")
        os.system("pkill -9 aria2c")
        await message.reply_text("**All downloads stopped!**")
    except Exception as e:
        await message.reply_text(f"Error stopping processes: {str(e)}")

bot.run()
