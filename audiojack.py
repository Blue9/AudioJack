from __future__ import unicode_literals
import os
import re
import sys
from subprocess import Popen, PIPE
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
def set_useragent(name, version):
    '''Must do this before anything else!!!'''
    musicbrainzngs.set_useragent(name, version)

def get_results(url):
    '''Start here (after setting user agent).'''
    ydl = youtube_dl.YoutubeDL(opts) # object that downloads YouTube/SoundCloud/etc. video
    info = ydl.extract_info(url, download=False)
    if 'entries' in info: # If the URL is a playlist, only retrieve the first video (May change later).
        info = info['entries'][0]
    id = info['id']
    parsed = parse(info)
    print 'Getting song metadata - this may take a while...'
    return get_metadata(parsed)

def download(url, title=None, path=None):
    if not path:
        path = '%s/Downloads'% os.path.expanduser('~')
    if title:
        main = '%s/%s' % (path, title) # Does not matter what the extension is. FFMpeg will convert it to MP3 anyway.
    else:
        main = '%s/download' % path
    opts['outtmpl'] = '%s.temp' % main
    file = '%s.mp3' % main
    ydl = youtube_dl.YoutubeDL(opts)
    ydl.download([url])
    return file

def parse(info):
    parsed = {
        'url': info['webpage_url']
    }
    title = re.sub(r'\(| \([^)]*\)|\) ', '', info['title']) # Remove everything in between parentheses because they could interfere with the search (i.e. remove 'official music video' from the video title)
    title = re.sub(r'\[| \[[^\]]*\]|\] ', '', title) # Same as above but with brackets
    title = re.sub(r'\d*\s?(?i)kbps', '', title)
    banned_words = ['lyrics', 'hd', 'hq', 'free download', 'download', '720p', '1080p'] # Remove all words that could interfere with the search
    for word in banned_words:
        re.sub('(?i)%s' % word, '', title)
    if info['uploader'][-8:] == ' - Topic' and info['uploader'][:-8] != 'Various Artists':
        artist = info['uploader'][:-8]
        parsed['artist'] = artist
        parsed['title'] = title
    else:
        artist_title = re.split(' - | : |- |: ', title)[:2] # Most songs are uploaded as ARTIST - TITLE or something similar.
        parsed['title'] = artist_title[-1]
        if len(artist_title) == 2:
            parsed['artist'] = artist_title[0].split(' & ')[0] # Only get the first artist
        else:
            parsed['artist'] = ''
        fts = [' ft.', ' feat.', ' featuring', ' ft', ' feat']
        for ft in fts:
            if ft in parsed['artist'].lower():
                parsed['artist'] = parsed['artist'][:parsed['artist'].lower().find(ft)]
            if ft in parsed['title'].lower():
                parsed['title'] = parsed['title'][:parsed['title'].lower().find(ft)]
    return parsed

def get_metadata(parsed):
    temp = []
    results = []
    search_results = musicbrainzngs.search_recordings(recording=parsed['title'], artist=parsed['artist'], limit=50)
    for recording in search_results['recording-list']:
        if re.sub(r' |\.|\\|/|\|', '', parsed['title']).lower() in re.sub(r' |\.|\\|/|\|', '', recording['title']).lower() or re.sub(r' |\.|\\|/|\|', '', recording['title']).lower() in re.sub(r' |\.|\\|/|\|', '', parsed['title']).lower():
            if 'release-list' in recording:
                for release in recording['release-list']:
                    artist = recording['artist-credit'][0]['artist']['name']
                    title = recording['title']
                    album = release['title']
                    id = release['id']
                    entry = {
                        'artist': artist,
                        'title': title,
                        'album': album,
                    }
                    if entry not in temp and valid(recording, release, entry, id):
                        temp.append(entry.copy())
                        entry['id'] = id
                        entry['url'] = parsed['url']
                        results.append(entry)
    return results

def valid(recording, release, entry, id):
    '''Checks to make sure the result is not an instrumental, remix, compilation, etc. Also requires cover art for the song to be deemed valid.'''
    banned = ['instrumental', 'best of', 'diss', 'remix', '2015', '2016', '2k15', '2k16', 'what i call', 'ministry of sound']
    for word in banned:
        if word in entry['title'].lower() or word in entry['album'].lower():
            return False
    if 'secondary-type-list' in release['release-group']:
        secondary_type = release['release-group']['secondary-type-list'][0].lower()
        if secondary_type != 'soundtrack' and secondary_type != 'remix':
            return False
    if get_cover_art_as_data(id) == '':
        return False
    return True

def get_cover_art_as_data(id):
    '''Gets cover art as binary data if not already stored.'''
    try:
        return musicbrainzngs.get_image_front(id).encode('base64')
    except musicbrainzngs.musicbrainz.ResponseError:
        return ''

def select(entry):
    '''Select the metadata to be added to the MP3.'''
    if 'title' in entry and entry['title']: 
        file = download(entry['url'], title=entry['title'])
    else:
        file = download(entry['url'])
    tags = MP3(file)
    if 'artist' in entry and entry['artist']: 
        tags['TPE1'] = TPE1(encoding=3, text=entry['artist'])
    if 'title' in entry and entry['title']: 
        tags['TIT2'] = TIT2(encoding=3, text=entry['title'])
    if 'album' in entry and entry['album']: 
        tags['TALB'] = TALB(encoding=3, text=entry['album'])
    if 'id' in entry and entry['id']:    
        img = get_cover_art_as_data(entry['id']).decode('base64')
        tags['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, data=img)
    tags.save(v2_version=3)
    return file

def cut_file(file, start_time, end_time):
    ''' Cut the mp3 file with start and end time. '''
    output = '%s_cut.mp3' % file[:-4]
    try:
        os.remove(output)
    except Exception:
        pass
    if not start_time:
        if not end_time:
            return file
        else:
            p = Popen(['ffmpeg', '-i', file, '-c:a', 'copy', '-to', end_time, '-id3v2_version', '3', output], stdout=PIPE)
    elif not end_time:
        p = Popen(['ffmpeg', '-i', file, '-c:a', 'copy', '-ss', start_time, '-id3v2_version', '3', output], stdout=PIPE)
    else:
        p = Popen(['ffmpeg', '-i', file, '-c:a', 'copy', '-ss', start_time, '-to', end_time, '-id3v2_version', '3', output], stdout=PIPE)
    p.communicate()
    os.remove(file)
    os.rename(output, file)
    return file

if __name__ == '__main__':
    url = sys.argv[1]
    set_useragent('AudioJack', '1.0')
    results = get_results(url)
    download(url, results[0]['title'])
