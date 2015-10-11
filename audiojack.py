from __future__ import unicode_literals
import os
import re

import youtube_dl
import musicbrainzngs

from mutagen.id3 import TPE1, TIT2, TALB, APIC
from mutagen.mp3 import MP3

opts = {
    'format': 'bestaudio',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '256'
    }],
}
cover_art_dict = {} 
url = '' 
artist_title = [] 
results = [] 
ydl = youtube_dl.YoutubeDL(opts) 
id = '' 
title = '' 

def set_useragent(name, version):
    musicbrainzngs.set_useragent(name, version)

def get_results(u):
    global url
    global results
    global id
    url = u
    url_info = ydl.extract_info(url, download=False)
    if 'entries' in url_info: 
        url_info = url_info['entries'][0]
    id = url_info['id']
    artist_title = get_artist_title(url_info)
    results = get_metadata(artist_title)
    return results

def download(url, id):
    global opts
    global title
    if title != '':
        file = '%s.temp' % title 
        opts['outtmpl'] = file
    ydl = youtube_dl.YoutubeDL(opts)
    ydl.download([url])
    return file

def get_artist_title(url_info):
    if url_info['uploader'][0] == '#':
        artist_title = [url_info['uploader'], url_info['title']]
    else:
        title = re.sub(r'\(| \([^)]*\)|\) ', '', url_info['title']) 
        title = re.sub(r'\[| \[[^\]]*\]|\] ', '', title) 
        banned_words = ['lyrics', 'hd', 'hq', '320kbps', 'free download', 'download', '1080p', '720p'] 
        for word in banned_words:
            while word in title.lower():
                title = title.replace(word, '')
        artist_title = re.split(' - | : |- |: ', title)[:2] 
        if len(artist_title) == 1:
            return ['', artist_title[0]]
        artist_title[0] = artist_title[0].split(' & ')[0]
        fts = [' ft.', ' feat.', ' featuring', ' ft', ' feat']
        for ft in fts:
            artist_title[1] = artist_title[1].split(ft)[0]
    return artist_title

def get_metadata(artist_title):
    temp_results = []
    results = []
    search_results = musicbrainzngs.search_recordings(recording=artist_title[1], artist=artist_title[0], limit=50)
    for recording in search_results['recording-list']:
        if artist_title[0] in recording['artist-credit'][0]['artist']['name'] or recording['artist-credit'][0]['artist']['name'] in artist_title[0]:
            if 'release-list' in recording:
                for release in recording['release-list']:
                    artist = recording['artist-credit'][0]['artist']['name']
                    title = recording['title']
                    album = release['title']
                    id = release['id']
                    entry = [artist, title, album, id]
                    if entry[:3] not in temp_results and valid(recording, release, entry):
                        temp_results.append(entry[:3])
                        results.append(entry)
    return results

def valid(recording, release, entry):
    banned = ['instrumental', 'best of', 'diss', 'remix', '2015', '2016', '2k15', '2k16', 'what i call']
    for word in banned:
        if word in entry[1].lower() or word in entry[2].lower():
            return False
    if 'secondary-type-list' in release['release-group']:
        type = release['release-group']['secondary-type-list'][0].lower()
        if type != 'soundtrack' and type != 'remix':
            return False
    if get_cover_art_as_data(entry[3]) == '':
        return False
    return True

def get_cover_art_as_data(id):
    global cover_art_dict
    if id in cover_art_dict:
        return cover_art_dict[id]
    try:
        cover_art_dict[id] = musicbrainzngs.get_image_front(id).encode('base64')
    except musicbrainzngs.musicbrainz.ResponseError:
        cover_art_dict[id] = ''
    return cover_art_dict[id]

def select(index):
    global title
    selection = results[index]
    title = selection[1]
    file = '%s.mp3' % title
    download(url, id)
    img = get_cover_art_as_data(selection[3]).decode('base64')
    tags = MP3(file)
    tags['TPE1'] = TPE1(encoding=3, text=selection[0])
    tags['TIT2'] = TIT2(encoding=3, text=selection[1])
    tags['TALB'] = TALB(encoding=3, text=selection[2])
    tags['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, data=img)
    tags.save()
    return file