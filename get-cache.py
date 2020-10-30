import configparser
import spotipy.util as util


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('masterconfig.ini')
    CLIENT_ID = config['app']['client_id']
    CLIENT_SECRET = config['app']['client_secret']
    scope = config['app']['scope']
    callback = config['app']['callback']
    username = config['user']['username']

    token = util.prompt_for_user_token(username=username,
                                       scope=scope,
                                       client_id=CLIENT_ID,
                                       client_secret=CLIENT_SECRET,
                                       redirect_uri=callback)
    print('Success! Current token for the next 1 hour is: {}'.format(token))