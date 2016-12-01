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

    @property
    def medium(self):
        '''
        Returns the release's delivery mechanism (Vinyl, CD, WEB, etc.).
        '''
        return {
            'CD': 'CD',
            'CD-R': 'CD',
            'Enhanced CD': 'CD',
            'HDCD': 'CD',
            'DualDisc': 'CD',
            'Copy Control CD': 'CD',
            'Vinyl': 'Vinyl',
            '12\' Vinyl': 'Vinyl',
            'Digital Media': 'WEB',
            'SACD': 'SACD',
            'Hybrid SACD': 'SACD',
            'Cassette': 'Cassette',
            None: 'CD',
        }[self.media]

    @property
    def format(self):
        '''
        Returns the release's file format (FLAC / V0 / 320).
        '''
        # TODO: Support V0/320.
        return 'FLAC'
