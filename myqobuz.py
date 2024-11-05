# -*- coding: utf-8 -*-
#!python
# pylint: disable=line-too-long, too-many-lines

"""
Around my "qobuz" : manage playlists and favorites from command line
    - displays playlists, favorites
    - add or remove tracks from playlists
    - add or remove favorites albums, tracks, artists

Need "qobuz" module modified for raw mode, list of performers

Note: playlists are supposed to have no duplicated track

"""

import sys
import os
import logging
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from datetime import datetime, timedelta
import json
import re
import requests

# read config file for login and preferences
try:
    with open('config.json') as fconf:
        MYCONFIG = json.load(fconf)
except FileNotFoundError:
    sys.exit('FAILED to load config file')

# the qobuz module can be located in a specific path
try:
    if MYCONFIG['qobuz_module']:
        sys.path.insert(0, MYCONFIG['qobuz_module'])
except KeyError:
    pass
import qobuz



def seconds_tostring(seconds):
    '''
    convert seconds to string
    format returned :
        [H:]MM:SS
    '''
    stime = []
    if seconds // 3600 > 0:
        stime.append('{}:'.format(seconds // 3600))
    stime.append('{:02d}:'.format((seconds // 60) % 60))
    stime.append('{:02d}'.format(seconds % 60))
    return ''.join(stime)


def timestamp_tostring(timestamp, fmt='%d/%m/%Y'):
    '''
    convert timestamp (negative or not) to date string
    '''
    if timestamp < 0:
        return (datetime(1970, 1, 1) + timedelta(seconds=timestamp)).strftime(fmt)
    else:
        return datetime.fromtimestamp(timestamp).strftime(fmt)


def str_max(string, maxchar):
    '''
    Returns string limited to max characters
    '''
    if len(string) <= maxchar:
        return string
    return string[:maxchar - 3] + '...'


def print_header(fmt, elements):
    '''
    print header for table
    '''
    #print('Favorites Albums')
    header = fmt % elements
    print(len(header) * '=')
    print(header)
    print(len(header) * '=')


def smart_bio(bio, size):
    '''
    process qobuz artist biography
        remove html tags
        split in lines of max size, on word
    '''
    lines = list()
    if not bio:
        return lines
    # remove html tag
    re_clean = re.compile('<.*?>')
    bio = re.sub(re_clean, '', bio)
    # split on a word
    while len(bio) > size:
        bioline = bio[:size]
        pos = bioline.rfind(' ')
        if pos > 0:
            lines.append(bioline[:pos])
            bio = bio[pos:]
        else:
            lines.append(bioline)
            bio = bio[size:]
    if len(bio) > 0:
        lines.append(bio)
    return lines



def download_album_image(album):
    '''
    download album image
    '''
    filename = f'{album.artist.name} - {album.title}.{album.id}.jpg'
    filename = filename.replace(':', '-').replace('/', '-')
    filename = f"{MYCONFIG['album']['cover_dir']}\\{filename}"
    if os.path.exists(filename):
        return
    resp = requests.get(album.images[MYCONFIG['album']['cover_size']], allow_redirects=True)
    open(filename, 'wb').write(resp.content)


def get_user_playlists(user, ptype, raw=False):
    '''
    Returns all user playlists

    Parameters
    ----------
    user: qobuz.User object
    '''
    limit = 50
    offset = 0
    playlists = list()
    while True:
        pls = user.playlists_get(filter=ptype, limit=limit, offset=offset, raw=raw)
        if raw:
            if len(pls["playlists"]["items"]) == 0:
                break
            playlists.append(pls["playlists"])
            offset += limit
            continue
        if not pls:
            break

        playlists += pls
        offset += limit
    return playlists



def get_user_favorites(user, fav_type, raw=False):
    '''
    Returns all user favorites

    Parameters
    ----------
    user: dict
        returned by qobuz.User
    fav_type: str
        favorites type: 'tracks', 'albums', 'artists'
    limi
    '''
    limit = 50
    offset = 0
    favorites = list()
    while True:
        favs = user.favorites_get(fav_type=fav_type, limit=limit, offset=offset, raw=raw)
        if raw:
            if len(favs[fav_type]["items"]) == 0:
                break
            for _f in favs[fav_type]["items"]:
                favorites.append(_f)
        else:
            if not favs:
                break
            favorites += favs
        offset += limit
    return favorites



def get_all_tracks(playlist, raw=False):
    '''
    Returns all tracks for a playlist

    Parameters
    ----------
    user: qobuz.User object
    '''
    limit = 50
    offset = 0
    tracks = list()
    while True:
        trks = playlist.get_tracks(limit=limit, offset=offset, raw=raw)
        if raw:
            if len(trks["tracks"]["items"]) == 0:
                break
            for _t in trks["tracks"]["items"]:
                tracks.append(_t)
        else:
            if not trks:
                break
            tracks += trks
        offset += limit
    return tracks



def qobuz_myplaylists(user, args, log):
    '''
    Get and displays my playlists
    '''
    log.info('get all playlists...')
    if args.type == 'all':
        args.type = 'owner,subscriber'
    if args.raw:
        json_data = get_user_playlists(user, args.type, args.raw)
        print(json.dumps(json_data, indent=4))
        print()
        for playlist in get_user_playlists(user, args.type):
            if args.name and args.name.lower() != playlist.name.lower():
                log.info('skip playlist "%s"', playlist.name)
                continue
            json_data = get_all_tracks(playlist, args.raw)
            print(json.dumps(json_data, indent=4))
            print()
        log.info('... done')
        return
    playlists = get_user_playlists(user, args.type, args.raw)
    log.info('... done')

    for playlist in playlists:
        if args.name and args.name.lower() != playlist.name.lower():
            log.info('skip playlist "%s"', playlist.name)
            continue

        print('Playlist: "{}", description: "{}", public: {}, collaborative: {}, duration: {}, {} tracks, update date: {}, id: {}'.\
            format(playlist.name, playlist.description, playlist.public, playlist.collaborative, \
                seconds_tostring(playlist.duration), playlist.tracks_count, datetime.fromtimestamp(playlist.updated_at).strftime('%Y-%m-%d'), playlist.id))

        if args.no_tracks:
            continue

        log.info('get playlist tracks for "%s"', playlist.name)
        tracks = get_all_tracks(playlist)

        log.info('display playlist tracks...')
        fmt = '    %9s | %-40s | %-50s | %-50s | %10s | %s'
        print_header(fmt, ('#idTrack', 'Artist', 'Album', 'Title', 'Track', 'Duration'))
        if args.sort:
            tracks.sort(key=lambda x: x.artist.name + x.album.title)
        for track in tracks:
            print(fmt % (track.id,
                         str_max(track.artist.name, 40),
                         str_max(track.album.title, 50),
                         str_max(track.title, 50),
                        f'{track.track_number}/{track.album.tracks_count}',
                        seconds_tostring(track.duration)))
            if args.performers:
                for performer in track.performers:
                    print(f'        -> {performer}')
        log.info('... done')
        print()


def qobuz_myfavorites(user, args, log):
    '''
    Get and displays favorites
    '''
    if args.type in ['tracks', 'all']:
        print('Favorites Tracks')
        fmt = '    %9s | %-40s | %-50s | %-50s | %10s | %10s'
        print_header(fmt, ('#idTrack', 'Artist', 'Album', 'Title', 'Track', 'Duration'))
        log.info('get all favorites...')
        tracks = get_user_favorites(user, 'tracks', args.raw)
        log.info('... done')
        if args.raw:
            print(json.dumps(tracks, indent=4))
        else:
            if args.sort:
                tracks.sort(key=lambda x: x.artist.name + x.album.title)
            for track in tracks:
                log.info('display track')
                print(fmt % (track.id,
                             str_max(track.artist.name, 40),
                             str_max(track.album.title, 50),
                             str_max(track.title, 50),
                             f'{track.track_number}/{track.album.tracks_count}',
                             seconds_tostring(track.duration)))
                if args.performers:
                    for performer in track.performers:
                        print(f'        -> {performer}')
                if args.cover:
                    download_album_image(track.album)
            log.info('display done')
        print()

    if args.type in ['albums', 'all']:
        print('Favorites Albums')
        fmt = '    %13s | %-40s | %-50s | %10s | %10s'
        print_header(fmt, ('#idAlbum', 'Artist', 'Album', 'Tracks', 'Parution'))
        log.info('get all favorites albums...')
        albums = get_user_favorites(user, 'albums', args.raw)
        log.info('... done')
        if args.raw:
            print(json.dumps(albums, indent=4))
        else:
            albums.sort(key=lambda x: x.artist.name)
            for album in albums:
                log.info('display album')
                print(fmt % (album.id,
                             str_max(album.artist.name, 40),
                             str_max(album.title, 50),
                             f'{album.tracks_count} tracks',
                             timestamp_tostring(album.released_at)))
                if args.cover:
                    download_album_image(album)
            log.info('display done')
        print()

    if args.type in ['artists', 'all']:
        print('Favorites Artists')
        fmt = '    %9s | %-40s | %10s'
        print_header(fmt, ('#idArtist', 'Artist', 'Albums'))
        log.info('get all favorites artists...')
        artists = get_user_favorites(user, 'artists', args.raw)
        log.info('... done')
        if args.raw:
            print(json.dumps(artists, indent=4))
        else:
            artists.sort(key=lambda x: x.name)
            for artist in artists:
                log.info('display artist')
                print(fmt % (artist.id, artist.name, artist.albums_count))
        print()


def _read_playlists_file(file_source):
    '''
    Read playlists file
        The playlist file format is similar to the output of command "playlists"
    Return dict of playlist
    '''
    # use regular expressions conform to qobuz_myplaylists output
    re_pldesc = re.compile(r'^Playlist: "(.+)", description: "(.*)", public: (\w+), collaborative: (\w+)')
    re_idtrk = re.compile(r'^ *(\d+)')
    new_playlists = dict()
    playlist_name = None
    for line in file_source.readlines():
        match = re_pldesc.match(line)
        if match:
            playlist_name = match.group(1)
            new_playlists[playlist_name] = {
                'description': match.group(2),
                'public': match.group(3) == 'True',
                'collaborative' :match.group(4) == 'True',
                'tracks': list()
            }
            continue
        match = re_idtrk.match(line)
        if match:
            if not playlist_name:
                print('ERROR : id found without playlist declared')
            new_playlists[playlist_name]['tracks'].append(int(match.group(1)))
    return new_playlists


def qobuz_mod_playlist(user, action, args, log):
    '''
    Modify playlist(s)
    '''
    # read playlist source file
    #
    if args.track_file:
        try:
            fsource = open(args.track_file, encoding='utf8')
        except FileNotFoundError:
            print(f'FAILED: file "{args.track_file}" not found')
            return
    else:
        fsource = sys.stdin
        print('Read source playlist(s) from stdin.')
    new_playlists = _read_playlists_file(fsource)
    log.info('playlist file "%s" loaded', args.track_file)

    # Before creating a playlist we need to check if the name already exists.
    # This avoid to have several playlist with the same name
    # So load our current playlists :
    log.info('get current playlists')
    current_playlists = {p.name.lower():p.id for p in get_user_playlists(user, 'owner')}
    log.info('current playlists : %s', current_playlists)

    # finally modify playlists
    #
    for name, new_playlist in new_playlists.items():
        local_action = action
        log.info('%s tracks for playlist "%s" : %s', local_action, name, new_playlist)
        if name.lower() in current_playlists.keys():
            if local_action == 'add':
                if args.replace:
                    local_action = 'replace'
                    log.info('force "replace" action')
                print(f'Add track(s) to existing playlist "{name}"')
                id_playlist = current_playlists[name.lower()]
            elif local_action == 'del':
                print(f'Delete track(s) to existing playlist "{name}"')
                id_playlist = current_playlists[name.lower()]
        else:
            # create new playlist
            log.info('create new playlist "%s"', name)
            id_playlist = user.playlist_create(name, new_playlist['description'], int(new_playlist['public']), int(new_playlist['collaborative'])).id

        # track ids for current playlist. Warning :
        #   - Playlist.add_tracks uses list of Track.id
        #   - Playlist.del_tracks uses list of Track.playlist_track_id
        log.info('get current tracks for existing playlist')
        playlist_work = qobuz.Playlist.from_id(id_playlist, user)
        current_tracks = {t.id:t.playlist_track_id for t in get_all_tracks(playlist_work)}
        log.info('... done')

        if local_action == 'add':
            # add tracks not already in current playlist
            tracks_to_add = list()
            for track in new_playlist['tracks']:
                if not track in current_tracks:
                    tracks_to_add.append(track)
            print(f'  number of tracks to add : {len(tracks_to_add)}')
            if tracks_to_add:
                log.info('add tracks %s ...', tracks_to_add)
                playlist_work.add_tracks(tracks_to_add, user)
            log.info('... done')

        elif local_action == 'del':
            tracks_to_del = list()
            for track in new_playlist['tracks']:
                if track in current_tracks:
                    # add the playlist_track_id
                    tracks_to_del.append(current_tracks[track])
            print(f'  number of tracks to delete : {len(tracks_to_del)}')
            if tracks_to_del:
                log.info('delete tracks %s ...', tracks_to_del)
                playlist_work.del_tracks(tracks_to_del, user)
            log.info('... done')

        elif local_action == 'replace':
            # prepare tracks to del and tracks to add
            playlist_tracks_to_del = list()
            tracks_to_del = list()
            tracks_to_add = list()
            for track in new_playlist['tracks']:
                if not track in current_tracks:
                    tracks_to_add.append(track)
            for track in current_tracks.keys():
                if not track in new_playlist['tracks']:
                    playlist_tracks_to_del.append(current_tracks[track])
                    tracks_to_del.append(track)
            # do add and delete
            print(f'  {len(tracks_to_add)} tracks to add, {len(playlist_tracks_to_del)} to delete')
            if tracks_to_add:
                log.info('add tracks %s ...', tracks_to_add)
                playlist_work.add_tracks(tracks_to_add, user)
            if tracks_to_del:
                log.info('delete tracks %s ...', tracks_to_del)
                playlist_work.del_tracks(playlist_tracks_to_del, user)
            log.info('... done')



def qobuz_mod_favorites(user, action, args, log):
    '''
    Modify favorites(s)
    '''
    # read favorites source file
    #
    if args.fav_file:
        try:
            fsource = open(args.fav_file[0], encoding='utf8')
            log.info('Favorites %s from "%s"', action, args.fav_file[0])
        except FileNotFoundError:
            print(f'FAILED: file "{args.fav_file[0]}" not found')
            return
    else:
        fsource = sys.stdin
        log.info('Favorites %s from stdin', action)
        print('Read source favorites(s) from stdin.')

    #
    # use regular expression for simple id at the begin of line
    re_section = re.compile(r'^Favorites (\w+)')
    re_idfav = re.compile(r'^ *([\d\w]+)')
    section = None
    favorites = {'Artists':list(), 'Albums':list(), 'Tracks':list()}
    for line in fsource.readlines():
        match = re_section.match(line)
        if match:
            if not match.group(1) in ['Artists', 'Albums', 'Tracks']:
                print(f'ERROR : favorites section unkwown : "{match.group(1)}"')
                return
            section = match.group(1)
            continue
        match = re_idfav.match(line)
        if match:
            if not section:
                print('ERROR : missing favorites section')
            favorites[section].append(match.group(1))
    log.info('Favorites to %s : %s', action, favorites)

    result = False
    if action == 'add':
        result = user.favorites_add(albums=favorites['Albums'], tracks=favorites['Tracks'], artists=favorites['Artists'])
    elif action == 'del':
        result = user.favorites_del(albums=favorites['Albums'], tracks=favorites['Tracks'], artists=favorites['Artists'])
    if result:
        print(f"  Favorites processed : Artists:{len(favorites['Artists'])}, Albums:{len(favorites['Albums'])}, Tracks:{len(favorites['Tracks'])}")
    else:
        print('FAILED')





def main():
    ''' Main program entry '''
    #
    # commands parser
    #
    parser = ArgumentParser(description='Various commands around Qobuz catalog',\
                                     formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--log', help='log on file')

    # create subparsers
    subparsers = parser.add_subparsers(help=': availables commands', dest='command')

    # parser get playlists
    subparser = subparsers.add_parser(
        'playlists',
        description='Retrieves user playlists',
        help=': retrieves and displays user playlists')
    subparser.add_argument('--name', help='Filter playlists on this name')
    subparser.add_argument('--type', choices=['owner', 'subscriber', 'all'], help='Type of playlist : "owner", "subscriber" or "all". (default=%(default)s)', default='owner')
    subparser.add_argument('--sort', action='store_true', help='Sort tracks on "artist" and "album"')
    subparser.add_argument('--performers', action='store_true', help='Displays performers for tracks')
    subparser.add_argument('--no-tracks', action='store_true', help='Don\'t display tracks')
    subparser.add_argument('--raw', action='store_true', help='Displays json structure only')

    # parser add tracks to playlists
    subparser = subparsers.add_parser(
        'playlists-add',
        description="""    Add tracks to playlists from a source file, for one or several playlist.
    If a playlist name doesn't exist, a new playlist is created.
    Source files have the same format as the output of command "playlists". For tracks, only the idTrack are relevant
    Example : adding 2 tracks to playlist "MyJazz" and 1 to "MyRock"
        Playlist: "MyJazz", description: "", public: False, collaborative: False
          13757514
          40071709
        Playlist: "MyRock", description: "", public: False, collaborative: False
          23265470""",
        help=': add tracks to playlist(s) from a source file',
        formatter_class=RawDescriptionHelpFormatter)
    subparser.add_argument('--replace', action='store_true', help='replace playlist if name already exists')
    subparser.add_argument('track_file', nargs='?', help='File source for tracks to add. When empty, source is read from standard input')

    # parser delete tracks from playlists
    subparser = subparsers.add_parser(
        'playlists-del',
        description="""    Delete tracks of playlists from a source file, for one or several playlist

    Source files have the same format as the output of command "playlists". For tracks, only the idTrack are relevant.

    Example : deleting 2 tracks from playlist "MyJazz" and 1 to "MyRock"
        Playlist: "MyJazz", description: "", public: False, collaborative: False
          13757514
          40071709
        Playlist: "MyRock", description: "", public: False, collaborative: False
          23265470""",
        help=': remove tracks from playlist(s) from a source file',
        formatter_class=RawDescriptionHelpFormatter)
    subparser.add_argument('track_file', nargs='?', help='File source for tracks to delete. When empty, source is read from standard input')

    # parser get favorites
    subparser = subparsers.add_parser(
        'favorites',
        description='Retrieves user favorites',
        help=': retrieves and displays user favorites')
    subparser.add_argument('--type', help='Type of favorites to retrieve', \
                    choices=['tracks', 'albums', 'artists', 'all',], default='all')
    subparser.add_argument('--sort', action='store_true', help='Sort tracks on "artist" and "album"')
    subparser.add_argument('--cover', action='store_true', help='Download album cover image. Destination and size is specified in "config.json"')
    subparser.add_argument('--performers', action='store_true', help='Displays performers for tracks')
    subparser.add_argument('--raw', action='store_true', help='Print json structure')

    # parser add favorites
    subparser = subparsers.add_parser(
        'favorites-add',
        description="""    Add favorites artists, albums, tracks from a source file

    Source file has the same format as the output of command "favorites".
    A section ("Favorites Artists", "Favorites Albums", "Favorites Tracks") introduce the favorite type, followed by one id on each line.

    Example : add 1 artist and 2 tracks
        Favorites Artists
            300082
        Favorites Tracks
            6667992
            204465""",
        help=': add favorites',
        formatter_class=RawDescriptionHelpFormatter)
    subparser.add_argument('fav_file', nargs='?', help='File source for favorites to add')

    # parser del favorites
    subparser = subparsers.add_parser(
        'favorites-del',
        description="""    Delete favorites artists, albums, tracks from a source file

    Source file has the same format as the output of command "favorites".
    A section ("Favorites Artists", "Favorites Albums", "Favorites Tracks") introduce the favorite type, followed by one id on each line.

    Example : delete 1 artist and 2 tracks
        Favorites Artists
            300082
        Favorites Tracks
            6667992
            204465""",
        help=': delete favorites',
        formatter_class=RawDescriptionHelpFormatter)
    subparser.add_argument('fav_file', nargs='?', help='File source for favorites to add')

    # parse arguments
    args = parser.parse_args()

    # logging
    if args.log:
        # basicConfig doesn't support utf-8 encoding yet (?)
        #   logging.basicConfig(filename=args.log, level=logging.INFO, encoding='utf-8')
        # use work-around :
        log = logging.getLogger()
        log.setLevel(logging.INFO)
        handler = logging.FileHandler(args.log, 'a', 'utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        log.addHandler(handler)
    log = logging.getLogger()
    log.info('myqobuz start')

    # register qobuz app
    qobuz.api.register_app(MYCONFIG['login']['app_id'], MYCONFIG['login']['app_secret'])

    # prepare qobuz authentification
    log.info('login...')
    user = qobuz.User(MYCONFIG['login']['email'], MYCONFIG['login']['password'])
    log.info('... done')


    if args.command == 'favorites':
        qobuz_myfavorites(user, args, log)

    elif args.command == 'favorites-add':
        qobuz_mod_favorites(user, 'add', args, log)

    elif args.command == 'favorites-del':
        qobuz_mod_favorites(user, 'del', args, log)

    elif args.command == 'playlists':
        qobuz_myplaylists(user, args, log)

    elif args.command == 'playlists-add':
        qobuz_mod_playlist(user, 'add', args, log)

    elif args.command == 'playlists-del':
        qobuz_mod_playlist(user, 'del', args, log)

    # elif args.command == 'playlists-set':
    #     qobuz_mod_playlist(user, 'update', args, log)

    log.info('myqobuz end')



if __name__ == '__main__':
    # protect main from IOError occuring with a pipe command
    try:
        main()
    except IOError as _e:
        if _e.errno not in [22, 32]:
            raise _e
