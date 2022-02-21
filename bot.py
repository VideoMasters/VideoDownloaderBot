import io
import json
import re
import os
import sys
import asyncio
import logging
import time
from textwrap import dedent
from subprocess import getstatusoutput
from typing import BinaryIO, Union
from get_video_info import get_video_attributes, get_video_thumb
import requests
from dotenv import load_dotenv
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from pyromod import listen
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from p_bar import progress_bar

load_dotenv()
os.makedirs("./downloads", exist_ok=True)

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
NAME = os.environ.get("NAME")

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, sleep_threshold=120)

with bot:
    BOT = bot.get_me().username.lower()

auth_users = [ int(chat) for chat in os.environ.get("AUTH_USERS").split(",") if chat != '']
sudo_groups = [ int(chat) for chat in os.environ.get("GROUPS").split(",")  if chat != '']
sudo_json_groups = [ int(chat) for chat in os.environ.get("JSON_GROUPS").split(",")  if chat != '']
sudo_users = auth_users
print(sudo_groups, sudo_json_groups, sudo_users)

DEF_FORMAT = "360"
thumb = os.environ.get("THUMB")
if thumb.startswith("http://") or thumb.startswith("https://"):
    getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
    thumb = "thumb.jpg"

file_handler = logging.FileHandler(filename="bot.log", mode="w")
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]
logging.basicConfig(
    format="%(name)s - %(levelname)s - %(message)s\n",
    level=logging.WARNING,
    handlers=handlers,
)
logger = logging.getLogger(__name__)


async def query_same_user_filter_func(_, __, query):
    message = query.message.reply_to_message
    if message.from_user is None:
        return True
    if query.from_user.id != message.from_user.id:
        await query.answer("❌ Not for you", True)
        return False
    else:
        return True


async def query_document_filter_func(_, __, query):
    msg = query.message.reply_to_message
    msg = await __.get_messages(msg.chat.id, msg.message_id)
    if msg.document is not None:
        return True
    elif msg.reply_to_message is not None:
        if msg.reply_to_message.document is not None:
            return True
        else:
            return False
    else:
        return False


query_same_user = filters.create(query_same_user_filter_func)
query_document = filters.create(query_document_filter_func)


@bot.on_message(filters.command("start"))
async def start(bot, message):
    await message.reply("Send video link or json")


async def send_video(bot: Client, message: Message, path, caption, filename, thumbnail: Union[str, BinaryIO]):
    global thumb

    reply = await message.reply("Uploading Video")

    try:
        if isinstance(thumbnail, str):
            if thumb == "" or thumbnail.upper() == "V":
                thumb_to_send = get_video_thumb(path)
            elif thumbnail.upper() == "N":
                thumb_to_send = thumb
        else:
            thumb_to_send = thumbnail
    except:
        logger.exception("Error generating gIl")
        thumb_to_send = "thumb.jpg"

    try:
        duration, width, height = get_video_attributes(path)
    except:
        logger.exception("Error fetching attributes")
        duration = width = height = 0

    start_time = time.time()
    await bot.send_video(
        message.chat.id,
        video=path,
        caption=caption,
        duration=duration,
        width=width,
        height=height,
        thumb=thumb_to_send,
        reply_to_message_id=message.message_id,
        file_name=filename,
        supports_streaming=True,
        progress=progress_bar,
        progress_args=(reply,start_time),
    )
    await reply.delete()


@bot.on_message(
    (
        (filters.command("download_json"))
        | filters.regex(f"^/download_json@{BOT}")
    )
    & (filters.chat(sudo_json_groups) | filters.user(sudo_users))
)
async def download_json_info(bot: Client, message: Message):
    json_ans = await bot.ask(message.chat.id, "Send json")
    try:
        if json_ans.document.mime_type != "application/json":
            return
        file_name = json_ans.document.file_name
    except:
        return
    json_file = f"./downloads/{message.chat.id}/{file_name}"
    await json_ans.download(json_file)
    videos_dict = json.load(open(json_file))
    opt_ques = """\
    Send options in this format
    FORMAT|START(OPT)|N1|N2|...(OPT)
    \n
    By default start from 1,
    n1, n2, .. index instead of start to only download those indexes
    \n
    e.g. 360 or 480|34 or 720||3|27
    """
    opt_ans = await bot.ask(message.chat.id, dedent(opt_ques))
    opt_ans = opt_ans.text
    opt_parts = opt_ans.split("|")
    start = ''
    req_vids = []
    try:
        vid_format, start, *req_vids = opt_parts
    except:
        try:
            vid_format, start = opt_parts
        except:
            vid_format = opt_parts[0]
    videos = []
    for topic, vids in videos_dict.items():
        for title, link in vids.items():
            videos.append((link, vid_format, title, topic))
    req_videos = []
    if req_vids:
        videos_ = [(int(vid), videos[int(vid) -1]) for vid in req_vids]
        req_videos += videos_
    elif not start:
        start = '1'
    if start:
        videos_ = videos[int(start) - 1:]
        req_videos += enumerate(req_videos, int(start))
    req_videos = sorted(set(req_videos))
    n = len(req_videos)
    thumb_ques = "Send custom thumbnail url or N for default or V for video thumbnail."
    thumbnail = await bot.ask(message.chat.id, thumb_ques)
    thumbnail = thumbnail.text
    await message.reply(f"Downloading!!! {n} videos")
    await download_videos(bot, message, req_videos, thumbnail)


def is_vimeo(link):
    webpage_cmd = f"curl -s '{link}'"
    st_web, webpage = getstatusoutput(webpage_cmd)

    vimeo_urls = []
    for match in re.finditer(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//player\.vimeo\.com/video/\d+.*?)\1',
            webpage):
        vimeo_urls.append(match)

    return len(vimeo_urls) == 1


def download_video(chat_id, video):
    link, vid_format, title, topic = video

    if "youtu" in link:
        if vid_format in ["144", "240", "480"]:
            ytf = f"b[height<={vid_format}][ext=mp4]/bv[height<={vid_format}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
        elif vid_format == "360":
            ytf = 18
        elif vid_format == "720":
            ytf = 22
        else:
            ytf = 18

        if "/youtube/" in link:
            link = f"https://youtube.com/watch?v={link.split('/')[-1]}"
    elif ("/brightcove/" in link ):
        if vid_format not in ["144", "240", "360", "480", "720"]:
            vid_format = "360"
        ytf = f"b[height<={vid_format}]/bv[height<={vid_format}]+ba"
    elif ("/jw/" in link):
        if vid_format == "144":
            vid_format = "180"
        elif vid_format == "240":
            vid_format = "270"
        elif vid_format == "360":
            vid_format = "360"
        elif vid_format == "480":
            vid_format = "540"
        elif vid_format == "720":
            vid_format = "720"
        else:
            vid_format = "360"
        ytf = f"b[height<={vid_format}]"
    elif is_vimeo(link) or ("/vimeo/" in link  and link.split('/')[1].isnumeric()):
        if vid_format == "144":
            ytf = f"http-240p"
        elif vid_format == "240":
            ytf = f"http-240p"
        elif vid_format == "360":
            ytf = "http-360p"
        elif vid_format == "480":
            ytf = "http-540p"
        elif vid_format == "720":
            ytf = "http-720p"
        else:
            ytf = "http-360p"
        link = f"https://player.vimeo.com/video/{link.split('/')[-1]}"
    elif (any([x in link for x in ["/m3u8", "/mpd"]])):
        ytf = f"b[height<={vid_format}]/bv[height<={vid_format}]+ba"
    else:
        ytf = f"b[height<={vid_format}]/bv[height<={vid_format}]+ba"

    ytf = f"{ytf}/b[height<={DEF_FORMAT}]/bv[height<={DEF_FORMAT}]+ba/b/bv+ba"

    cmd = (
        f"yt-dlp --socket-timeout 30 -R 25 --no-warning '{link}'"
    )
    title_cmd = f"{cmd} -e"
    st1, yt_title = getstatusoutput(title_cmd)
    if st1 != 0:
        logger.error(title_cmd)
        caption = f"Can't Download. Probably DRM.\n\nBy: {NAME}\n\nTitle: {title}\n\nTopic: {topic}\n\nError: {yt_title}\n\nLink: {link}"
        return 1, "", caption, ""
    if title == "":
        title = yt_title
    filename = title.replace("/", "|")

    cmd = f"{cmd} -o './downloads/{chat_id}/{filename}.%(ext)s' -f '{ytf}'"
    filename_cmd = f"{cmd} --get-filename"
    st1, path = getstatusoutput(filename_cmd)
    if st1 != 0:
        logger.error(filename_cmd)
        caption = f"Can't Download. Probably DRM.\n\nBy: {NAME}\n\nTitle: {title}\n\nTopic: {topic}\n\nError: {path}\n\nLink: {link}"
        return 1, "", caption, filename


    download_cmd = f"{cmd} --fragment-retries 25 --external-downloader aria2c --downloader-args 'aria2c: -x 16 -j 32'"
    st2, out2 = getstatusoutput(download_cmd)
    if st2 != 0:
        logger.error(download_cmd)
        caption = f"Can't download link.\n\nBy: {NAME}\n\nTitle: {title}\n\nTopic: {topic}\n\nError: {out2}\n\nLink: {link}"
        return 2, "", caption, filename
    else:
        filename += "." + path.split(".")[-1]
        caption = f"By: {NAME}\n\nTitle: {title}\n\nTopic: {topic}"
        return 0, path, caption, filename


async def download_videos(bot, message: Message, videos, thumbnail):
    if thumbnail.upper() not in ["V", "N"]:
        thumbnail = requests.get(thumbnail).content
        thumbnail = io.BytesIO(thumbnail)
        thumbnail.name = "thumb.jpg"
    err_list = []
    for index, video in videos:
        r, path, caption, filename = download_video(message.chat.id, video)
        caption += f"\n\nIndex: {index}"
        if r in [1, 2]:
            err_list.append(str(index))
            try:
                await message.reply(caption)
            except FloodWait as e:
                time.sleep(e.x+1)
                await message.reply(caption)
        elif r == 0:
            await send_video(bot, message, path, caption, filename, thumbnail)
            os.remove(path)

    if not isinstance(thumbnail, str):
        thumbnail.close()
    await message.reply("Done.")
    await message.reply(f"Errors: \n`{'|'.join(err_list)}`", parse_mode="markdown")


def get_videos(req_videos):
    videos = []
    for video in req_videos:
        video_parts = video.split("|")
        try:
            video_link, video_format, video_name, video_topic  = video_parts
        except:
            try:
                video_link, video_format, video_name = video_parts
            except:
                try:
                    video_link, video_format = video_parts
                except:
                    video_link = video_parts[0]
                    video_format = DEF_FORMAT
                finally:
                    video_topic = ""
                    video_name = ""
            finally:
                video_topic = ""
        if video_format == "":
            video_format = DEF_FORMAT
        videos.append((video_link, video_format, video_name, video_topic))
    return list(enumerate(videos, 1))


@bot.on_message(
    (
        (filters.command("download_link"))
        | filters.regex(f"^/download_link@{BOT}")
    )
    & (filters.chat(sudo_groups) | filters.user(sudo_users))
)
async def download_link(bot: Client, message: Message):
    user = message.from_user.id if message.from_user is not None else None
    download_ques = """\
    Send video link(s) in this format
    LINK1|format(Opt, Def=360)|Custom Name(Opt)|Topic(Opt),LINK2|ormat,...
    \n
    e.g. https://link1|360,http://link2,http://link3|480|My Video.mp4|Study
    \n
    One link per user at a time.
    """
    videos_ans = await bot.ask(message.chat.id, dedent(download_ques))
    videos_ans = videos_ans.text
    videos_ans: str
    req_videos = videos_ans.split(",")
    if user is not None and user not in sudo_users and len(req_videos) > 1:
        await message.reply("Not authorized for this action.", quote=True)
        return
    videos = get_videos(req_videos)
    n = len(videos)
    thumb_ques = "Send custom thumbnail url or N for default or V for video thumbnail."
    thumbnail = await bot.ask(message.chat.id, thumb_ques)
    thumbnail = thumbnail.text
    await message.reply(f"Downloading!!! {n} videos")
    await download_videos(bot, message, videos, thumbnail)


bot.run()
