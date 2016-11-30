#!/usr/bin/env python
import requests
from . import utils


PTH_URL = 'https://passtheheadphones.me/'
RATE_LIMIT = 2.0  # Seconds between requests.


class LoginException(Exception):
    pass


class API:
    '''
    A class for interacting with PTH and its API.
    '''
    def __init__(self, username=None, password=None, url=PTH_URL):
        self.username = username
        self.password = password
        self.url = url
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
