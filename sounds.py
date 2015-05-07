import time
from slackclient import SlackClient
import os, re

keyword = 'play'
player = 'mpg123'
sounds_dir = 'sounds'
filetype = 'mp3'

regex = re.compile("^" + keyword + "\s([a-z]+)$")

f = open('token.txt')
token = f.readline()

sc = SlackClient(token)

if sc.rtm_connect():
    while True:
        for event in sc.rtm_read():
            if event['type'] == 'message':
                m = regex.match(event['text'])
                if m:
                    os.system(player + ' ' + sounds_dir + '/' + m.group(1) + '.' + filetype)
        time.sleep(1);
else:
    print "Connection failed, invalid token?"

