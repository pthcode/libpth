import string
import textwrap
from beets.util import sanitize_path


ALBUM_TEMPLATE = string.Template('$artist - $album ($year) [$format_info]')


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
