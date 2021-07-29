# VideoDownloaderBot
Download videos from various websites using this telegram bot

### Local
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
Follow this to deploy using the heroku.yml https://devcenter.heroku.com/articles/build-docker-images-heroku-yml

Add all environment vars either from cli or heroku settings

## Docker



