import re
import requests
from . import utils


PTH_URL = 'https://passtheheadphones.me/'
RATE_LIMIT = 2.0  # Seconds between requests.


class LoginException(Exception):
    pass


class UploadException(Exception):
    pass


class API:
    '''
    A class for interacting with PTH and its API.
    '''
    def __init__(self, username=None, password=None, url=PTH_URL):
        self.username = username
        self.password = password
        self.url = url
        self.authkey = None
        self.passkey = None
        self.userid = None
        self.session = requests.Session()
        self._login()

    @utils.rate_limit(RATE_LIMIT)
    def get(self, url, *args, **kwargs):
        return self.session.get(self.url + url, *args, **kwargs)

    @utils.rate_limit(RATE_LIMIT)
    def post(self, url, *args, **kwargs):
        return self.session.post(self.url + url, *args, **kwargs)

    def _login(self):
        data = {'username': self.username, 'password': self.password}
        r = self.post('login.php', data=data)
        if r.status_code != 200:
            raise LoginException('Unable to log in. Check your credentials.')
        res = self.get('ajax.php', params={'action': 'index'}).json()
        accountinfo = res['response']
        self.authkey = accountinfo['authkey']
        self.passkey = accountinfo['passkey']
        self.userid = accountinfo['id']

    def upload(self, release, description=None):
        '''
        Uploads the release to PTH.
        '''
        data = [
            ('submit', 'true'),
            ('auth', self.authkey),
            ('type', '0'),
            ('title', release.title),
            ('year', str(release.original_year)),
            ('record_label', release.record_label if release.is_original else ''),
            ('catalogue_number', release.catalog_number if release.is_original else ''),
            ('releasetype', str(release.type)),
            ('remaster', 'on' if not release.is_original else None),
            ('remaster_year', str(release.year) if not release.is_original else ''),
            ('remaster_title', ''),
            ('remaster_record_label', release.record_label if not release.is_original else ''),
            ('remaster_catalogue_number', release.catalog_number if not release.is_original else ''),
            ('format', release.format),
            ('bitrate', release.bitrate),
            ('other_bitrate', ''),
            ('media', release.medium),
            ('genre_tags', release.tags[0]),
            ('tags', ', '.join(release.tags)),
            ('image', release.artwork_url),
            ('album_desc', release.description),
            ('release_desc', description)
        ]
        for artist in release.artists:
            data.append(("artists[]", artist.name))
            data.append(("importance[]", artist.importance))

        files = [("file_input", open(release.torrent, 'rb'))]
        for log_file in release.log_files:
            files.append(("logfiles[]", open(log_file, 'rb')))

        r = self.post('upload.php', data=data, files=files)
        if 'torrent_comments' not in r.text:
            match = re.search('<p style="color: red; text-align: center;">([^<]+)', r.text)
            if match:
                raise UploadException(match.group(1))
            else:
                raise UploadException('The upload failed.')
