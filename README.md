# VideoDownloaderBot
Download videos from various websites using this telegram bot

### Docker (Easiest)
- Make sure docker is installed and running
```sh
    # Create ~/vdb.env file with appropriate values.
    docker run -d --restart=always --env-file ~/vdb.env deshdeepak1/video_downloader_bot:latest
```
- Try on https://labs.play-with-docker.com/

#### Manually
- Make sure docker is installed and running
```sh
    git clone https://github.com/DaruaraFriends/VideoDownloaderBot
    cd VideoDownloaderBot
    docker build -t vdb .
    cp sample.env .env
    # Change values in .env
    docker run -d --restart=always --env-file .env vdb
```

### Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DaruaraFriends/VideoDownloaderBot/blob/main/VideoDownloaderBot.ipynb)

### Heroku

#### Easy Way
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/DaruaraFriends/VideoDownloaderBot)

#### Docker
- Make sure heroku-cli is installed  `npm i -g heroku`
```sh
    heroku login
    git clone https://github.com/DaruaraFriends/VideoDownloaderBot
    cd VideoDownloaderBot
    heroku create
    heroku stack:set container
    git push heroku main
```
- Help: https://devcenter.heroku.com/articles/build-docker-images-heroku-yml

- Add all environment vars either from cli or heroku settings
    ```sh
        heroku config:set ENV1=abc ENV2=123
    ```

### Python
- Make sure python3, ffmpeg, aria2 are installed
```sh
    git clone https://github.com/DaruaraFriends/VideoDownloaderBot
    cd VideoDownloaderBot
    cp sample.env .env
    # Change values in .env
    python3 -m venv venv
    . ./venv/bin/activate
    pip install -r ./requirements.txt
    python3 bot.py
```

### .env
```sh
    API_ID=12345 # Get from https://my.telegram.org/apps
    API_HASH=abcdef # Get from https://my.telegram.org/apps
    BOT_TOKEN=123:abc # Get from https://t.me/BotFather
    AUTH_USERS=123,456 # User ids of those who can use bot anywhere without limit
    GROUPS=123,456 # Chat ids where you wan't many to use the bot
    HTML_GROUPS=123,456 # Chat ids where you wan't many to use the bot to download from htmls
    THUMB=thumb.jpg # Url of video thumbnail. Leave to use video's thumbnail
    NAME=Deshdeepak # Name to send with video
```

### Instructions
- /download_link - To download from links
- /download_html - To download from htmls
- /download_link@bot_username & /download_html@bot_username - To use in groups

