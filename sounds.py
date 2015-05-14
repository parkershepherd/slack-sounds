import time
from slackclient import SlackClient
import os, re

player = 'mpg123'
text2voice = 'espeak'
sounds_dir = 'sounds'
filetype = 'mp3'

play_regex = re.compile("^play\s([a-z]+)$")
speak_regex = re.compile("^speak\s([a-z ]+)$")
play_yt_regex = re.compile("^play-yt\s<?(https?:\/\/[a-z./]*\?v=[a-zA-Z0-9_-]*)>?(\s([0-9.]*)\s([0-9.]*)$)?")
# lol that above regex matches the pattern:
#     play-yt <yt video url> <start> <duration>
# start and duration are optional

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
                play_yt_match = play_yt_regex.match(event['text'])
                if play_match:
                    print play_match.group(0)
                    print 'Play match found: ' + play_match.group(1)
                    command = player + ' ' + sounds_dir + '/' + play_match.group(1) + '.' + filetype
                    print 'Running command: ' + command
                    os.system(command)
                if speak_match:
                    print 'Speak match found: ' + speak_match.group(1)
                    command = text2voice + ' "' + speak_match.group(1) + '"'
                    print 'Running command: ' + command
                    os.system(command)
                if play_yt_match:
                    print 'Play yt match found:'
                    command = './yt-audio.sh ' + play_yt_match.group(1) + play_yt_match.group(2)
                    print 'Running command: ' + command
                    os.system(command)
        time.sleep(1);
else:
    print 'Connection failed, invalid token?'
