"""
Oracle
Debug script to check contents of playlist-data
"""
import argparse
import pickle
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates or replaces new playlists')
    parser.add_argument('playlist', type=str)
    args = parser.parse_args(['newtest22'])
    playlist = args.playlist
    with open(os.path.join('playlist-data', playlist + '.dat'), 'rb') as f:
        data = pickle.load(f)
    print(data)