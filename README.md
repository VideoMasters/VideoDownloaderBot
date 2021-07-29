# VideoDownloaderBot
Download videos from various websites using this telegram bot

### Local
- Make sure python3 ffmpeg aria2 are installed
```sh
    git clone https://github.com/DaruaraFriends/VideoDownloaderBot
    cp sample.env .env
    # Change values in .env
    python3 -m venv venv
    . ./venv/bin/activate
    pip install -r ./requirements.txt
    python3 bot.py
```

### Heroku

####  Python
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Add ffmpeg buildpack https://elements.heroku.com/buildpacks/jonathanong/heroku-buildpack-ffmpeg-latest

Add aria2 buildpack https://elements.heroku.com/buildpacks/amivin/aria2-heroku

#### Docker
- Make sure heroku-cli is installed
```sh
    heroku login
    git clone https://github.com/DaruaraFriends/VideoDownloaderBot
    heroku stack:set container
    git push heroku main
```
Help: https://devcenter.heroku.com/articles/build-docker-images-heroku-yml

Add all environment vars either from cli or heroku settings

## Docker (Easiest)
- Make sure docker is installed and running
```sh
    # Create ~/vdb.env file with appropriate values.
    docker run -d --restart=always --env-file ~/vdb.env deshdeepak1/video_downloader_bot:latest
```

#### Manually
- Make sure docker is installed and running
```sh
    git clone https://github.com/DaruaraFriends/VideoDownloaderBot
    docker build -t vdb .
    cp sample.env .env
    # Change values in .env
    docker run -d --restart=always --env-file .env vdb
```






