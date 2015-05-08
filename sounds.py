import time
from slackclient import SlackClient
import os, re

keyword = 'play'
player = 'mpg123'
sounds_dir = 'sounds'
filetype = 'mp3'

regex = re.compile("^" + keyword + "\s([a-z]+)$")

f = open('token.txt')
token = f.readline().rstrip()

print "Connecting using token " + token
sc = SlackClient(token)

if sc.rtm_connect():
    while True:
        for event in sc.rtm_read():
            if event['type'] == 'message':
                print "Parsing message: '" + event['text'] + "'"
                m = regex.match(event['text'])
                if m:
                    print "Match found: " + m.group(1)
                    command = player + ' ' + sounds_dir + '/' + m.group(1) + '.' + filetype
                    print 'Running command: ' + command
                    os.system(command)
        time.sleep(1);
else:
    print "Connection failed, invalid token?"
