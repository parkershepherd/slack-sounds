#!/usr/bin/env python
import time
from slackclient import SlackClient
import os, re

base_dir = os.path.dirname(os.path.realpath(__file__))

player = 'mpg123'
text2voice = 'espeak'
sounds_dir = 'sounds'
filetype = 'mp3'
debug = True
bots_channel = 'wcms-bots'

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

def action(command, message):
    global debug
    global sc
    global bots_channel

    print message
    print bots_channel
    sc.rtm_send_message(bots_channel, message)
    if debug: print 'Running command: ' + command
    os.system(command)

whitelist = {}
with open(os.path.join(base_dir, 'whitelist.txt')) as f:
    for line in f:
        (name, identifier) = line.split()
        whitelist[identifier] = name

print "Whitelist:"
print whitelist

f = open(os.path.join(base_dir, 'token.txt'))
token = f.readline().rstrip()
f.close()

print "Connecting using token " + token
sc = SlackClient(token)

if sc.rtm_connect():
    while True:
        for event in sc.rtm_read():
            if 'type' in event and event['type'] == 'message' and 'text' in event:
                if ('user' in event and event['user'] in whitelist.keys()):
                    user = whitelist[event['user']]
                elif ('subtype' in event and event['subtype'] == 'bot_message' and 'bot_id' in event and event['bot_id'] in whitelist.keys()):
                    user = whitelist[event['bot_id']]
                else:
                    user = False
                if user:
                    if debug: print "Parsing message from " + user + ": '" + event['text'] + "'"
                    play_match = play_regex.match(event['text'])
                    speak_match = speak_regex.match(event['text'])
                    play_yt_match = play_yt_regex.match(event['text'])
                    add_sound_match = add_sound_regex.match(event['text'])

                    if play_match:
                        message = user + ' plays ' + play_match.group(1)
                        sound_file = os.path.join(base_dir, sounds_dir, play_match.group(1) + '.' + filetype)
                        command = player + ' ' + sound_file
                        action(command, message)
                    elif speak_match:
                        message = user + ' speaks ' + speak_match.group(1)
                        command = text2voice + ' "' + speak_match.group(1) + '"'
                        action(command, message)
                    elif play_yt_match:
                        message = user + ' plays youtube video ' + play_yt_match.group(1)
                        command = os.path.join(base_dir, 'yt-audio.sh') + ' ' + play_yt_match.group(1)
                        if play_yt_match.group(2): command += play_yt_match.group(2)
                        action(command, message)
                    elif add_sound_match:
                        message = user + ' adds sound ' + add_sound_match.group(1) + ' from youtube video ' + add_sound_match.group(2)
                        command = os.path.join(base_dir, 'yt-add-sound.sh') + ' ' + add_sound_match.group(1) + ' ' + add_sound_match.group(2)
                        if add_sound_match.group(3): command += add_sound_match.group(3)
                        action(command, message)
        time.sleep(1);
else:
    print 'Connection failed, invalid token?'
