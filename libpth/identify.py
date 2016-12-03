import os
import sys
import math
from collections import defaultdict
from beets import autotag, config, importer, ui
from beets.autotag import AlbumMatch, Recommendation
from beets.importer import QUEUE_SIZE, read_tasks
from beets.ui import UserError, print_
from beets.ui.commands import TerminalImportSession, manual_search, dist_string, penalty_string, disambig_string,\
    show_change, manual_id
from beets.util import pipeline, displayable_path, syspath, normpath
from beetsplug.fetchart import FetchArtPlugin, CoverArtArchive, AlbumArtOrg, Amazon, Wikipedia, FanartTV
from beetsplug.lastgenre import LastGenrePlugin, LASTFM
from .structures import Release


VALID_TAGS = set([
    '1960s', '1970s', '1980s', '1990s', '2000s', '2010s', 'alternative', 'ambient', 'black.metal', 'blues', 'classical',
    'comedy', 'country', 'death.metal', 'deep.house', 'downtempo', 'drum.and.bass', 'dub', 'dubstep', 'electronic',
    'experimental', 'folk', 'funk', 'gospel', 'grime', 'heavy.metal', 'hip.hop', 'house', 'idm', 'indie',
    'instrumental', 'jazz', 'live', 'metal', 'noise', 'pop', 'pop.rock', 'post.punk', 'progressive.rock', 'psychedelic',
    'punk', 'reggae', 'rhythm.and.blues', 'rock', 'shoegaze', 'ska', 'soul', 'synth.pop', 'techno', 'trance',
    'video.game'
])
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.gif', '.png')


class IdentifySession(TerminalImportSession):
    '''
    A beets import session which is used to identify releases.
    '''
    def __init__(self, paths, release_list, callback):
        self.want_resume = False
        self.config = defaultdict(lambda: None)
        self.release_list = release_list
        self.callback = callback
        super().__init__(None, None, paths, None)

    def run(self):
        stages = [
            read_tasks(self),
            lookup_candidates(self),
            identify_release(self)
        ]
        pl = pipeline.Pipeline(stages)
        pl.run_parallel(QUEUE_SIZE)


class ArtworkFetcher(FetchArtPlugin):
    def __init__(self):
        super().__init__()
        sources = [CoverArtArchive, AlbumArtOrg, Amazon, Wikipedia, FanartTV]
        self.sources = [s(self._log, self.config) for s in sources]


def choose_candidate(candidates, singleton, rec, cur_artist=None,
                     cur_album=None, item=None, itemcount=None,
                     extra_choices=[]):
    """Given a sorted list of candidates, ask the user for a selection
    of which candidate to use. Applies to both full albums and
    singletons  (tracks). Candidates are either AlbumMatch or TrackMatch
    objects depending on `singleton`. for albums, `cur_artist`,
    `cur_album`, and `itemcount` must be provided. For singletons,
    `item` must be provided.

    `extra_choices` is a list of `PromptChoice`s, containg the choices
    appended by the plugins after receiving the `before_choose_candidate`
    event. If not empty, the choices are appended to the prompt presented
    to the user.

    Returns one of the following:
    * the result of the choice, which may be SKIP, ASIS, TRACKS, or MANUAL
    * a candidate (an AlbumMatch/TrackMatch object)
    * the short letter of a `PromptChoice` (if the user selected one of
    the `extra_choices`).
    """
    # Sanity check.
    assert not singleton
    assert cur_artist is not None
    assert cur_album is not None

    # Zero candidates.
    if not candidates:
        print_(u"No matching release found for {0} tracks."
               .format(itemcount))
        print_(u'For help, see: '
               u'http://beets.readthedocs.org/en/latest/faq.html#nomatch')
        opts = (u'Skip', u'Enter search', u'enter Id', u'aBort')
        sel = ui.input_options(opts)
        if sel == u'e':
            return importer.action.MANUAL
        elif sel == u's':
            return importer.action.SKIP
        elif sel == u'b':
            raise importer.ImportAbort()
        elif sel == u'i':
            return importer.action.MANUAL_ID
        else:
            assert False

    while True:
        # Display and choose from candidates.
        require = rec <= Recommendation.low

        # Display list of candidates.
        print_(u'Finding tags for {0} "{1} - {2}".'.format(
            u'album', cur_artist, cur_album,
        ))

        print_(u'Candidates:')
        for i, match in enumerate(candidates):
            # Index, metadata, and distance.
            line = [
                u'{0}.'.format(i + 1),
                u'{0} - {1}'.format(
                    match.info.artist,
                    match.info.album,
                ),
                u'({0})'.format(dist_string(match.distance)),
            ]

            # Penalties.
            penalties = penalty_string(match.distance, 3)
            if penalties:
                line.append(penalties)

            # Disambiguation
            disambig = disambig_string(match.info)
            if disambig:
                line.append(ui.colorize('text_highlight_minor',
                                        u'(%s)' % disambig))

            print_(u' '.join(line))

        # Ask the user for a choice.
        opts = (u'Skip', u'Enter search', u'enter Id', u'aBort')
        sel = ui.input_options(opts,
                               numrange=(1, len(candidates)))
        if sel == u's':
            return importer.action.SKIP
        elif sel == u'e':
            return importer.action.MANUAL
        elif sel == u'b':
            raise importer.ImportAbort()
        elif sel == u'i':
            return importer.action.MANUAL_ID
        else:  # Numerical selection.
            match = candidates[sel - 1]
            if sel != 1:
                # When choosing anything but the first match,
                # disable the default action.
                require = True

        # Show what we're about to do.
        show_change(cur_artist, cur_album, match)

        # Exact match => tag automatically.
        if rec == Recommendation.strong:
            return match

        # Ask for confirmation.
        opts = (u'Apply', u'More candidates', u'Skip', u'Enter search',
                u'enter Id', u'aBort')
        default = config['import']['default_action'].as_choice({
            u'apply': u'a',
            u'skip': u's',
            u'none': None,
        })
        if default is None:
            require = True
        sel = ui.input_options(opts, require=require,
                               default=default)
        if sel == u'a':
            return match
        elif sel == u's':
            return importer.action.SKIP
        elif sel == u'e':
            return importer.action.MANUAL
        elif sel == u'b':
            raise importer.ImportAbort()
        elif sel == u'i':
            return importer.action.MANUAL_ID


def choose_match(task):
    """Given an initial autotagging of items, go through an interactive
    dance with the user to ask for a choice of metadata. Returns an
    AlbumMatch object or SKIP.
    """
    # Show what we're tagging.
    print_()
    print_(displayable_path(task.paths, u'\n') +
           u' ({0} items)'.format(len(task.items)))

    # Loop until we have a choice.
    candidates, rec = task.candidates, task.rec
    while True:
        # Ask for a choice from the user.
        choice = choose_candidate(
            candidates, False, rec, task.cur_artist, task.cur_album,
            itemcount=len(task.items)
        )

        # Choose which tags to use.
        if choice is importer.action.SKIP:
            # Pass selection to main control flow.
            return choice
        elif choice is importer.action.MANUAL:
            # Try again with manual search terms.
            search_artist, search_album = manual_search(False)
            _, _, candidates, rec = autotag.tag_album(
                task.items, search_artist, search_album
            )
        elif choice is importer.action.MANUAL_ID:
            # Try a manually-entered ID.
            search_id = manual_id(False)
            if search_id:
                _, _, candidates, rec = autotag.tag_album(
                    task.items, search_ids=search_id.split()
                )
        else:
            # We have a candidate! Finish tagging. Here, choice is an
            # AlbumMatch object.
            assert isinstance(choice, autotag.AlbumMatch)
            return choice


@pipeline.stage
def lookup_candidates(session, task):
    if not task or task.skip:
        return

    task.lookup_candidates()
    return task


@pipeline.stage
def identify_release(session, task):
    if not task or task.skip:
        return

    match = choose_match(task)
    if not isinstance(match, AlbumMatch):
        return

    path = task.toppath.decode(sys.getfilesystemencoding())
    release = Release(path, match=match)
    session.callback and session.callback(release)
    session.release_list.append(release)


def identify_releases(release_paths, callback=None):
    '''
    Given an iterator of release paths, this will attempt to identify
    each release and return a list of corresponding Release objects.

    Releases that could not be identified will not be present in the list.

    Note: This function will ask for user input.

    If you pass in `callback`, it will be called for each identified
    Release.
    '''
    for path in release_paths:
        if not os.path.exists(syspath(normpath(path))):
            raise UserError(u'no such file or directory: {0}'.format(
                displayable_path(path)))

    result = []
    session = IdentifySession(release_paths, result, callback)
    session.run()
    return result


def fetch_artwork(release, fetcher=ArtworkFetcher()):
    '''
    Given a Release, this will search the internet for matching album
    artwork, and if found, return its URL.
    '''
    album = release.to_beets_album()
    result = fetcher.art_for_album(album, [release.path], False)

    if result and result.url:
        url = result.url

        # If the URL doesn't end with a image extension, PTH won't accept it.
        if not url.endswith(IMAGE_EXTENSIONS):
            # So we have to trick it.
            url += '#.jpg'

        return url

    return None


def fetch_tags(release, limit=5, min_weight=10, lastgenre=LastGenrePlugin()):
    '''
    Given a release, this will search last.fm for tags and return the
    ones that are valid on PTH (up to a specified `limit`).

    Tags with fewer than `min_weight` votes will be excluded.
    '''
    result = set()

    # First retrieve tags for the album.
    last_obj = LASTFM.get_album(release.album_artist, release.title)
    for tag in lastgenre._tags_for(last_obj, min_weight)[:math.ceil(limit / 2)]:
        if tag in VALID_TAGS:
            result.add(tag)

    # If we don't have enough, fall back to artist tags.
    if len(result) < math.floor(limit / 2):
        last_obj = LASTFM.get_artist(release.album_artist)
        for tag in lastgenre._tags_for(last_obj, min_weight)[:math.ceil(limit / 2)]:
            if tag in VALID_TAGS:
                result.add(tag)

    return list(result)[:limit]
