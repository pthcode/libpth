import beets


class ReleaseGroup:
    '''
    A ReleaseGroup represents an album and all of its releases.
    '''
    pass


class Release(beets.library.Album):
    '''
    A Release is a given release of an album in a certain format.

    It contains a list of tracks and other files associated with it.
    '''
    pass
