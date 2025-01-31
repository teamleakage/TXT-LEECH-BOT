# Created by @JOHN_FR34K
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
            await message.reply_text("Please reply to a text file containing links!")
            return
        
        if not message.reply_to_message.document:
            await message.reply_text("Please reply to a text file!")
            return
            
        if not message.reply_to_message.document.file_name.endswith('.txt'):
            await message.reply_text("Please reply to a text file!")
            return
            
        msg = await message.reply_text("Processing...")
        
        file = await message.reply_to_message.download()
        links = []
        
        with open(file, 'r') as f:
            links = f.read().splitlines()
            
        if not links:
            await msg.edit("No links found in the text file!")
            os.remove(file)
            return
            
        await msg.edit(f"Found {len(links)} links. Starting download...")
        
        for i, link in enumerate(links, 1):
            try:
                command = f'yt-dlp -f "b[height<=720]/bv[height<=720]+ba/b/bv+ba" "{link}" -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32"'
                os.system(command)
                await msg.edit(f"Downloaded {i}/{len(links)}")
            except Exception as e:
                await msg.edit(f"Error downloading link {i}: {str(e)}")
                continue
                
        await msg.edit("All downloads completed!")
        os.remove(file)
        
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
