from pyrogram import Client
from pyrogram import filters
from bs4 import BeautifulSoup
import re
import os

bot = Client('bot', config_file='config.ini')


@bot.on_message(filters.command('start'))
async def start(bot, message):
    await message.reply("Upload html file")


@bot.on_message(filters.document)
async def upload(bot, message):
    if message.document["mime_type"] == "text/html":
        file = message.document.file_id+'.html'
        await message.download(file)

        with open('./downloads/'+file,'r') as f:
            source = f.read()

        soup = BeautifulSoup(source,'html.parser')

        paras = soup.find_all("p")

        title = paras[0].string

        vids = ''.join([ str(tag) for tag in soup.find_all("p", style="text-align:center;font-size:25px;") ])
        vids_soup = BeautifulSoup(vids, 'html.parser')
        links = [link.extract().text for link in vids_soup.findAll('a')]
        name = re.compile('\d+\..*?(?=<br/>)')
        names = name.findall(vids)

        vids_dict = dict(zip(names, links))
        await message.reply(title)
        for vid in vids_dict:
            video = 'Name: ' + vid + '\n' + 'Link: ' + vids_dict[vid]
            vid_name = vid+".mp4"
            vid_path = "./downloads/"+vid_name
            vid_link = vids_dict[vid]
            command = "youtube-dl -o '" + vid_path + "' -f 'bestvideo[height=360]+bestaudio' " + vid_link
            print(command)
            os.system(command)
            await message.reply(video)

bot.run()
