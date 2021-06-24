import re
import os
from pyrogram.types.messages_and_media import message
from telegram_upload import files
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bs4 import BeautifulSoup

bot = Client("bot", config_file="config.ini")


@bot.on_message(filters.command("start"))
async def start(bot, message):
    await message.reply("Upload html file")


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


@bot.on_message(filters.document)
async def choose_format(bot, message):
    if message.document["mime_type"] == "text/html":
        file = (
            "./downloads/"
            + str(message.from_user.id)
            + "/"
            + message.document.file_id
            + ".html"
        )
        await message.download(file)

        with open(file, "r") as f:
            source = f.read()

        soup = BeautifulSoup(source, "html.parser")

        formats = ["144", "240", "360", "480", "720"]
        buttons = []
        for format in formats:
            buttons.append(
                InlineKeyboardButton(text=format + "p", callback_data=format)
            )
        buttons_markup = InlineKeyboardMarkup([buttons])

        paras = soup.find_all("p")
        title = paras[0].string
        await message.reply(title, quote=True, reply_markup=buttons_markup)
        os.remove(file)


@bot.on_callback_query()
async def upload(bot, query):
    message = query.message.reply_to_message
    await message.reply_chat_action("upload_video")
    format = query.data
    file = (
        "./downloads/"
        + str(message.from_user.id)
        + "/"
        + message.document.file_id
        + ".html"
    )
    await message.download(file)

    with open(file, "r") as f:
        source = f.read()

    soup = BeautifulSoup(source, "html.parser")

    vids = "".join(
        [
            str(tag)
            for tag in soup.find_all("p", style="text-align:center;font-size:25px;")
        ]
    )
    vids_soup = BeautifulSoup(vids, "html.parser")
    links = [link.extract().text for link in vids_soup.findAll("a")]
    name = re.compile("\d+\..*?(?=<br/>)")
    names = name.findall(vids)
    vids_dict = dict(zip(names, links))

    for vid in vids_dict:
        vid_name = vid + ".mp4"
        vid_path = "./downloads/" + str(message.from_user.id) + "/" + vid_name
        vid_link = vids_dict[vid]
        command = (
            "youtube-dl -o '"
            + vid_path
            + "' -f 'bestvideo[height="+format+"]+bestaudio' "
            + vid_link
        )
        os.system(command)
        await send_video(message, vid_path, vid)
        os.remove(vid_path)

    os.remove(file)

bot.run()
