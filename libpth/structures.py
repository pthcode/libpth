from . import tagging


class ReleaseGroup:
    '''
    A ReleaseGroup represents an album and all of its releases.
    '''
    pass


class Release:
    '''
    A Release is a given release of an album in a certain format.

    It contains a list of tracks and other files associated with it.
    '''
    def __init__(self, path):
        self.path = path
        self.artist = None
        self.title = None
        self.genre = None
        self.year = None
        self.month = None
        self.day = None
        self.disctotal = None
        self.is_compilation = None
        self.mb_albumid = None
        self.mb_albumartistid = None
        self.albumtype = None
        self.label = None
        self.mb_releasegroupid = None
        self.asin = None
        self.media = None
        self.catalognum = None
        self.script = None
        self.language = None
        self.country = None
        self.albumstatus = None
        self.albumdisambig = None
        self.original_year = None
        self.original_month = None
        self.original_day = None

    @classmethod
    def from_beets_albuminfo(cls, path, albuminfo):
        '''
        Converts a beets.autotag.AlbumInfo to a Release.
        '''
        result = Release(path)
        for key, value in albuminfo.__dict__.items():
            if key == 'album':
                dest = 'title'
            elif key == 'album_id':
                dest = 'mb_albumid'
            elif key == 'releasegroup_id':
                dest = 'mb_releasegroupid'
            else:
                dest = key
            setattr(result, dest, value)
        return result

    @property
    def files(self):
        '''
        Returns a list of all allowed files within this release.
        '''
        return tagging.allowed_files(self.path)

    @property
    def audio_files(self):
        '''
        Returns a list of all audio files within this release.
        '''
        return tagging.audio_files(self.path)

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
        return tagging.audio_format(self.audio_files[0])
