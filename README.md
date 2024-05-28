# lyrics-downloader

A naive synced lyrics downloader using NetEase's API

## Install
```
git clone https://github.com/HamletDuFromage/lyrics-downloader
cd lyrics-downloader
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Usage
```
usage: lyrics-downloader.py [-h] -p PATH [-g BLACKLISTED_GENRES [BLACKLISTED_GENRES ...]] [-l LOG_LEVEL]
```
### Exemple:
```
./venv/bin/python lyrics-downloader.py -p ~/Music/ -g jazz fusion classical
```