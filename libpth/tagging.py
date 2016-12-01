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
    artist = textwrap.shorten(release.albumartist, width=50, placeholder='_')
    album = textwrap.shorten(release.album, width=40, placeholder='_')
    year = release.year
    format_info = release.medium + ' ' + release.format
    path = ALBUM_TEMPLATE.substitute(**locals())
    if release.catalognum:
        path += ' {' + release.catalognum + '}'
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
    Returns the format (FLAC / V0 / 320) of the audio file located at `path`.
    '''
    mediafile = MediaFile(path)
    if mediafile.format == 'FLAC':
        return 'FLAC'
    elif mediafile.format == 'MP3' and mediafile.bitrate == 320000:
        return '320'
    elif mediafile.format == 'MP3' and mediafile.bitrate >= 200000:
        return 'V0'
    raise InvalidFormatException('{} is not a valid audio file.'.format(path))
