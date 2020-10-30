"""
Listener
Component 2 of 4 in PlaylistManager

Should always be running the background.
Receives messages from the gatekeeper about new playlists.
Schedules tasks with the Orchestrator
"""
import os
import socket
import json
import logging
import subprocess
from configparser import ConfigParser
from datetime import datetime
from os import mkdir, makedirs
from sys import stdout
import schedule


def check_create_dir(dirname):
    '''
    Checks if directory exists and if it doesn't creates a new directory
    :param dirname: Path to directory
    '''
    if not os.path.exists(dirname):
        if '/' in dirname:
            makedirs(dirname)
        else:
            mkdir(dirname)


def run_orchestrator(json_data):
    logger = logging.getLogger(__name__ + '.run_orchestrator')
    logger.info('Task triggered')
    subprocess.run(['python', 'orchestrator.py', json_data.replace('"', "'")])
    return schedule.CancelJob


if __name__ == '__main__':
    print('Listener')
    config = ConfigParser()
    config.read('masterconfig.ini')
    HOST = config['listener']['host']
    PORT = int(config['listener']['port'])
    TASK_LIMIT = config['listener']['task_limit']

    # Init logging
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    consoleHandler = logging.StreamHandler(stdout)
    consoleHandler.setFormatter(logging.Formatter('[%(threadName)s]-[%(name)s] - %(levelname)s - %(message)s'))
    check_create_dir('logs/Listener')
    fileHandler = logging.FileHandler(
        os.path.join('logs/Listener', 'Listener{0}.log'.format(datetime.now().strftime('%d-%m-%y-%H-%M-%S'))))
    fileHandler.setFormatter(logging.Formatter('%(asctime)s:[%(threadName)s]-[%(name)s] - %(levelname)s - %(message)s'))
    consoleHandler.setLevel(logging.INFO)
    rootLogger.addHandler(consoleHandler)
    fileHandler.setLevel(logging.DEBUG)
    rootLogger.addHandler(fileHandler)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        stop = False
        while not stop:
            schedule.run_pending()
            rootLogger.debug('Listening on 3000')
            s.listen()
            conn, addr = s.accept()
            with conn:
                rootLogger.info('Connected by {}'.format(addr))
                while True:
                    raw_data = conn.recv(1024)
                    if not raw_data:
                        break
                    decoded_data = raw_data.decode()
                    if decoded_data == 'ACK':
                        rootLogger.info('Heartbeat acknowledged')
                        break
                    data = json.loads(decoded_data)
                    print(data)
                    stopexe = data.get('stop', False)
                    if stopexe:
                        rootLogger.info('Stop message received')
                        stop = True
                    else:
                        rootLogger.debug('Data recieved')
                        if os.path.exists('task-counter.txt'):
                            with open('task-counter.txt', 'r') as f:
                                cnt = int(f.read())
                            cnt = cnt + 1 if (cnt + 1) < int(TASK_LIMIT) else 0
                        else:
                            cnt = 0
                        with open('task-counter.txt', 'w') as f:
                            f.write(str(cnt))
                        rootLogger.debug('Adding task')
                        run_time = datetime.strptime(data['start_str'], '%H:%M:%d:%m:%Y')
                        days_interval = (run_time - datetime.today()).days
                        if days_interval == 0:
                            schedule.every().day \
                                .at(run_time.strftime('%H:%M')) \
                                .do(run_orchestrator, json.dumps(data['orch_data']))
                        elif days_interval < 0:
                            rootLogger.error('Invalid data entered')
                        else:
                            schedule.every(days_interval).days \
                                .at(run_time.strftime('%H:%M')) \
                                .do(run_orchestrator, json.dumps(data['orch_data']))