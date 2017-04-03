#!/usr/bin/env python
from __future__ import unicode_literals
import imghdr
import os
import re
import socket
import subprocess
import sys
import urllib2
from urlparse import urlparse

import musicbrainzngs
import youtube_dl
from mutagen.id3 import ID3, TPE1, TIT2, TALB, APIC

musicbrainzngs.set_useragent(socket.gethostname(), '1.1.1')


class AudioJack(object):
    def __init__(self, bitrate=256, small_cover_art=False):
        self.ydl = youtube_dl.YoutubeDL({
            'format': 'bestaudio',
            'outtmpl': '%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': str(bitrate)
            }]
        })
        self.small_cover_art = small_cover_art
        self._cover_art_cache = {}

    def get_results(self, url):
        info = self.ydl.extract_info(url, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return self._get_metadata(self._parse(info))

    def select(self, entry, path=None):
        if 'url' not in entry:
            raise ValueError('Media URL must be specified.')
        info = self.ydl.extract_info(entry['url'])
        file = '%s.mp3' % info['id']
        tags = ID3()
        filename = entry['title'] if 'title' in entry and entry['title'] else 'download'
        filename = re.sub(r'\W*[^a-zA-Z\d\s]\W*', '_', filename)
        if 'title' in entry:
            tags.add(TIT2(encoding=3, text=entry['title']))
        if 'artist' in entry:
            tags.add(TPE1(encoding=3, text=entry['artist']))
        if 'album' in entry:
            tags.add(TALB(encoding=3, text=entry['album']))
        if 'img' in entry and entry['img'] != '':
            scheme = urlparse(entry['img']).scheme
            img_path = entry['img']
            if scheme == '':
                # Local path to absolute path
                img_path = os.path.abspath(img_path)
            if scheme[:4] != 'http':
                # Absolute path to file URI
                img_path = 'file:///%s' % img_path
            img_request = urllib2.urlopen(img_path)
            img = img_request.read()
            img_request.close()
            valid_exts = ['jpeg', 'png', 'gif', 'bmp']
            ext = imghdr.what(None, img)
            if ext not in valid_exts:
                raise ValueError('%s is an unsupported file extension.' % ext)
            else:
                mime = 'image/%s' % ext
                tags.add(APIC(encoding=3, mime=mime, type=3, data=img))
        tags.save(file, v2_version=3)
        if path:
            filename = '%s/%s' % (path, filename)
            if not os.path.exists(path):
                os.makedirs(path)
        target_file = '%s.mp3' % filename
        i = 1
        while os.path.exists(target_file):
            target_file = '%s (%d).mp3' % (filename, i)
            i += 1
        os.rename(file, target_file)
        return os.path.realpath(target_file)

    def cut_file(self, file, start_time=0, end_time=None):
        # TODO: Fix loss of cover art
        output = '%s_cut.mp3' % file
        if end_time:
            subprocess.Popen(
                ['ffmpeg', '-i', file, '-ss', str(start_time), '-to', str(end_time), '-c:a', 'copy', '-id3v2_version',
                 '3', output]).communicate()
        else:
            subprocess.Popen(
                ['ffmpeg', '-i', file, '-ss', str(start_time), '-c:a', 'copy', '-id3v2_version', '3',
                 output]).communicate()
        os.remove(file)
        os.rename(output, file)
        return file

    def _parse(self, info):
        parsed = {
            'url': info['webpage_url']
        }

        banned_words = ['lyrics', 'hd', 'hq', 'free download', 'download', '1080p', 'official music video', 'm/v']
        feats = ['featuring', 'feat.', 'ft.', 'feat', 'ft']
        artist_delimiters = [',', 'x', '&', 'and']

        video_title = info['title']
        video_title = re.sub(r'\([^)]*|\)|\[[^]]*|\]', '', video_title).strip()  # Remove parentheses and brackets
        video_title = re.sub(self._gen_regex(banned_words), ' ', video_title).strip()  # Remove banned words
        parsed_title = re.split(r'\W*[\-:] \W*', video_title)  # 'Artist - Title' => ['Artist', 'Title']

        title = self._split(parsed_title[-1], feats)  # 'Song feat. Some Guy' => ['Song', 'Some Guy']
        parsed['title'] = title[0]
        secondary_artist_list = title[1:]

        if info['uploader'][-8:] == ' - Topic' and info['uploader'][:-8] != 'Various Artists':
            parsed['artists'] = [info['uploader'][:-8]]

        elif len(parsed_title) > 1:
            artists = self._split(parsed_title[-2], feats)  # 'A1 and A2 feat. B1' => ['A1 and A2', 'B1']
            parsed['artists'] = self._split(artists[0], artist_delimiters)  # 'A1 and A2' => ['A1', 'A2']
            secondary_artist_list.extend(artists[1:])

        if len(secondary_artist_list) > 0:
            # Each string in the secondary_artist_list is split according to the artist delimiters.
            # Each of the newly created lists are then flattened into a single list (see self._flatten).
            parsed['secondary_artists'] = self._multi_split(secondary_artist_list, artist_delimiters)
        return parsed

    def _get_metadata(self, parsed):
        results = []
        temp = []
        artists = parsed['artists'] if 'artists' in parsed else None
        artist = artists[0] if artists else ''
        artistname = artists[1] if artists and len(artists) > 1 else ''
        mb_results = musicbrainzngs.search_recordings(query=parsed['title'], artist=artist, artistname=artistname,
                                                      limit=20)
        for recording in mb_results['recording-list']:
            if 'release-list' in recording:
                title = recording['title']
                if ('artists' not in parsed or title.lower() == parsed['title'].lower()) and self._valid_title(title):
                    artists = [a['artist']['name'] for a in recording['artist-credit'] if
                               isinstance(a, dict) and 'artist' in a]
                    artist = artists[0]  # Only use the first artist (may change in the future)
                    for release in recording['release-list']:
                        album = release['title']
                        album_id = release['id']
                        entry = {
                            'url': parsed['url'],
                            'title': title,
                            'artist': artist,
                            'album': album
                        }
                        if entry not in temp and self._valid(release):
                            temp.append(entry.copy())
                            entry['id'] = album_id
                            entry['img'] = self._cover_art_cache[
                                album_id] if album_id in self._cover_art_cache else self._get_cover_art(album_id)
                            results.append(entry)
        return results

    def _flatten(self, lst):
        return [item for sublist in lst for item in sublist]

    def _gen_regex(self, word_list):
        return r'(?:^|\W)*?(?i)(?:%s)\W*' % '|'.join(word_list)

    def _split(self, string, delimiters):
        return re.split(self._gen_regex(delimiters), string)

    def _multi_split(self, lst, delimiters):
        return self._flatten([self._split(item, delimiters) for item in lst])

    def _valid(self, release):
        banned_words = ['instrumental', 'best of', 'diss', 'remix', 'what i call', 'ministry of sound']
        approved_secondary_types = ['soundtrack', 'remix', 'mixtape/street']
        for word in banned_words:
            if word in release['title'].lower():
                return False
        if 'secondary-type-list' in release['release-group']:
            st = release['release-group']['secondary-type-list'][0].lower()
            if st not in approved_secondary_types:
                return False
        if not self._get_cover_art(release['id']):
            return False
        return True

    def _valid_title(self, title):
        banned_words = ['remix', 'instrumental', 'a cappella', 'remake']
        for word in banned_words:
            if word in title.lower():
                return False
        return True

    def _get_cover_art(self, album_id):
        try:
            if album_id in self._cover_art_cache:
                return self._cover_art_cache[album_id]
            else:
                if self.small_cover_art:
                    self._cover_art_cache[album_id] = musicbrainzngs.get_image_list(album_id)['images'][0]['thumbnails'][
                        'small']
                else:
                    self._cover_art_cache[album_id] = musicbrainzngs.get_image_list(album_id)['images'][0]['image']
                return self._cover_art_cache[album_id]
        except musicbrainzngs.musicbrainz.ResponseError:
            return None


if __name__ == '__main__':
    aj = AudioJack()
    url = sys.argv[1]
    results = aj.get_results(url)
    if len(results) > 0:
        download = aj.select(results[0])
    else:
        download = aj.select({'url': url})
    print 'Downloaded %s' % download
