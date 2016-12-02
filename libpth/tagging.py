import os
import re
import shutil
import string
import os.path
import textwrap
from beets.mediafile import MediaFile
from beets.util import sanitize_path
from .utils import locate, ext_matcher


ALBUM_TEMPLATE = string.Template('$artist - $album ($year) [$format_info]')
AUDIO_EXTENSIONS = ('.flac', '.mp3')
ALLOWED_EXTENSIONS = AUDIO_EXTENSIONS + ('.cue', '.log', '.gif', '.jpeg', '.jpg', '.md5', '.nfo', '.pdf', '.png',
                                         '.sfv', '.txt')
MAX_FILENAME_LENGTH = 180


class InvalidFormatException(Exception):
    pass


def directory_name(release):
    '''
    Returns the proper directory name for a Release.
    '''
    artist = textwrap.shorten(release.album_artist, width=50, placeholder='_')
    album = textwrap.shorten(release.title, width=40, placeholder='_')
    year = release.year
    format_info = release.format
    if release.medium != 'CD':
        format_info = release.medium + ' ' + format_info
    path = ALBUM_TEMPLATE.substitute(**locals())
    if release.catalog_number:
        path += ' {' + release.catalog_number + '}'
    path = path.replace('/', '_').replace('\\', '_')
    path = sanitize_path(path)
    return path


def fix_release_filenames(release, directory=None):
    '''
    Renames a release and all of its files so that it has the proper
    directory name and includes only allowed files with filenames less
    than {} characters total.

    If `directory` is specified, the release will be moved
    there. Otherwise, it will be renamed in its current directory.
    '''.format(MAX_FILENAME_LENGTH)
    if directory is None:
        directory = os.path.dirname(release.path)

    output_dir = os.path.join(directory, directory_name(release))
    os.makedirs(output_dir)

    for audio_file in release.audio_files:
        relpath = os.path.relpath(audio_file, start=release.path)
        path = os.path.join(output_dir, relpath)
        path = truncate_path(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.move(audio_file, path)

    for other_file in release.other_files:
        relpath = os.path.relpath(other_file, start=release.path)
        path = os.path.join(output_dir, relpath)
        path = truncate_path(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.move(other_file, path)

    shutil.rmtree(release.path)
    release.path = output_dir
    return release


def truncate_path(path):
    '''
    Truncates `path` to contain no more than {max_length} characters.

    If `path` has fewer than {max_length} characters, it will be returned unchanged.
    '''.format(max_length=MAX_FILENAME_LENGTH)
    if len(path) <= MAX_FILENAME_LENGTH:
        return path

    base, ext = os.path.splitext(os.path.basename(path))
    offset = MAX_FILENAME_LENGTH - len(path)
    assert len(base) + offset > 0
    return os.path.join(os.path.dirname(path), base[:offset] + ext)


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
