# Phice
A lightweight privacy-friendly alternative front-end for Facebook.

Inspired by [Nitter](https://github.com/zedeus/nitter), [Invidious](https://github.com/iv-org/invidious) and others

# Screenshot
![screenshot](screenshot.png)

# Features
* No ADS
* No trackers
* No JavaScript required
* No account required
* Lightweight
* Free and open-source
* RSS feeds

# Installation
## Docker
Docker image avaliable at: https://hub.docker.com/r/c4ffe14e/phice

or build your image with
```sh
docker buildx build -t phice:latest .
```

Create a config file
```sh
cp config.example.json config.json
```

Run it with docker
```sh
docker run --rm -v "./config.json:/src/phice/config.json:ro" -p "5000:5000" -d phice:latest
```

or with compose
```sh
docker-compose up -d
```

## Manual
### Dependencies:
* python >= 3.13
* uv
* a WSGI server (ex: gunicorn)

```sh
uv sync
cp config.example.json config.json
```

And start your server
```sh
uv run gunicorn -b 0.0.0.0:8000 -w 4 "app:app"
```

# Mirrors
[Codeberg](https://codeberg.org/c4ffe14e/phice)

[GitHub](https://github.com/c4ffe14e/phice)
