import os
import re
import sys
import json
import time
import asyncio
import signal
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

# Global flag for graceful shutdown
is_shutting_down = False

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def cleanup():
    """Cleanup function to kill any running processes"""
    try:
        os.system("pkill -9 yt-dlp")
        os.system("pkill -9 aria2c")
        os.system("pkill -9 ffmpeg")
    except:
        pass

async def shutdown(signal, loop):
    """Cleanup and shutdown coroutines"""
    global is_shutting_down
    is_shutting_down = True
    
    print(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    await cleanup()
    
    [task.cancel() for task in tasks]
    print(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

def handle_exception(loop, context):
    """Global exception handler"""
    msg = context.get("exception", context["message"])
    print(f"Caught exception: {msg}")

# [Rest of the existing functions remain the same until the upload_file function]

@bot.on_message(filters.command("upload"))
async def upload_file(client, message):
    global is_shutting_down
    try:
        if is_shutting_down:
            await message.reply_text("Bot is shutting down. Please try again later.")
            return
            
        # [Rest of the existing upload_file function code remains the same]
        
    except asyncio.CancelledError:
        await message.reply_text("Operation cancelled due to bot shutdown")
    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {str(e)}")

@bot.on_message(filters.command("stop"))
async def stop_process(client, message):
    try:
        await cleanup()
        await message.reply_text("**✅ All processes stopped!**")
    except Exception as e:
        await message.reply_text(f"❌ Error stopping processes: {str(e)}")

def main():
    loop = asyncio.get_event_loop()
    
    # Set up signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGQUIT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(shutdown(s, loop))
        )
    
    # Set up exception handler
    loop.set_exception_handler(handle_exception)
    
    try:
        loop.run_until_complete(bot.run())
    finally:
        loop.close()

if __name__ == "__main__":
    main()