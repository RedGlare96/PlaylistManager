"""
Watcher
Component 4 of 4 in PlaylistManager

Should run every hour
Checks playlist contents and manages placements of priority tracks
"""
import os
import configparser
import pickle
import logging
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


def extract_uris(tracks):
    '''
    Extract uri of tracks
    :param tracks: Raw track data
    :return: List of extracted uris
    '''
    return [ele['track']['uri'] for ele in tracks['items']]


def get_tracks(source):
    '''
    Get all the tracks in the source
    :param source: ID of the source playlist
    :return: List of track uris for the contents of the source playlist
    '''
    track_list = []
    results = sp.playlist(source,
                          fields="tracks,next")
    tracks = results['tracks']
    track_list.extend(extract_uris(tracks))
    while tracks['next']:
        tracks = sp.next(tracks)
        track_list.extend(extract_uris(tracks))
    return track_list


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('masterconfig.ini')
    CLIENT_ID = config['app']['client_id']
    CLIENT_SECRET = config['app']['client_secret']
    scope = config['app']['scope']
    callback = config['app']['callback']
    username = config['user']['username']

    # Init logging
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    consoleHandler = logging.StreamHandler(stdout)
    consoleHandler.setFormatter(logging.Formatter('[%(threadName)s]-[%(name)s] - %(levelname)s - %(message)s'))
    check_create_dir('logs/Watcher')
    fileHandler = logging.FileHandler(
        os.path.join('logs/Watcher', 'Watcher{0}.log'.format(datetime.now().strftime('%d-%m-%y-%H-%M-%S'))))
    fileHandler.setFormatter(logging.Formatter('%(asctime)s:[%(threadName)s]-[%(name)s] - %(levelname)s - %(message)s'))
    consoleHandler.setLevel(logging.INFO)
    rootLogger.addHandler(consoleHandler)
    fileHandler.setLevel(logging.DEBUG)
    rootLogger.addHandler(fileHandler)

    token = util.prompt_for_user_token(username=username,
                                       scope=scope,
                                       client_id=CLIENT_ID,
                                       client_secret=CLIENT_SECRET,
                                       redirect_uri=callback)
    sp = spotipy.Spotify(auth=token)
    user = sp.current_user()['id']
    playlists = sp.current_user_playlists()
    for item in os.listdir('playlist-data'):
        name = item[: item.index('.')]
        with open(os.path.join('playlist-data', item), 'rb') as f:
            data = pickle.load(f)
            f.close()
        new_data = data
        for playlist in playlists['items']:
            if playlist['name'] == name:
                today = datetime.today()
                for i, ele in enumerate(data['priority_entries']):
                    start = datetime.strptime(ele['start'], '%d:%m:%Y')
                    end = datetime.strptime(ele['end'], '%d:%m:%Y')
                    if (today - start).days == 0 and not ele['added']:
                        rootLogger.info('Adding track for the first time')
                        sp.user_playlist_remove_all_occurrences_of_tracks(user=user,
                                                                          playlist_id=playlist['id'],
                                                                          tracks=[ele['track']])
                        sp.user_playlist_add_tracks(user=user, playlist_id=playlist['id'],
                                                    tracks=[ele['track']], position=int(ele['position']))
                        new_data['priority_entries'][i]['added'] = True
                        continue
                    elif (today - end).days >= 1:
                        rootLogger.info('Deleting track from entry')
                        new_data['priority_entries'].remove(ele)
                        continue
                    else:
                        tracks = get_tracks(playlist['id'])
                        if tracks[int(ele['position'])] != 'spotify:track:' + ele['track']:
                            rootLogger.info('Track mismatch')
                            sp.user_playlist_remove_all_occurrences_of_tracks(user=user,
                                                                              playlist_id=playlist['id'],
                                                                              tracks=[ele['track']])
                            sp.user_playlist_add_tracks(user=user, playlist_id=playlist['id'],
                                                        tracks=[ele['track']], position=int(ele['position']))
                with open(os.path.join('playlist-data', playlist['name']) + '.dat', 'wb') as f:
                    pickle.dump(new_data, f)





