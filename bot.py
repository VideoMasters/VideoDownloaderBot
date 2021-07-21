import re
import os
import asyncio
from config import Config
from pyrogram.types.messages_and_media import message
from telegram_upload import files
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bs4 import BeautifulSoup

API_ID = int(os.environ.get("API_ID", Config.API_ID))
API_HASH = os.environ.get("API_HASH", Config.API_HASH)
BOT_TOKEN = os.environ.get("BOT_TOKEN", Config.BOT_TOKEN)

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@bot.on_message(filters.command("start"))
async def start(bot, message):
    await message.reply("Send video link or html")


async def send_video(message, path, caption):
    atr = files.get_file_attributes(path)
    duration = atr[0].duration
    width = atr[0].w
    height = atr[0].h
    thumb = "thumb.png"
    await message.reply_video(
        video=path,
        caption=caption,
        duration=duration,
        width=width,
        height=height,
        thumb=thumb,
        supports_streaming=True,
    )


# @bot.on_message(filters.document)
# async def choose_format(bot, message):
    # if message.document["mime_type"] == "text/html":
        # file = (
            # "./downloads/"
            # + str(message.from_user.id)
            # + "/"
            # + message.document.file_id
            # + ".html"
        # )
        # await message.download(file)

        # with open(file, "r") as f:
            # source = f.read()

        # soup = BeautifulSoup(source, "html.parser")

        # formats = ["144", "240", "360", "480", "720"]
        # buttons = []
        # for format in formats:
            # buttons.append(
                # InlineKeyboardButton(text=format + "p", callback_data=format)
            # )
        # buttons_markup = InlineKeyboardMarkup([buttons])

        # paras = soup.find_all("p")
        # title = paras[0].string
        # await message.reply(title, quote=True, reply_markup=buttons_markup)
        # os.remove(file)


# @bot.on_callback_query()
# async def upload(bot, query):
    # message = query.message.reply_to_message
    # format = query.data
    # file = (
        # "./downloads/"
        # + str(message.from_user.id)
        # + "/"
        # + message.document.file_id
        # + ".html"
    # )
    # await message.download(file)

    # with open(file, "r") as f:
        # source = f.read()

    # soup = BeautifulSoup(source, "html.parser")

    # vids = "".join(
        # [
            # str(tag)
            # for tag in soup.find_all("p", style="text-align:center;font-size:25px;")
        # ]
    # )
    # vids_soup = BeautifulSoup(vids, "html.parser")
    # links = [link.extract().text for link in vids_soup.findAll("a")]
    # name = re.compile("\d+\..*?(?=<br/>)")
    # names = name.findall(vids)
    # vids_dict = dict(zip(names, links))

    # for vid in vids_dict:
        # vid_name = vid + ".mp4"
        # vid_path = "./downloads/" + str(message.from_user.id) + "/" + vid_name
        # vid_link = vids_dict[vid]
        # command = (
            # "youtube-dl -o '"
            # + vid_path
            # + "' -f 'bestvideo[height="+format+"]+bestaudio' "
            # + vid_link
        # )
        # os.system(command)
        # await message.reply_chat_action("upload_video")
        # await send_video(message, vid_path, vid)
        # os.remove(vid_path)

    # os.remove(file)

async def download_video(video):
    await asyncio.sleep(0)
    print(video)
    print(video[0][-1])


async def download_videos(videos):
    await asyncio.gather(*(download_video(video) for video in videos))
    return


@bot.on_callback_query()
async def choose_format(bot, query):
    message = query.message.reply_to_message
    def_format = query.data
    command = message.text.split()
    req_videos = command[1:-1]
    videos = []
    for video in req_videos:
        video_parts = video.split('|')
        video_link = video_parts[0]
        video_format = video_parts[1] if len(video_parts) == 2 and video_parts[1] != '' else def_format
        videos.append((video_link, video_format, '', ''))

    await message.reply('Downloading!!!')
    await download_videos(videos)


@bot.on_message(filters.command("downloadLink"))
async def download_link(bot, message):
    if len(message.command) == 1:
        await message.reply(
                "Send video link(s) separated by space, and format separated by | or f at end to choose format (optional) \n\n"
                + "e.g. /downloadLink https://link1|360 http://link2 http://link3|480 \n\n"
                + "e.g. /downloadLink http://link1 http://link2 f"
                )
        return
    if message.command[-1] == 'f':
        formats = ["144", "240", "360", "480", "720"]
        buttons = []
        for def_format in formats:
            buttons.append(
                InlineKeyboardButton(text=def_format + "p", callback_data=def_format)
            )
        buttons_markup = InlineKeyboardMarkup([buttons])
        await message.reply("Choose Format", quote=True, reply_markup=buttons_markup)
    else:
        req_videos = message.command[1:]
        def_format = "360"
        videos = []
        for video in req_videos:
            video_parts = video.split('|')
            video_link = video_parts[0]
            video_format = video_parts[1] if len(video_parts) == 2 and video_parts[1] != '' else def_format
            videos.append((video_link, video_format, '', ''))

        await message.reply('Downloading!!!')
        await download_videos(videos)


bot.run()
