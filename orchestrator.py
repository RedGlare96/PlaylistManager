"""
Orchestrator
Component 3 of 4 in PlaylistManager

Runs at scheduled time
Gets access to Spotify and creates playlist
Populates playlist with random tracks from source playlist
If already exists, replaces playlist
"""
import os
import configparser
import argparse
import logging
import random
import json
import pickle
from datetime import datetime
from sys import stdout
import spotipy
import spotipy.util as util


def check_create_dir(dirname):
    '''
    Checks if directory exists and if it doesn't creates a new directory
    :param dirname: Path to directory
    '''
    if not os.path.exists(dirname):
        if '/' in dirname:
            os.makedirs(dirname)
        else:
            os.mkdir(dirname)


def extract_uris(raw_pls):
    '''
    Extract uris of playlists
    :param raw_pls: Raw playlist data
    :return: List of extracted uris
    '''
    ret = []
    for pl in raw_pls['items']:
        ret.append(pl['track']['uri'])
    return ret


def get_random_tracks(source, max_tracks):
    '''
    Choose random tracks from source playlist
    :param source: ID of source playlist
    :param max_tracks: The maximum amount of random tracks to get
    :return: List with random tracks
    '''
    track_list = []
    results = sp.playlist(source,
                          fields="tracks,next")
    tracks = results['tracks']
    track_list.extend(extract_uris(tracks))
    while tracks['next']:
        tracks = sp.next(tracks)
        track_list.extend(extract_uris(tracks))
    pl_len = len(track_list)
    if pl_len < max_tracks:
        max_tracks = pl_len
    return random.sample(track_list, max_tracks)


if __name__ == '__main__':
    print('Orchestrator')
    parser = argparse.ArgumentParser(description='Creates or replaces new playlists')
    parser.add_argument('data', type=str)
    args = parser.parse_args()
    data = json.loads(args.data.replace("'", '"'))
    config = configparser.ConfigParser()

    # Init logging
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    consoleHandler = logging.StreamHandler(stdout)
    consoleHandler.setFormatter(logging.Formatter('[%(threadName)s]-[%(name)s] - %(levelname)s - %(message)s'))
    check_create_dir('logs/Orchestrator')
    fileHandler = logging.FileHandler(
        os.path.join('logs/Orchestrator', 'Orchestrator{0}.log'.format(datetime.now().strftime('%d-%m-%y-%H-%M-%S'))))
    fileHandler.setFormatter(logging.Formatter('%(asctime)s:[%(threadName)s]-[%(name)s] - %(levelname)s - %(message)s'))
    consoleHandler.setLevel(logging.INFO)
    rootLogger.addHandler(consoleHandler)
    fileHandler.setLevel(logging.DEBUG)
    rootLogger.addHandler(fileHandler)

    rootLogger.debug('Looking for config...')
    config.read('masterconfig.ini')
    CLIENT_ID = config['app']['client_id']
    CLIENT_SECRET = config['app']['client_secret']
    scope = config['app']['scope']
    callback = config['app']['callback']
    username = config['user']['username']
    max_tracks = int(config['orchestrator']['max_tracks'])

    token = util.prompt_for_user_token(username=username,
                                       scope=scope,
                                       client_id=CLIENT_ID,
                                       client_secret=CLIENT_SECRET,
                                       redirect_uri=callback)
    sp = spotipy.Spotify(auth=token)
    target_pl = data['target']
    source_pl = data['source']
    exists = False
    playlists = sp.current_user_playlists()
    new_pl = None
    for playlist in playlists['items']:
        if target_pl == playlist['name']:
            rootLogger.info('Found existing playlist')
            exists = True
            sp.user_playlist_replace_tracks(user=sp.current_user()['id'], playlist_id=playlist['id'],
                                            tracks=get_random_tracks(source_pl, max_tracks))
            new_pl = playlist
            break
    if not exists:
        rootLogger.info('Creating new playlist')
        new_pl = sp.user_playlist_create(user=sp.current_user()['id'], name=target_pl,
                                         description='Managed by PlaylistManager')
        sp.user_playlist_add_tracks(user=sp.current_user()['id'], playlist_id=new_pl['id'],
                                    tracks=get_random_tracks(source_pl, max_tracks))
    if new_pl is not None:
        data['playlist_id'] = new_pl['id']
        if exists:
            # If playlist already exists, carry over priority data from previous entry
            with open(os.path.join('playlist-data', '{}.dat'.format(target_pl)), 'rb') as f:
                prev_data = pickle.load(f)
                data['priority_entries'] = prev_data['priority_entries']
        check_create_dir('playlist-data')
        with open(os.path.join('playlist-data', '{}.dat'.format(target_pl)), 'wb') as f:
            pickle.dump(data, f)

