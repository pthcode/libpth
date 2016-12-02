import os
import re
import shutil
import string
import os.path
import textwrap
from beets.mediafile import MediaFile
from beets.util import sanitize_path
from .utils import locate, ext_matcher
from . import identify


ALBUM_TEMPLATE = string.Template('$artist - $album ($year) [$format_info]')
AUDIO_EXTENSIONS = ('.flac', '.mp3')
ALLOWED_EXTENSIONS = AUDIO_EXTENSIONS + ('.cue', '.log', '.gif', '.jpeg', '.jpg', '.md5', '.nfo', '.pdf', '.png',
                                         '.sfv', '.txt')
MAX_FILENAME_LENGTH = 180
MAX_FIELD_LENGTH = 80
MIN_YEAR = 1889
MIN_CD_YEAR = 1982
MAX_ALBUM_LENGTH = 200
MAX_URL_LENGTH = 255
ALLOWED_RELEASE_TYPES = [1,3,5,6,7,9,11,13,14,15,16,17,18,19,21]
ALLOWED_BITRATES = ['192', 'APS (VBR)', 'V2 (VBR)', 'V1 (VBR)', '256', 'APX (VBR)', 'V0 (VBR)', 'q8.x (VBR)', '320', 'Lossless', '24bit Lossless', 'Other']
ALLOWED_MEDIA = ['CD', 'DVD', 'Vinyl', 'Soundboard', 'SACD', 'DAT', 'Cassette', 'WEB']



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
    matches = re.findall(r'\d{4}', path)
    result = 0
    if len(matches) > 0:
        result = max(matches)
    mediafile = MediaFile(audio_files(path)[0])
    return max(int(result),int(mediafile.year))


def original_year(path):
    '''
    Returns the year in which the release located at `path` was released.
    '''
    matches = re.findall(r'\d{4}', path)
    result = 0
    if len(matches) > 0:
        result = min(matches)
    mediafile = MediaFile(audio_files(path)[0])
    return min(int(result),int(mediafile.year))

def is_original(release):
    if release.year != release.original_year:
        return False
    else:
        return True
    #elif disambig = ''
    #elif release.title != release_group.title

def validate_upload(release):
    '''
    The following checks are taken from Gazelle
    /sections/upload/upload_handle.php
    '''
    if len(release.title) not in range(1,MAX_ALBUM_LENGTH):
        print('Title must be between 1 and 200 characters.')
        return False
    elif release.type not in ALLOWED_RELEASE_TYPES:
        print('Release is not of valid type (album, compilation, etc.).')
        return False
    # TO-DO: elif len(release.tags) < 1:
    #     print('Enter at least one tag')
    elif release.record_label is not None and len(release.record_label) not in range(2,MAX_FIELD_LENGTH):
        print('Record label must be between 2 and ' + str(MAX_FIELD_LENGTH) + ' characters.')
        return False
    elif release.catalog_number is not None and len(release.catalog_number) not in range(2,MAX_FIELD_LENGTH):
        print('Catalog number must be between 2 and ' + str(MAX_FIELD_LENGTH) + ' characters.')
        return False
    # TO-DO: elif len(release.album_description) < 10:
    #     print('The album description has a minimum length of 10 characters.')
    elif release.medium == 'CD' and release.original_year < MIN_CD_YEAR:
        print('You have selected a year for an album that predates the media you say it was created on.')
        return False
    elif not is_original(release) and not release.year:
        print('Year of remaster/re-issue must be entered.')
        return False
    elif release.format == 'FLAC' and audio_bitrate(release.path) != 'Lossless':
        # Better: Do album file size vs. album duration check
        print('FLAC bitrate must be lossless.')
        return False
    # Missing Gazelle validation: ' You must enter the other bitrate (max length: 9 characters).'
    # This is the extra field when the bitrate is not one of the normal presets: V0/V2/320 etc.
    elif release.bitrate not in ALLOWED_BITRATES:
        print('You must choose a bitrate.')
        return False
    elif release.medium not in ALLOWED_MEDIA:
        print('Please select a valid media.')
        return False
    # TO-DO change fetch_artwork(release) back to release.artwork_url
    elif len(identify.fetch_artwork(release)) not in range(12,MAX_URL_LENGTH):
        print('The image URL you entered was invalid.')
        return False
    # TO-DO: elif len(release.description) < 10:
    #     print('The release description has a minimum length of 10 characters.')
    # TO-DO: Group ID was not numeric
    elif release.original_year > release.year:
        print('Invalid remaster year')
        return False

    '''
    Implementation of custom sanity checks
    '''
    if release.original_year < MIN_YEAR:
        print('Minimum year is ' + MIN_YEAR + ' as that is when the first record has been made.')
        return False
    elif ' & ' in release.artists[0].name:
        print('Arist names that contain & are not yet supported.')
        return False

    return True
