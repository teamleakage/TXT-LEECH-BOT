import os
import time
import asyncio
from utils import progress_bar

async def download(url, name):
    """Download file from Google Drive"""
    try:
        cmd = f'yt-dlp -o "{name}" "{url}"'
        os.system(cmd)
        return name
    except Exception as e:
        print(f"Download error: {str(e)}")
        return None

async def download_video(url, cmd, name):
    """Download video using yt-dlp"""
    try:
        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
        os.system(download_cmd)
        return f"{name}.mp4"
    except Exception as e:
        print(f"Video download error: {str(e)}")
        return None

async def send_vid(bot, m, cc, filename, thumb, name, prog):
    """Send video file to chat"""
    try:
        start_time = time.time()
        duration = 0
        
        if os.path.exists(filename):
            await bot.send_video(
                chat_id=m.chat.id,
                video=filename,
                caption=cc,
                thumb=thumb if thumb != "no" else None,
                duration=duration,
                progress=progress_bar,
                progress_args=(
                    "Uploading...",
                    prog,
                    start_time
                )
            )
            
            # Cleanup
            if os.path.exists(filename):
                os.remove(filename)
            if thumb != "no" and os.path.exists(thumb):
                os.remove(thumb)
                
        return True
    except Exception as e:
        print(f"Send video error: {str(e)}")
        if os.path.exists(filename):
            os.remove(filename)
        if thumb != "no" and os.path.exists(thumb):
            os.remove(thumb)
        return False