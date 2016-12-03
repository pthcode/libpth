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
    - `match`: An optional beets.autotag.AlbumMatch object.
    '''
    def __init__(self, path=None, info=None, match=None, title=None, album_artist=None, artists=None, year=None,
                 original_year=None, medium=None, format=None, bitrate=None, record_label=None, catalog_number=None,
                 type=None, artwork_url=None, tags=None, torrent=None):
        self.path = path
        self.match = match
        self.info = match and match.info
        self.artwork_url = artwork_url
        self.tags = tags
        self.torrent = torrent
        self._title = title
        self._album_artist = album_artist
        self._artists = artists
        self._year = year
        self._original_year = original_year
        self._medium = medium
        self._format = format
        self._bitrate = bitrate
        self._record_label = record_label
        self._catalog_number = catalog_number
        self._type = type

    @property
    def title(self):
        '''
        Returns the release title.
        '''
        return self._title or self.info.album

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def album_artist(self):
        '''
        Returns the primary artist for this release.
        '''
        return self._album_artist or self.info.artist

    @album_artist.setter
    def album_artist(self, value):
        self._album_artist = value

    @property
    def artists(self):
        '''
        Returns a list of ReleaseArtists for this release.
        '''
        return self._artists or list(map(ReleaseArtist, (track.artist for track in self.info.tracks)))

    @artists.setter
    def artists(self, value):
        self._artists = value

    @property
    def year(self):
        '''
        Returns the year in which this release was released.
        '''
        return self._year or self.info.year or tagging.release_year(self.path)

    @year.setter
    def year(self, value):
        self._year = value

    @property
    def original_year(self):
        '''
        Returns the year in which this release group was originally released.
        '''
        return self._original_year or self.info.original_year

    @original_year.setter
    def original_year(self, value):
        self._original_year = value

    @property
    def medium(self):
        '''
        Returns the release's delivery mechanism (Vinyl, CD, WEB, etc.).
        '''
        return self._medium or {
            'CD': 'CD',
            'CD-R': 'CD',
            'Enhanced CD': 'CD',
            'HDCD': 'CD',
            'DualDisc': 'CD',
            'Copy Control CD': 'CD',
            'Vinyl': 'Vinyl',
            '12\" Vinyl': 'Vinyl',
            'Digital Media': 'WEB',
            'SACD': 'SACD',
            'Hybrid SACD': 'SACD',
            'Cassette': 'Cassette',
            None: 'CD',
        }[self.info.media]

    @medium.setter
    def medium(self, value):
        self._medium = value

    @property
    def format(self):
        '''
        Returns the release's audio format (FLAC / MP3).
        '''
        return self._format or tagging.audio_format(self.path)

    @format.setter
    def format(self, value):
        self._format = value

    @property
    def bitrate(self):
        '''
        Returns the release's audio bitrate (Lossless / 24bit Lossless / 320 / V0 (VBR)).
        '''
        return self._bitrate or tagging.audio_bitrate(self.path)

    @bitrate.setter
    def bitrate(self, value):
        self._bitrate = value

    @property
    def record_label(self):
        '''
        Return the release's record label.
        '''
        return self._record_label or self.info.label

    @record_label.setter
    def record_label(self, value):
        self._record_label = value

    @property
    def catalog_number(self):
        '''
        Returns the release's catalog number.
        '''
        return self._catalog_number or self.info.catalognum

    @catalog_number.setter
    def catalog_number(self, value):
        self._catalog_number = value

    @property
    def type(self):
        '''
        Returns the release type (e.g. Album, Compilation, Anthology).
        '''
        if self._type:
            return self._type

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

    @type.setter
    def type(self, value):
        self._type = value

    @property
    def is_original(self):
        '''
        Returns True if this release is the original release; False otherwise.
        '''
        if self.original_year is None:
            return True
        if self.original_year == self.year:
            return True
        return False

    @property
    def description(self):
        '''
        Returns a bbcode formatted description for this release.
        '''
        return tagging.release_description(self)

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
    def other_files(self):
        '''
        Returns a list of all non-audio (but still allowed) files within
        this release.
        '''
        return sorted(set(self.files) - set(self.audio_files))

    @property
    def log_files(self):
        '''
        Returns a list of all log files in this release.
        '''
        return tagging.log_files(self.path)

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
