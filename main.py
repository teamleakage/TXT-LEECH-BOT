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
        
        # Try to get video metadata
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

async def progress_bar(current, total, name, message, start):
    """Show progress bar for uploads"""
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "[{0}{1}] \nPercentage: {2}%\n".format(
            ''.join(["●" for i in range(math.floor(percentage / 5))]),
            ''.join(["○" for i in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))

        tmp = progress + "{0} of {1}\nSpeed: {2}/s\nETA: {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(
                text=f"{name}\n {tmp}"
            )
        except:
            pass

def humanbytes(size):
    """Convert bytes to human readable format"""
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(milliseconds: int) -> str:
    """Format milliseconds to readable time string"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2]

[Previous code continues unchanged...]
