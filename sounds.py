import time
from slackclient import SlackClient
import os, re

player = 'mpg123'
text2voice = 'espeak'
sounds_dir = 'sounds'
filetype = 'mp3'

play_regex = re.compile("^play\s([a-z]+)$")
speak_regex = re.compile("^speak\s([a-z ]+)$")

f = open('token.txt')
token = f.readline().rstrip()

print "Connecting using token " + token
sc = SlackClient(token)

if sc.rtm_connect():
    while True:
        for event in sc.rtm_read():
            if event['type'] == 'message' and 'text' in event:
                print "Parsing message: '" + event['text'] + "'"
                play_match = play_regex.match(event['text'])
                speak_match = speak_regex.match(event['text'])
                if play_match:
                    print play_match.group(0)
                    print "Play match found: " + play_match.group(1)
                    command = player + ' ' + sounds_dir + '/' + play_match.group(1) + '.' + filetype
                    print 'Running command: ' + command
                    os.system(command)
                if speak_match:
                    print "Speak match found: " + speak_match.group(1)
                    command = text2voice + ' "' + speak_match.group(1) + '"'
                    print 'Running command: ' + command
                    os.system(command)
        time.sleep(1);
else:
    print "Connection failed, invalid token?"
