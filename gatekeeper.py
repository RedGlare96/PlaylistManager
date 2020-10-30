"""
Gatekeeper
Component 1 of 4 in PlaylistManager

Controls and hosts the web interface
"""
import os
import json
import pickle
import socket
import time
from threading import Thread
from datetime import datetime
from configparser import ConfigParser
from os import path
from flask import Flask, url_for, redirect, request, render_template
from jinja2 import Environment, FileSystemLoader

app = Flask(__name__, template_folder=os.getcwd() + '/templates')
jenv = Environment(loader=FileSystemLoader(os.getcwd()), trim_blocks=True)


def send_to_listener(datadict):
    '''
    Package and send to listener
    :param datadict: Dictionary with data
    '''
    data = json.dumps(datadict)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(data.encode())
    except ConnectionRefusedError:
        print('Connection error')


def send_heartbeat():
    data = 'ACK'
    later = time.clock()
    while True:
        now = time.clock()
        if int(now - later) >= 10:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((HOST, PORT))
                    s.sendall(data.encode())
            except ConnectionError:
                print('Heartbeat error: Cannot connect to listener. Make sure it is running')
            later = now


@app.route('/index')
def index():
    return render_template('dashboard.html')


@app.route('/createplaylist')
def create_playlist():
    return render_template('playlistform.html')


@app.route('/createpriority/<playlist>')
def create_priority(playlist):
    return render_template('priorityform.html', type='new', playlist=playlist, namevalue=0, idvalue=0, positionvalue=0,
                           start=0, end=0)


@app.route('/deleteplaylist/<id>')
def delete_playlist(id):
    try:
        os.remove(id + '.dat')
    except OSError:
        print('Cannot find file')
    return redirect(url_for('show_playlist'))


@app.route('/deletepriority/<id>')
def delete_priority(id):
    playlistname = id.split(':')[0]
    trackname = id.split(':')[-1]
    for item in os.listdir('playlist-data'):
        if playlistname == item.split('.')[0]:
            with open(path.join('playlist-data', item), 'rb') as f:
                raw_data = pickle.load(f)
            for ele in raw_data['priority_entries']:
                if trackname == ele['name']:
                    raw_data['priority_entries'].remove(ele)
                    with open(path.join('playlist-data', item), 'wb') as f:
                        pickle.dump(raw_data, f)
    return redirect('/priority/{}'.format(playlistname))


@app.route('/editpriority/<id>')
def edit_priority(id):
    playlistname = id.split(':')[0]
    trackname = id.split(':')[-1]
    for item in os.listdir('playlist-data'):
        if playlistname == item.split('.')[0]:
            with open(path.join('playlist-data', item), 'rb') as f:
                raw_data = pickle.load(f)
            for ele in raw_data['priority_entries']:
                if trackname == ele['name']:
                    return render_template('priorityform.html', type='edit', playlist=playlistname, namevalue=ele['name'],
                                           idvalue=ele['track'], positionvalue=ele['position'], start=ele['start'],
                                           end=ele['end'])
            return render_template('priorityform.html', playlist='Cannot find entry', type='edit')
    return render_template('priorityform.html', playlist='Cannot find playlist', type='edit')


@app.route('/listplaylist')
def list_playlist():
    itemlist = [(ele.split('.')[0], ele.split('.')[0]) for ele in os.listdir('playlist-data')]
    return render_template('listview.html', directlink='playlist',
                           itemlist=itemlist, listlen=len(itemlist), identifier='Current playlists',
                           endbutton=False)


@app.route('/playlist/<name>')
def show_playlist(name):
    for item in os.listdir('playlist-data'):
        if name == item.split('.')[0]:
            with open(path.join('playlist-data', item), 'rb') as f:
                data = pickle.load(f)
            del data['priority_entries']
            return render_template('dataview.html', identifier='Playlist data', empty=False,
                                   data=data, button={'link': '/priority/' + name, 'text': 'View priority tracks'},
                                   delete='/deleteplaylist/{}'.format(name))
    return render_template('dataview.html',
                           empty=True, button={'link': '/priority/' + name, 'text': 'View priority tracks'},
                           delete='/deleteplaylist/{}'.format(name))


@app.route('/priority/<name>')
def list_priority(name):
    for item in os.listdir('playlist-data'):
        if name == item.split('.')[0]:
            with open(path.join('playlist-data', item), 'rb') as f:
                data = pickle.load(f)
            itemlist = [(name + ':' + ele['name'], ele['name']) for ele in data['priority_entries']]
            return render_template('listview.html', itemlist=itemlist, listlen=len(itemlist),
                                   identifier='Priority tracks for {}'.format(name), directlink='priorityentry',
                                   endbutton=True, button={'link': '/createpriority/' + name, 'text': 'Create new track'})
    return render_template('listiew.html', listlen=0, identifier='Priority tracks for {}'.format(name),
                           endbutton=True, button={'link': '/createpriority/' + name, 'text': 'Create new track'})


@app.route('/priority/priorityentry/<id>')
def show_priority(id):
    playlistname = id.split(':')[0]
    trackname = id.split(':')[1]
    print('trackname = {}'.format(trackname))
    print('trackname type = {}'.format(type(trackname)))
    print('trackname size = {}'.format(len(trackname)))
    for item in os.listdir('playlist-data'):
        if playlistname == item.split('.')[0]:
            with open(path.join('playlist-data', item), 'rb') as f:
                raw_data = pickle.load(f)
            for ele in raw_data['priority_entries']:
                print('got in')
                print('ele-name = {}'.format(ele['name']))
                print('ele-name type = {}'.format(type(ele['name'])))
                print('ele-name size = {}'.format(len(ele['name'])))
                if trackname == ele['name']:
                    print('Got in 2')
                    data = ele
                    return render_template('dataview.html', identifier='Priority track', empty=False, data=data,
                                           button={'link': '/editpriority/' + id, 'text': 'Edit entry'},
                                           deletelink='/deletepriority/{}'.format(id))
            return render_template('dataview.html', empty=True, button={'link': '/editpriority/' + id, 'text': 'Edit entry'},
                                   deletelink='/deletepriority/{}'.format(id))
    return render_template('dataview.html', empty=True, button={'link': '/editpriority/' + id, 'text': 'Edit entry'},
                           deletelink='/deletepriority/{}'.format(id))


@app.route('/form1', methods=["GET", "POST"])
def form1():
    target = request.form['element_1']
    source = request.form['element_2'].split('/')[-1]
    hours = int(request.form['element_4_1']) if request.form['element_4_4'] == 'AM'\
        else int(request.form['element_4_1']) + 12
    schedeule = datetime(day=int(request.form['element_3_1']), month=int(request.form['element_3_2']),
                         year=int(request.form['element_3_3']), hour=hours,
                         minute=int(request.form['element_4_2']))
    orch_data = {'target': target, 'source': source, 'priority_entries': []}
    ret = {'start_str': schedeule.strftime('%H:%M:%d:%m:%Y'), 'orch_data': orch_data}
    send_to_listener(ret)
    return redirect(url_for('index'))


@app.route('/form2/<type>', methods=["GET", "POST"])
def form2(type):
    dat = request.form
    playlistname = dat['element_5']
    entryname = dat['element_6'].strip()
    entryid = dat['element_1'].split('/')[-1]
    print(type)
    if type == 'new':
        position = int(dat['element_2']) - 1
    else:
        position = int(dat['element_2'])
    start = datetime(day=int(dat['element_3_1']), month=int(dat['element_3_2']),
                     year=int(dat['element_3_3']))
    end = datetime(day=int(dat['element_4_1']), month=int(dat['element_4_2']),
                   year=int(dat['element_4_3']))
    new_entry = {'name': entryname, 'track': entryid, 'position': position,
                 'start': start.strftime('%d:%m:%Y'), 'end': end.strftime('%d:%m:%Y'), 'added': False}
    for item in os.listdir('playlist-data'):
        if playlistname == item.split('.')[0]:
            with open(path.join('playlist-data', item), 'rb') as f:
                raw_data = pickle.load(f)
            old_index = -1
            for i, ele in enumerate(raw_data['priority_entries']):
                if new_entry['name'] == ele['name']:
                    old_index = i
            if old_index >= 0:
                print('edit entry')
                raw_data['priority_entries'][old_index] = new_entry
            else:
                print('new entry')
                raw_data['priority_entries'].append(new_entry)
            with open(path.join('playlist-data', item), 'wb') as f:
                pickle.dump(raw_data, f)
            print('Entry added')
            print(new_entry)
            return redirect('/priority/{}'.format(playlistname))
    print('Could not find playlist')
    return redirect('/priority/{}'.format(playlistname))


@app.route('/')
def login():
    return redirect(url_for('index'))


@app.route('/antechamber/<password>', methods=['GET', 'POST'])
def secret_shutdown(password):
    if password == 'overrideroberthouse':
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        return 'Override accepted.\nWelcome Mr House.\nShutting down now...'
    else:
        return redirect(url_for('index'))


if __name__ == '__main__':
    config = ConfigParser()
    config.read('masterconfig.ini')
    webhost = config['gatekeeper']['host']
    webport = int(config['gatekeeper']['port'])
    HOST = config['listener']['host']
    PORT = int(config['listener']['port'])
    print('Starting heartbeat')
    heartbeat_thread = Thread(name='heartbeat', target=send_heartbeat).start()
    app.run(host=webhost, port=webport, threaded=True)