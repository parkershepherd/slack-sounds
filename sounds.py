import time
from slackclient import SlackClient
import os, re

player = 'mpg123'
text2voice = 'espeak'
sounds_dir = 'sounds'
filetype = 'mp3'
debug = True

play_regex = re.compile("^play\s([a-z]+)$")
speak_regex = re.compile("^speak\s([a-zA-Z0-9,'!?\- ]+)$")
play_yt_regex = re.compile("^play-yt\s<?(https?:\/\/[a-z./]*\?v=[a-zA-Z0-9_-]*)>?(\s([0-9.]*)\s([0-9.]*)$)?")
# lol that above regex matches the pattern:
#     play-yt <yt video url> <start> <duration>
# start and duration are optional
add_sound_regex = re.compile("^add-sound\s([a-z]+)\s<?(https?:\/\/[a-z./]*\?v=[a-zA-Z0-9_-]*)>?(\s([0-9.]*)\s([0-9.]*)$)?")
# lol that above regex matches the pattern:
#     add-sound <token> <yt video url> <start> <duration>
# start and duration are optional

whitelist = {}
with open('whitelist.txt') as f:
    for line in f:
        (name, identifier) = line.split()
        whitelist[identifier] = name

print "Whitelist:"
print whitelist

f = open('token.txt')
token = f.readline().rstrip()
f.close()

print "Connecting using token " + token
sc = SlackClient(token)

if sc.rtm_connect():
    while True:
        for event in sc.rtm_read():
            if 'type' in event and event['type'] == 'message' and 'text' in event and 'user' in event and event['user'] in whitelist.keys():
                if debug: print "Parsing message from " + whitelist[event['user']] + ": '" + event['text'] + "'"
                play_match = play_regex.match(event['text'])
                speak_match = speak_regex.match(event['text'])
                play_yt_match = play_yt_regex.match(event['text'])
                add_sound_match = add_sound_regex.match(event['text'])

                if play_match:
                    print whitelist[event['user']] + ' plays ' + play_match.group(1)
                    command = player + ' ' + sounds_dir + '/' + play_match.group(1) + '.' + filetype
                    if debug: print 'Running command: ' + command
                    os.system(command)
                elif speak_match:
                    print whitelist[event['user']] + ' speaks ' + speak_match.group(1)
                    command = text2voice + ' "' + speak_match.group(1) + '"'
                    if debug: print 'Running command: ' + command
                    os.system(command)
                elif play_yt_match:
                    print whitelist[event['user']] + ' plays youtube video ' + play_yt_match.group(1)
                    command = './yt-audio.sh ' + play_yt_match.group(1)
                    if play_yt_match.group(2): command += play_yt_match.group(2)
                    if debug: print 'Running command: ' + command
                    os.system(command)
                elif add_sound_match:
                    print whitelist[event['user']] + ' adds sound ' + add_sound_match.group(1) + ' from youtube video ' + add_sound_match.group(2)
                    command = './yt-add-sound.sh ' + add_sound_match.group(1) + ' ' + add_sound_match.group(2)
                    if add_sound_match.group(3): command += add_sound_match.group(3)
                    if debug: print 'Running command: ' + command
                    os.system(command)
        time.sleep(1);
else:
    print 'Connection failed, invalid token?'
