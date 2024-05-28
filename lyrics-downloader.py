#!/usr/bin/env python3

import requests
import argparse
import logging
import urllib.parse
from tinytag import TinyTag
from tinytag import TinyTagException
import re
import os
from colorlog import ColoredFormatter

LOG_LEVEL = logging.DEBUG
LOGFORMAT = "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
log = logging.getLogger('pythonConfig')
log.setLevel(LOG_LEVEL)
log.addHandler(stream)

class Downloader:
    def __init__(self, blacklisted_genres = []) -> None:
        search_limit = 3 #Lower means higher confidence and lower waiting time for instrumental songs
        self.search_url = f"https://music.xianqiao.wang/neteaseapiv2/search?limit={search_limit}&type=1&keywords="
        self.lyrics_url = "https://music.xianqiao.wang/neteaseapiv2/lyric?id="
        self.timestamp_pattern = re.compile("\[\d\d:\d\d(?:.\d+)?\]")
        self.filename_pattern = re.compile("(.+)(?=\.\w+$)")
        self.blacklisted_genres = blacklisted_genres

    def search_song(self, keywords):
        url = urllib.parse.quote(f"{self.search_url}{keywords}", safe=":/?=&")
        log.debug(f"search request: {url}")
        song_request = requests.get(url = url)
        try:
            return song_request.json()["result"]["songs"]
        except KeyError:
            log.warning(f"Couldn't find songs for keywords: {keywords}")
            return {}

    def fetch_synced_lyrics(self, song_id):
        log.debug(f"song id: {song_id}")
        lyrics_request = requests.get(url = f"{self.lyrics_url}{song_id}")
        lyrics = lyrics_request.json()["lrc"]["lyric"]
        return self.verify_lyrics(lyrics)

    def write_lrc_file(self, lyrics, stem):
        filename = stem + ".lrc"
        with open(filename, 'w') as lrc_file:
            lrc_file.write(lyrics)
        log.info(f"🤙🤙🤙 {filename} has been written to disk 🤙🤙🤙")

    def verify_lyrics(self, lyrics):
        if self.timestamp_pattern.match(lyrics):
            if len(lyrics.split('\n')) > 3:
                lyrics = re.sub(r'($\[\d{2}:\d{2}\.\d{2})\d(\])', r'\1\2', lyrics)
                lyrics = lyrics.replace("作词", "Songwriter").replace("作曲", "Composer")
                return lyrics
        return None

    def run(self, filename):
        try:
            tags = TinyTag.get(filename)
        except TinyTagException:
            log.info(f"{filename} is not a song")
            return False
        title = tags.title
        for genre in self.blacklisted_genres:
            try:
                if genre.lower() in tags.genre.lower():
                    log.info(f"song {title} was skipped because it was of the genre: {tags.genre}")
                    return False
            except AttributeError:
                pass
        stem = self.filename_pattern.search(filename).group(1)
        if os.path.exists(stem + ".lrc"):
            log.info(f"{title} already has an associated lyrics file")
            return False
        log.info(f"Fetching lyrics for {title}")
        for song in self.search_song(f"{title} {tags.artist}"):
            lyrics = self.fetch_synced_lyrics(song["id"])
            if lyrics is not None:
                self.write_lrc_file(lyrics, stem)
                return True
        log.error(f"Couldn't find lyrics for {title}")
        return False

class Crawler:
    def __init__(self, path, blacklisted_genres) -> None:
        self.success_count = 0
        self.downloader = Downloader(blacklisted_genres)
        if os.path.isdir(path):
            self.recursive_download(path)
        elif os.path.isfile(path):
            self.download_lyrics(path)
        else:
            log.critical(f"path: {path} is not supported.")

    def recursive_download(self, path):
        for root, dirs, files in os.walk(path):
            for name in files:
                self.download_lyrics(os.path.join(root, name))
            for name in dirs:
                self.recursive_download(os.path.join(root, name))

    def download_lyrics(self, lyrics):
        if self.downloader.run(lyrics):
            self.success_count += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Download synced lyrics from NetEase Cloud Music")
    required = parser.add_argument_group('Required arguments')
    required.add_argument('-p', '--path', help='directory or filepath', required=True)
    optional = parser.add_argument_group('Optional arguments')
    optional.add_argument('-g', '--blacklisted_genres', nargs='+', help='blacklisted genres', required=False, default=[])
    args = parser.parse_args()

    cr = Crawler(args.path, args.blacklisted_genres)
    print(f"🎷🎷🎷 Successfully downloaded {cr.success_count} .lrc files! 🎷🎷🎷")