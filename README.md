# AudioJack
A smart YouTube to MP3 converter that automatically finds and adds metadata/ID3 tags (artist, title, album, cover art) to downloaded MP3 files.

## Disclaimer
This program is strictly intended for demonstration purposes. Using this program to download online media may breach the corresponding website's terms of service and may even be illegal in your country. Use this program at your own discretion.

## Demo
- [Desktop version](https://github.com/Blue9/AudioJack-GUI)

## Requirements
1. Python 3.6+
2. [FFmpeg](https://www.ffmpeg.org/) (for MP3 conversion).  
3. In addition, you will need to install the following modules before using AudioJack:
 - [mutagen](https://bitbucket.org/lazka/mutagen)
 - [musicbrainzngs v0.6](https://github.com/alastair/python-musicbrainzngs)
 - [youtube-dl](https://github.com/rg3/youtube-dl)

## Usage
Before doing anything, you must set a user agent for your application. This will let MusicBrainz know who is accessing their database and prevent abuse of their services. You can do this by typing:

    audiojack.set_useragent('App Name', 'Version')
**Note:** Both 'App Name' and 'Version' should be strings.

### Retrieving metadata for a song
To retrieve the metadata for a particular URL, use **AudioJack**'s `get_results(url)` function.

    audiojack.get_results("URL goes here")
This will return a list of entries as dictionaries, in the format `{'artist': artist, 'title': title, 'album': album, 'url': url, 'id': 'musicbrainz id'}`.  
Example results list:

    [{'artist': 'Hippy Hop', 'title': 'Formulaic Song', 'album': 'Formulaic Song Single', 'url': 'https://youtube.com/watch?v=notarealvideo, 'id': '1234'},
     {'artist': 'Hippy Hop', 'title': 'Formulaic Song', 'album': 'Formulaic Songs EP', 'url': 'https://youtube.com/watch?v=alsonotarealvideo, 'id': '5678'},
     {'artist': 'Hippy Hop', 'title': 'Another Formulaic Song', 'album': 'Formulaic Songs EP', 'url': 'https://youtube.com/watch?v=anothernotrealvideo, 'id': '2468'},]

### Selecting metadata
Selecting which ID3 tags to add is very easy with **AudioJack**, simply type:

    audiojack.select(entry)
where "entry" is either an entry dictionary provided by `audiojack.get_results(url)` or a custom made entry. For example, to download the first result when calling `audiojack.get_results(url)`, you could type:

    audiojack.select(audiojack.get_results(url)[0])

Optionally, the path to download the .mp3 file to may be added, however if this is omitted, the file will be placed in your Downloads folder:

    audiojack.select(entry, 'C:\Music')

### Downloading
After calling `audiojack.select(entry)`, the MP3 is automatically downloaded and converted in the format `SongTitle.mp3` to the Downloads folder or your set path.

## Contributing
Contributing back to the project is **strongly** suggested, as this helps keep the project alive and well. Guidelines for contributing will be added soon.
