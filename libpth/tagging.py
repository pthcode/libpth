import os
import re
import shutil
import string
import os.path
import textwrap
import beets.autotag
from beets.mediafile import MediaFile
from beets.util import sanitize_path
from .utils import locate, ext_matcher


ALBUM_TEMPLATE = string.Template('$artist - $album ($year) [$format_info]')
AUDIO_FILE_TEMPLATE = string.Template('$number. $title$extension')
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


def audio_filename(path, is_compilation=False):
    ''''
    Returns the proper filename for the audio file located at `path`.

    Assumes that the audio file has already been properly tagged.

    If `is_compilation` is True, it means the audio file is part of
    a compilation, and thus the track artist will be included in the
    filename.
    '''
    mediafile = MediaFile(path)

    if mediafile.disctotal and mediafile.disc and mediafile.disctotal > 1:
        number = '{}.{:02}'.format(mediafile.disc, mediafile.track)
    else:
        number = '{:02}'.format(mediafile.track)

    if is_compilation:
        title = '{} - {}'.format(mediafile.artist, mediafile.title)
    else:
        title = mediafile.title

    _, extension = os.path.splitext(path)
    return AUDIO_FILE_TEMPLATE.substitute(**locals())


def apply_metadata(release):
    '''
    Assuming that `release` has a valid AlbumMatch, this function will
    apply the new metadata to the release's audio files.
    '''
    beets.autotag.apply_metadata(release.info, release.match.mapping)
    for item, _ in release.match.mapping.items():
        item.try_write()


def fix_release_filenames(release, directory=None, copy=False):
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
    os.makedirs(output_dir, exist_ok=not copy)

    rename_audio_files(release, directory=output_dir, copy=copy)
    rename_other_files(release, directory=output_dir, copy=copy)

    release.path = output_dir
    return release


def rename_audio_files(release, directory, copy=False):
    '''
    Moves (or copies) `release.audio_files` to their proper location within `directory`.

    Assumes that the audio files have already been properly tagged.
    '''
    for audio_file in release.audio_files:
        filename = audio_filename(audio_file, is_compilation=release.type == 7)
        path = os.path.join(directory, filename)
        path = truncate_path(path)
        if copy:
            shutil.copy2(audio_file, path)
        else:
            shutil.move(audio_file, path)


def rename_other_files(release, directory, copy=False):
    '''
    Moves (or copies) `release.other_files` to their proper location within `directory`.
    '''
    for other_file in release.other_files:
        relpath = os.path.relpath(other_file, start=release.path)
        path = os.path.join(directory, relpath)
        path = truncate_path(path)
        os.makedirs(os.path.dirname(path), exist_ok=not copy)
        if copy:
            shutil.copy2(other_file, path)
        else:
            shutil.move(other_file, path)

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
