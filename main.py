import os
import re
import sys
import json
import time
import math
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
from utils import progress_bar, humanbytes, TimeFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import variables from vars.py
from vars import API_ID, API_HASH, BOT_TOKEN

# Initialize bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def extract_links_from_txt(file_path):
    """Extract and validate links from a .txt file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract links using regex pattern
            url_pattern = r'https?://[^\s<>"\']+'
            links = re.findall(url_pattern, content)
            return [link.strip() for link in links if link.strip()]
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
            url_pattern = r'https?://[^\s<>"\']+'
            links = re.findall(url_pattern, content)
            return [link.strip() for link in links if link.strip()]
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return []

async def process_link(link):
    """Process and transform links if needed"""
    try:
        if 'visionias' in link:
            async with ClientSession() as session:
                async with session.get(link, headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Pragma': 'no-cache',
                    'Referer': 'http://www.visionias.in/',
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36'
                }) as resp:
                    text = await resp.text()
                    link = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)
        
        elif 'videos.classplusapp' in link:
            response = requests.get(
                f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={link}', 
                headers={'x-access-token': 'your-token-here'}
            ).json()
            link = response['url']
        
        elif '/master.mpd' in link:
            id = link.split("/")[-2]
            link = f"https://d26g5bnklkwsh4.cloudfront.net/{id}/master.m3u8"
            
        return link
    except Exception as e:
        logger.error(f"Error processing link: {str(e)}")
        return link

async def send_vid(bot, message, cc, filename, thumb, name, prog):
    """Send video file to user"""
    try:
        if thumb == "no":
            thumbnail = None
        else:
            thumbnail = thumb
            
        duration = 0
        width = 0
        height = 0
        
        try:
            metadata = await bot.get_file_metadata(filename)
            if metadata:
                duration = metadata.duration
                width = metadata.width
                height = metadata.height
        except:
            pass
            
        start_time = time.time()
        
        try:
            await message.reply_video(
                video=filename,
                caption=cc,
                supports_streaming=True,
                height=height,
                width=width,
                duration=duration,
                thumb=thumbnail,
                progress=progress_bar,
                progress_args=(name, prog, start_time)
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            await message.reply_video(
                video=filename,
                caption=cc,
                supports_streaming=True,
                height=height,
                width=width,
                duration=duration,
                thumb=thumbnail,
                progress=progress_bar,
                progress_args=(name, prog, start_time)
            )
            
        os.remove(filename)
        if thumb != "no":
            os.remove(thumb)
            
    except Exception as e:
        await prog.edit(f"Failed to upload video: {str(e)}")
        if os.path.exists(filename):
            os.remove(filename)
        if thumb != "no" and os.path.exists(thumb):
            os.remove(thumb)
        raise

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
        "1. Send me a .txt file containing video links\n"
        "2. Reply to the .txt file with /upload command\n"
        "3. Use /stop to cancel ongoing process\n\n"
        "For support, contact @JOHN_FR34K"
    )

@bot.on_message(filters.command("upload"))
async def upload_file(client, message):
    try:
        if not message.reply_to_message:
            await message.reply_text("Please reply to a .txt file containing links!")
            return
        
        if not message.reply_to_message.document:
            await message.reply_text("Please reply to a .txt file!")
            return
            
        file_name = message.reply_to_message.document.file_name
        if not file_name.endswith('.txt'):
            await message.reply_text("Only .txt files are supported! Please send a .txt file.")
            return
            
        msg = await message.reply_text("📥 Downloading .txt file...")
        
        # Download the .txt file
        file_path = await message.reply_to_message.download()
        
        # Extract links from the .txt file
        links = await extract_links_from_txt(file_path)
            
        if not links:
            await msg.edit("❌ No valid links found in the .txt file!")
            os.remove(file_path)
            return
            
        await msg.edit(f"✅ Found {len(links)} links in the .txt file\n⏳ Starting downloads...")
        count = 1
        
        for i, link in enumerate(links, 1):
            try:
                # Process the link
                processed_link = await process_link(link)
                
                name1 = f"video_{str(i).zfill(3)}"
                name = f'{str(count).zfill(3)}) {name1}'
                
                if "youtu" in processed_link:
                    ytf = "b[height<=720][ext=mp4]/bv[height<=720][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
                else:
                    ytf = "b[height<=720]/bv[height<=720]+ba/b/bv+ba"

                if "jw-prod" in processed_link:
                    cmd = f'yt-dlp -o "{name}.mp4" "{processed_link}"'
                else:
                    cmd = f'yt-dlp -f "{ytf}" "{processed_link}" -o "{name}.mp4"'

                download_cmd = f"{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args 'aria2c: -x 16 -j 32'"
                
                Show = f"**⬇️ Downloading Video {i}/{len(links)} **\n\n**📝 Name »** `{name}`\n\n**🔗 URL »** `{processed_link}`"
                prog = await message.reply_text(Show)
                
                os.system(download_cmd)
                
                if os.path.exists(f"{name}.mp4"):
                    cc = f'**[📽️] Video {str(count).zfill(3)}:** {name1}.mp4'
                    await send_vid(bot, message, cc, f"{name}.mp4", "no", name, prog)
                    count += 1
                else:
                    await prog.edit(f"❌ Failed to download: {processed_link}")
                
                await prog.delete()
                
            except Exception as e:
                await message.reply_text(f"❌ Error downloading link {i}: {str(e)}")
                continue
                
        await msg.edit("✅ All downloads completed!")
        os.remove(file_path)
        
    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {str(e)}")

@bot.on_message(filters.command("stop"))
async def stop_process(client, message):
    try:
        os.system("pkill -9 yt-dlp")
        os.system("pkill -9 aria2c")
        await message.reply_text("✅ All processes stopped!")
    except Exception as e:
        await message.reply_text(f"❌ Error stopping processes: {str(e)}")

bot.run()
