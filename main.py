#!/usr/bin/python3

try:
    from configparser import ConfigParser
    import requests
    import json
    import time
except Exception as e:
    print(e)
    exit(1)

def loadConfig(config_obj={}, config_file='config.ini'):
    cparser = ConfigParser()
    cparser.read(config_file)

    config_sections = cparser.sections()
    for section in config_sections:
        section_obj = {}
        config_obj[section] = section_obj
        for key in cparser[section].keys():
            section_obj[key] = cparser[section][key]

    if 'app' not in config_obj:
        config_obj['app'] = {}

    if config_obj['app'].get('sleeptime') is None:
        config_obj['app']['sleeptime'] = 60.0
    else:
        config_obj['app']['sleeptime'] = float(config_obj['app']['sleeptime'])

    if config_obj['app'].get('twitch_notify_already_live_streams') is None:
        config_obj['app']['twitch_notify_already_live_streams'] = False
    else:
        config_obj['app']['twitch_notify_already_live_streams'] = bool(config_obj['app']['twitch_notify_already_live_streams'])

    return config_obj


def sendSlackMessage(msg):
    payload = {
        'text': msg,
        'username': 'bonbonbot',
        'channel': '#general'
    }

    print(json.dumps(payload))
    res = requests.post(global_config['slack']['webhook'], data=json.dumps(payload))
    print(res.status_code)
    print(res.text)

def twitchJob():
    def getLiveStreams():
        streams = {}
        res = requests.get('https://api.twitch.tv/kraken/streams/?client_id=' + global_config['twitch']['clientid']  +  '&channel=' + global_config['twitch']['streams'])
        json = res.json()

        if 'streams' not in json:
            return streams

        for stream in json['streams']:
            channel = stream['channel']
            streams[channel['name']] = {
                'name': channel['name'],
                'display_name': channel['display_name'],
                'status': channel['status'],
                'game': channel['game']
            }

        return streams

    def generateStreamDiff(current, past):
        current_keys = set(current.keys())
        past_keys = set(past.keys())

        return list(current_keys - (current_keys.intersection(past_keys)))

    def notifyOnNewStreams(new_streams):
        for stream_name in new_streams:
            stream = live_twitch_streams[stream_name]
            sendSlackMessage(':red_circle: NOW LIVE: <https://www.twitch.tv/' + stream['name'] + '|twitch.tv/' + stream['name'] + '>\n' +
                    stream['status'] + '\n' + stream['display_name'] + ' is playing ' + stream['game'])

    global live_twitch_streams
    current_streams = getLiveStreams()

    if live_twitch_streams is None and  global_config['app']['twitch_notify_already_live_streams']:
        live_twitch_streams = {}

    if live_twitch_streams is None:
        live_twitch_streams = current_streams
    else:
        new_streams = generateStreamDiff(current_streams, live_twitch_streams)
        live_twitch_streams = current_streams
        notifyOnNewStreams(new_streams)
    print(current_streams)

def doJobs():
    twitchJob()

start_time = time.time()
global_config = loadConfig()

'''
Job-specific data storage - if I were actually practicing proper OOP, there
 would be no need for this!
'''
live_twitch_streams = None

while True:
    doJobs()
    time.sleep(global_config['app']['sleeptime'] - ((time.time() - start_time) % global_config['app']['sleeptime']))
