# AudioJack
A smart YouTube to MP3 converter that automatically finds and adds metadata/ID3 tags (artist, title, album, cover art) to downloaded MP3 files.

## Requirements
1. Python 2.7
2. [FFmpeg](https://www.ffmpeg.org/) (for MP3 conversion).  
3. In addition, you will need to install the following modules before using AudioJack:
 - [mutagen](https://bitbucket.org/lazka/mutagen)
 - [musicbrainzngs v0.6.dev0](https://github.com/alastair/python-musicbrainzngs)
 - [youtube-dl](https://github.com/rg3/youtube-dl)

## Usage
Before doing anything, you must set a user agent for your application. This will let MusicBrainz know who is accessing their database and prevent abuse of their services. You can do this by typing:

    audiojack.set_useragent('App Name', 'Version')
**Note:** Both "App Name" and "Version" should be strings.

### Retrieving metadata for a song
To retrieve the metadata for a particular URL, use **AudioJack**'s built-in `get_results()` function.

    audiojack.get_results("URL goes here")
This will return a list of lists, each of which contains metadata in the format `[Artist, Title, Album, MusicBrainz ID]`.  
Example results list:

    [["Foo", "Foo's song", "Foo's album", "aaaa"],
     ["Bar", "Bar's song", "Bar's album", "bbbb"],
     ["Baz", "Baz's song", "Baz's album", "cccc"]]

### Selecting metadata
Selecting which ID3 tags to add is very easy with **AudioJack**, simply type:

    audiojack.select(index)
where "index" is equal to the numerical index of the metadata in the results list.  
For example, if the results lists was

    [["Foo", "Foo's song", "Foo's album", "aaaa"],
     ["Bar", "Bar's song", "Bar's album", "bbbb"],
     ["Baz", "Baz's song", "Baz's album", "cccc"]]
and `["Bar", "Bar's song", "Bar's album", "bbbb"]` was the correct metadata for the song, then you would type:

    audiojack.select(1)

### Custom metadata
In the rare case that none of the results are appropriate for the requested song, you can add custom tags to the MP3 by typing:

    audiojack.custom('Artist', 'Title', 'Album')

### Downloading
After using `audiojack.select()` or `audiojack.custom()`, the MP3 is automatically downloaded and converted in the format `SongTitle.mp3` in the same folder that the program was run in.

## Contributing
Contributing back to the project is **strongly** suggested, as this helps keep the project alive and well. Guidelines for contributing will be added soon.
