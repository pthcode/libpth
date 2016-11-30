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
    @classmethod
    def from_beets_albuminfo(cls, albuminfo):
        '''
        Converts a beets.autotag.AlbumInfo to a Release.
        '''
        result = Release()
        for key, value in albuminfo.__dict__.items():
            if key == 'artist':
                dest = 'albumartist'
            elif key == 'album_id':
                dest = 'mb_albumid'
            elif key == 'releasegroup_id':
                dest = 'mb_releasegroupid'
            else:
                dest = key
            setattr(result, dest, value)
        return result
