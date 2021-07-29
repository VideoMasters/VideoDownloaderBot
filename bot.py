import re
import os
import asyncio
import logging
import time
from dotenv import load_dotenv
from pyrogram.errors import FloodWait
from functools import wraps
from subprocess import getstatusoutput
from pyrogram.types.messages_and_media import message
from telegram_upload import files
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bs4 import BeautifulSoup

load_dotenv()

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

with bot:
    BOT = bot.get_me().username.lower()

auth_users = list(eval(os.environ.get("AUTH_USERS")))
sudo_groups = list(eval(os.environ.get("GROUPS")))
sudo_html_groups = list(eval(os.environ.get("HTML_GROUPS")))
sudo_users = auth_users

thumb = os.environ.get("THUMB")
if thumb.startswith("http://") or thumb.startswith("https://"):
    getstatusoutput(f"wget '{thumb}' -o 'thumb.jpg'")
    thumb = "thumb.jpg"

logging.basicConfig(
    filename="bot.log",
    format="%(asctime)s:%(levelname)s %(message)s",
    filemode="w",
    level=logging.WARNING,
)

logger = logging.getLogger()


def exception(logger):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            try:
                return func(*args, **kwargs)
            except:
                issue = "Exception in " + func.__name__ + "\n"
                issue = (
                    issue
                    + "-------------------------\
                ------------------------------------------------\n"
                )
                logger.exception(issue)

        return wrapper

    return decorator


async def query_same_user_filter_func(_, __, query):
    message = query.message.reply_to_message
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
    await message.reply("Send video link or html")


async def send_video(message, path, caption, quote, filename):
    global thumb
    atr = files.get_file_attributes(path)
    duration = atr[0].duration
    width = atr[0].w
    height = atr[0].h
    if thumb == "":
        thumb = files.get_video_thumb(path)
    await message.reply_video(
        video=path,
        caption=caption,
        duration=duration,
        width=width,
        height=height,
        thumb=thumb,
        supports_streaming=True,
        quote=quote,
        # file_name=filename
    )


def parse_html(file, def_format):
    with open(file, "r") as f:
        source = f.read()

    soup = BeautifulSoup(source, "html.parser")

    info = soup.select_one("p#info")
    mg_info = soup.select_one("p[style='text-align:center;font-size:30;color:Blue']")
    buttons_soup = soup.select("button.collapsible")
    paras_soup = soup.select("p")[2:]
    if info is not None:
        all_videos_soup = soup.select_one("div#videos")
        topics_soup = all_videos_soup.select("div.topic")
        videos = []
        for topic_soup in topics_soup:
            topic_name = topic_soup.select_one("span.topic_name").get_text(strip=True)
            videos_soup = topic_soup.select("p.video")
            for video_soup in videos_soup:
                video_name = video_soup.select_one("span.video_name").get_text(
                    strip=True
                )
                video_link = video_soup.select_one("a").get_text(strip=True)
                if not (
                    video_link.startswith("http://")
                    or video_link.startswith("https://")
                ):
                    continue
                videos.append((video_link, def_format, video_name, topic_name, False))
    elif mg_info is not None and len(buttons_soup) != 0:
        videos = []
        for button_soup in buttons_soup:
            topic_name = button_soup.get_text(strip=True).strip("Topic :- ")
            para = button_soup.find_next_sibling("div", class_="content").p
            # ps = [para.contents[i] for i in range(0,len(para)) if i%5==0 ]
            for a_soup in para.select("a"):
                br = a_soup.find_previous_sibling()
                br.decompose()
                video_name = a_soup.previousSibling
                video_link = a_soup.get_text(strip=True)
                if not (
                    video_link.startswith("http://")
                    or video_link.startswith("https://")
                ):
                    continue
                videos.append((video_link, def_format, video_name, topic_name, False))
    elif mg_info is not None and paras_soup[0].b is not None:
        videos = []
        for topic_para in paras_soup:
            if paras_soup.index(topic_para) % 2 == 0:
                topic_name = topic_para.get_text(strip=True).strip("Topic :- ")
                para = topic_para.find_next_sibling("p")
                for a_soup in para.select("a"):
                    br = a_soup.find_previous_sibling()
                    br.decompose()
                    video_name = a_soup.previousSibling
                    video_link = a_soup.get_text(strip=True)
                    if not (
                        video_link.startswith("http://")
                        or video_link.startswith("https://")
                    ):
                        continue
                    videos.append(
                        (video_link, def_format, video_name, topic_name, False)
                    )
            else:
                continue
    elif (
        mg_info is not None
        and paras_soup[0].get("style") == "text-align:center;font-size:25px;"
    ):
        topic_name = ""
        videos = []
        for para in paras_soup:
            video_name = para.contents[0]
            video_link = para.select_one("a").get_text(strip=True)
            if not (
                video_link.startswith("http://")
                or video_link.startswith("https://")
            ):
                continue
            videos.append((video_link, def_format, video_name, topic_name, False))
    else:
        videos = []
        topic_name = ""
        video_name = ""
        for a_soup in soup.select("a"):
            video_link = a_soup.get("href")
            if not (
                video_link.startswith("http://")
                or video_link.startswith("https://")
            ):
                continue
            videos.append((video_link, def_format, video_name, topic_name, False))

    return videos


@bot.on_callback_query(query_document & query_same_user)
async def choose_html_video_format(bot, query):
    msg = query.message.reply_to_message
    msg = await bot.get_messages(msg.chat.id, msg.message_id)
    only = False
    if msg.document is not None:
        commands = msg.caption.split()
    else:
        commands = msg.text.split()
    if len(commands) == 1:
        start_index = 1
    elif len(commands) == 2:
        if commands[1].isnumeric():
            start_index = int(commands[1])
        else:
            return
    elif len(commands) == 3 and commands[2] == "o":
        if commands[1].isnumeric():
            start_index = int(commands[1])
            only = True
        else:
            return
    else:
        return

    if msg.reply_to_message is not None:
        if msg.reply_to_message.document is not None:
            message = msg.reply_to_message
        else:
            return
    else:
        message = msg
    def_format = query.data
    if message.document["mime_type"] != "text/html":
        return
    file = f"./downloads/{message.chat.id}/{message.document.file_unique_id}.html"
    await message.download(file)

    videos = parse_html(file, def_format)
    if only:
        videos = [videos[start_index - 1]]
    else:
        videos = videos[start_index - 1 :]
    n = len(videos)
    await msg.reply(f"Downloading!!! {n} videos")
    await download_videos(msg, videos, start_index)


@bot.on_message(
    (
        (filters.command("download_html") & ~filters.group)
        | filters.regex(f"^/download_html@{BOT}")
    )
    & (filters.chat(sudo_html_groups) | filters.user(sudo_users))
    & (filters.document | filters.reply)
)
async def download_html(bot, msg):
    if msg.reply_to_message is not None:
        if msg.reply_to_message.document is not None:
            message = msg.reply_to_message
        else:
            return
    else:
        message = msg
    if message.document["mime_type"] != "text/html":
        return
    file = f"./downloads/{message.chat.id}/{message.document.file_unique_id}.html"
    await message.download(file)

    with open(file, "r") as f:
        source = f.read()

    soup = BeautifulSoup(source, "html.parser")

    info = soup.select_one("p#info")
    mg_info = soup.select_one("p[style='text-align:center;font-size:30;color:Blue']")
    if info is not None:
        title = soup.select_one("h1#batch").get_text(strip=True)
    elif mg_info is not None:
        title = soup.select_one("p").get_text(strip=True)
    else:
        title = message.document.file_name

    formats = ["144", "240", "360", "480", "720"]
    buttons = []
    for format in formats:
        buttons.append(InlineKeyboardButton(text=format + "p", callback_data=format))
    buttons_markup = InlineKeyboardMarkup([buttons])

    await msg.reply(title, quote=True, reply_markup=buttons_markup)
    os.remove(file)


@bot.on_message(
    (
        (filters.command("download_html") & ~filters.group)
        | filters.regex(f"^/download_html@{BOT}")
    )
    & (filters.chat(sudo_html_groups) | filters.user(sudo_users))
)
async def download_html_info(bot, message):
    await message.reply(
        "Send html with command as caption or reply.\n"
        + "Specify start index separated by space and o if only that index\n"
        + "e.g. /download_html\n"
        + "e.g. /download_html 5\n"
        + "e.g. /download_html 5 o\n"
    )


def download_video(message, video):
    chat = message.chat.id
    link = video[0]
    vid_format = video[1]
    title = video[2]
    topic = video[3]
    quote = video[4]

    if not vid_format.isnumeric():
        title = vid_format

    if "youtu" in link:
        if vid_format in ["144", "240", "480"]:
            ytf = f"'bestvideo[height<={vid_format}][ext=mp4]+bestaudio[ext=m4a]'"
        elif vid_format == "360":
            ytf = 18
        elif vid_format == "720":
            ytf = 22
        else:
            ytf = 18
    elif ("deshdeepak" in link and len(link.split("/")[-1]) == 13) or (
        "magnetoscript" in link
        and ("brightcove" in link or len(link.split("/")[-1]) == 13)
    ):
        if vid_format not in ["144", "240", "360", "480", "720"]:
            vid_format = "360"
        ytf = f"'bestvideo[height<={vid_format}]+bestaudio'"
    elif (
        ("deshdeepak" in link and len(link.split("/")[-1]) == 8)
        or ("magnetoscript" in link and "jwp" in link)
        or "jwplayer" in link
    ):
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
        ytf = f"'best[height<={vid_format}]'"
        if ".mp4" in link:
            ytf = "'best'"
        elif ".m3u8" in link:
            ytf = "'best'"
    else:
        ytf = "'best'"

    cmd = (
        f"yt-dlp -o './downloads/{chat}/%(id)s.%(ext)s' -f {ytf} --no-warning '{link}'"
    )
    filename = (
        title.replace("/", "|")
        .replace("+", "_")
        .replace("?", ":Q:")
        .replace("*", ":S:")
        .replace("#", ":H:")
    )
    filename_cmd = f"{cmd} -e --get-filename -R 25"
    st1, out1 = getstatusoutput(filename_cmd)
    if st1 != 0:
        caption = f"Can't Download. Probably DRM.\n\nLink: {link}\n\nTitle: {title}\n\nTopic: {topic}\n\nError: {out1}"
        return 1, "", caption, quote, filename
    yt_title, path = out1.split("\n")
    if title == "":
        title = yt_title

    download_cmd = f"{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args 'aria2c: -x 16 -j 32'"
    st2, out2 = getstatusoutput(download_cmd)
    if st2 != 0:
        caption = f"Can't download link.\n\nLink: {link}\n\nTitle: {title}\n\nTopic: {topic}\n\nError: {out2}"
        return 2, "", caption, quote, filename
    else:
        filename += "." + path.split(".")[-1]
        caption = f"Link: {link}\n\nTitle: {title}\n\nTopic: {topic}"
        return 0, path, caption, quote, filename


@exception(logger)
async def download_videos(message, videos, index=1):
    for video in videos:
        r, path, caption, quote, filename = download_video(message, video)
        caption += f"\n\nIndex: {index}"
        if r in [1, 2]:
            try:
                await message.reply(caption, quote=quote)
            except FloodWait as e:
                time.sleep(e.x)
        elif r == 0:
            await send_video(message, path, caption, quote, filename)
            os.remove(path)
        index += 1

    await message.reply("Done.")


def get_videos(req_videos, def_format):
    videos = []
    for video in req_videos:
        video_parts = video.split("|")
        video_link = video_parts[0]
        video_format = (
            video_parts[1]
            if len(video_parts) == 2 and video_parts[1] != ""
            else def_format
        )
        videos.append((video_link, video_format, "", "", True))

    return videos


@bot.on_callback_query(~query_document & query_same_user)
async def choose_video_format(bot, query):
    message = query.message.reply_to_message
    def_format = query.data
    commands = message.text.split()
    req_videos = commands[1:-1]
    videos = get_videos(req_videos, def_format)
    n = len(videos)
    await message.reply(f"Downloading!!! {n} videos")
    await download_videos(message, videos)


@bot.on_message(
    (
        (filters.command("download_link") & ~filters.group)
        | filters.regex(f"^/download_link@{BOT}")
    )
    & (filters.chat(sudo_groups) | filters.user(sudo_users))
)
async def download_link(bot, message):
    user = message.from_user.id
    commands = message.text.split()
    if len(commands) == 1:
        await message.reply(
            "Send video link(s) separated by space, and format separated by | or f at end to choose format (optional) \n\n"
            + "e.g. /downloadLink https://link1|360 http://link2 http://link3|480 \n"
            + "e.g. /downloadLink http://link1 http://link2 f\n\n"
            + "Default format 360p if unspecified.\n"
            + "One link per user at a time."
        )
        return
    if commands[-1] == "f":
        if user not in sudo_users and len(commands) > 3:
            await message.reply("Not authorized for this action.", quote=True)
            return
        formats = ["144", "240", "360", "480", "720"]
        buttons = []
        for def_format in formats:
            buttons.append(
                InlineKeyboardButton(text=def_format + "p", callback_data=def_format)
            )
        buttons_markup = InlineKeyboardMarkup([buttons])
        await message.reply("Choose Format", quote=True, reply_markup=buttons_markup)
    else:
        if user not in sudo_users and len(commands) > 2:
            await message.reply("Not authorized for this action.", quote=True)
            return
        def_format = "360"
        req_videos = commands[1:]
        videos = get_videos(req_videos, def_format)
        n = len(videos)
        await message.reply(f"Downloading!!! {n} videos")
        await download_videos(message, videos)


bot.run()
