import re
import string
import textwrap
from beets.mediafile import MediaFile
from beets.util import sanitize_path
from .utils import locate, ext_matcher


ALBUM_TEMPLATE = string.Template('$artist - $album ($year) [$format_info]')
AUDIO_EXTENSIONS = ('.flac', '.mp3')
ALLOWED_EXTENSIONS = AUDIO_EXTENSIONS + ('.cue', '.log', '.gif', '.jpeg', '.jpg', '.md5', '.nfo', '.pdf', '.png',
                                         '.sfv', '.txt')


class InvalidFormatException(Exception):
    pass


def directory_name(release):
    '''
    Returns the proper directory name for a Release.
    '''
    artist = textwrap.shorten(release.album_artist, width=50, placeholder='_')
    album = textwrap.shorten(release.title, width=40, placeholder='_')
    year = release.year
    format_info = release.medium + ' ' + release.format
    path = ALBUM_TEMPLATE.substitute(**locals())
    if release.catalog_number:
        path += ' {' + release.catalog_number + '}'
    path = path.replace('/', '_').replace('\\', '_')
    path = sanitize_path(path)
    return path


def audio_files(path):
    '''
    Returns a list of all audio files within `path`.
    '''
    return sorted(locate(path, ext_matcher(*AUDIO_EXTENSIONS)))


def allowed_files(path):
    '''
    Returns a list of all allowed files within `path`.
    '''
    return sorted(locate(path, ext_matcher(*ALLOWED_EXTENSIONS)))


def audio_format(path):
    '''
    Returns the format (FLAC / MP3) of the release located at `path`.
    '''
    mediafile = MediaFile(audio_files(path)[0])
    if mediafile.format == 'FLAC':
        return 'FLAC'
    elif mediafile.format == 'MP3':
        return 'MP3'
    raise InvalidFormatException('{} is not a valid audio release.'.format(path))


def audio_bitrate(path):
    '''
    Returns the bitrate (Lossless / 24bit Lossless / 320 / V0 (VBR))
    of the release located at `path`.
    '''
    mediafile = MediaFile(audio_files(path)[0])
    if mediafile.format == 'FLAC' and mediafile.bitdepth == 24:
        return '24bit Lossless'
    elif mediafile.format == 'FLAC' and mediafile.bitdepth == 16:
        return 'Lossless'
    elif mediafile.format == 'MP3' and mediafile.bitrate == 320000:
        return '320'
    elif mediafile.format == 'MP3':
        bitrates = (MediaFile(audio_file).bitrate for audio_file in audio_files(path))
        average_bitrate = sum(bitrates) / len(bitrates)
        if average_bitrate >= 200000:
            return 'V0'
    raise InvalidFormatException('{} is not a valid audio release.'.format(path))


def release_year(path):
    '''
    Returns the year in which the release located at `path` was released.
    '''
    match = re.search(r'\d{4}', path)
    if match:
        return int(match)
    mediafile = MediaFile(audio_files(path)[0])
    return mediafile.year
