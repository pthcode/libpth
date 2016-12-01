import beets.library
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

    - `path`: The path to the release directory.
    - `info`: An optional beets.autotag.AlbumInfo object.
    '''
    def __init__(self, path, info=None):
        self.path = path
        self.info = info

    @property
    def title(self):
        '''
        Returns the release title.
        '''
        return self.info.album

    @property
    def album_artist(self):
        '''
        Returns the primary artist for this release.
        '''
        return self.info.artist

    @property
    def artists(self):
        '''
        Returns a list of ReleaseArtists for this release.
        '''
        return list(map(ReleaseArtist, (track.artist for track in self.info.tracks)))

    @property
    def year(self):
        '''
        Returns the year in which this release was released.
        '''
        return self.info.year or tagging.release_year(self.path)

    @property
    def original_year(self):
        '''
        Returns the year in which this release group was originally released.
        '''
        return self.info.original_year

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
        }[self.info.media]

    @property
    def format(self):
        '''
        Returns the release's audio format (FLAC / MP3).
        '''
        return tagging.audio_format(self.path)

    @property
    def bitrate(self):
        '''
        Returns the release's audio bitrate (Lossless / 24bit Lossless / 320 / V0 (VBR)).
        '''
        return tagging.audio_bitrate(self.path)

    @property
    def record_label(self):
        '''
        Return the release's record label.
        '''
        return self.info.label

    @property
    def catalog_number(self):
        '''
        Returns the release's catalog number.
        '''
        return self.info.catalognum

    @property
    def type(self):
        '''
        Returns the release type (e.g. Album, Compilation, Anthology).
        '''
        result = {
            "album": 1,
            "soundtrack": 3,
            "ep": 5,
            "compilation": 7,
            "single": 9,
            "live": 11,
            "remix": 13,
            "other": 1,
            None: 1
        }[self.info.albumtype]
        if result == 7 and len(set(artist.name for artist in self.artists)) == 1:
            # A compilation of one artist's songs is an Anthology.
            result = 6
        return result

    def to_beets_album(self):
        '''
        Creates a beets.library.Album() object from this release.
        '''
        result = beets.library.Album()
        for key, value in self.info.__dict__.items():
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


class ReleaseArtist:
    '''
    A ReleaseArtist represents a musician or music group on a particular release.

    - `name`: The name of this artist.
    - `importance`: The role of the artist on the release.
    '''
    def __init__(self, name, importance=1):
        self.name = name
        self.importance = importance
