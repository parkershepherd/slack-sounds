#!/usr/bin/env python
import time
from slackclient import SlackClient
import os, re, traceback

base_dir = os.path.dirname(os.path.realpath(__file__))
config = {}
whitelist = {}
channels = {}
last_played = 0

play_regex = re.compile("^play\s([a-z0-9]+)$")
speak_regex = re.compile("^speak\s([a-zA-Z0-9,'!?\- ]+)$")
play_yt_regex = re.compile("^play-yt\s<?(https?:\/\/[a-z./]*\?v=[a-zA-Z0-9_-]*)>?(\s([0-9.]*)\s([0-9.]*)$)?")
# play-yt <yt video url> <start> <duration> (start and duration are optional)
add_sound_regex = re.compile("^add-sound\s([a-z0-9]+)\s<?(https?:\/\/[a-z./]*\?v=[a-zA-Z0-9_-]*)>?(\s([0-9.]*)\s([0-9.]*)$)?")
# add-sound <token> <yt video url> <start> <duration> (start and duration are optional)

def action(command):
  print ' -> %s\n' % command.replace(base_dir, '')
  os.system(command)


def refresh_whitelist():
  global whitelist
  with open(os.path.join(base_dir, 'config/whitelist.txt')) as f:
    for line in f:
      (name, identifier) = line.split()
      if not identifier in whitelist.keys():
        print "Adding user %s to the whitelist" % name
        whitelist[identifier] = name

f = open(os.path.join(base_dir, 'config/token.txt'))
token = f.readline().rstrip()
f.close()

print "Connecting using token " + token
sc = SlackClient(token)


def refresh_channels():
  global channels
  with open('config/channels.txt') as f:
    new_channels = f.read().splitlines()

  # channel was removed
  for channel_name in channels.values():
    if not channel_name in new_channels:
      print "Removing channel %s from watched list" % channel_name
      channel_id = channels.keys()[channels.values().index(channel_name)];
      del channels[channel_id]

  # channel was added
  for channel_name in new_channels:
    if not channel_name in channels.values():
      print "Adding channel %s to watched list" % channel_name
      channel = sc.server.channels.find(channel_name)
      channels[channel.id] = channel_name


def refresh_config():
  global config
  with open(os.path.join(base_dir, 'config/config.txt')) as f:
    for line in f:
      (key, value) = line.split()
      if not key in config.keys() or not config[key] == value:
        print "Setting %s to %s" % (key, value)
        config[key] = value


def is_valid_message():
  is_message = 'type' in event and event['type'] == 'message'
  has_text = 'text' in event
  has_channel = 'channel' in event
  has_user = 'user' in event or 'bot_id' in event
  has_message = 'text' in event
  is_soundbot = 'soundbot' in event['text'] if has_text else False
  is_valid_message = is_message and has_text and has_channel and has_user and has_message and not is_soundbot
  return is_valid_message


def parse_event():
  is_user = 'user' in event
  user = event['user'] if 'user' in event else event['bot_id']
  message = event['text'].encode('ascii','ignore').strip()
  user_name = whitelist[user] if user in whitelist.keys() else user
  user_name = user_name.encode('ascii','ignore')
  channel_name = channels[event['channel']] if event['channel'] in channels.keys() else event['channel']
  return {
    'text':         message,
    'user_id':      user,
    'user_name':    user_name,
    'channel_id':   event['channel'],
    'channel_name': channel_name,
  }


def show_help():
  print ' -> displaying help message'
  available_sounds = [f for f in os.listdir(config['sounds_dir']) if (
    os.path.isfile(os.path.join(config['sounds_dir'],f)) and 
    ".mp3" in f)]
  available_sounds = [sound.replace('.' + config['filetype'], '') for sound in available_sounds]
  help_message = '\n'.join([
    '*soundbot*: `play <filename>` (or if you\'re slackbot, just `<filename>`). Available sounds:',
    '```', ", ".join(available_sounds), '```',
  ])
  sc.rtm_send_message(message['channel_name'], help_message)


def print_unknown_user():
  print "Unknown user %s says '%s' (@%s)" % (message['user_name'], message['text'], message['channel_name'])


def print_debug_message():
  print "Message from %s: '%s' (@%s)" % (message['user_name'], message['text'], message['channel_name'])


def play_mp3():
  global last_played
  sound_file = os.path.join(base_dir, config['sounds_dir'], play_match.group(1) + '.' + config['filetype'])
  command = '%s "%s"' % (config['player'], sound_file)
  if os.path.isfile(sound_file):
    since_last_played = time.time() - last_played
    if (since_last_played) > int(config['timeout_duration']):
      last_played = time.time()
      action(command)
    else:
      print ' -> rate limit! (%ds remaining)' % (int(config['timeout_duration']) - since_last_played)
      sc.rtm_send_message(message['channel_name'], '*soundbot*: rate limit!')
  else: 
    print ' -> file doesnt exist: %s\n' % sound_file.replace(base_dir, '')


def text_to_speech():
  command = '%s "%s"' % (config['text2voice'], speak_match.group(1))
  action(command)


def play_youtube():
  command = os.path.join(base_dir, 'yt-audio.sh') + ' ' + play_yt_match.group(1)
  if play_yt_match.group(2): command += play_yt_match.group(2)
  action(command)


def download_youtube():
  command = os.path.join(base_dir, 'yt-add-sound.sh') + ' ' + add_sound_match.group(1) + ' ' + add_sound_match.group(2)
  if add_sound_match.group(3): command += add_sound_match.group(3)
  action(command)



# Actual startup loop and event processor
if sc.rtm_connect():
  print "Connected as: %s\n" % sc.server.username
  while True:
    for event in sc.rtm_read():
      try:
        refresh_config()
        refresh_whitelist()
        refresh_channels()
        if not is_valid_message(): continue

        message = parse_event()
        is_allowed_user = message['user_id'] in whitelist.keys()
        is_watched_channel = message['channel_id'] in channels.keys()
        if not is_allowed_user: print_unknown_user()
        if not is_allowed_user or not is_watched_channel: continue
        print_debug_message()

        if message['user_name'] == 'slackbot':
          message['text'] = "play %s" % message['text'] 

        if message['text'] == 'play help':
          show_help()
          continue

        play_match = play_regex.match(message['text'])
        speak_match = speak_regex.match(message['text'])
        play_yt_match = play_yt_regex.match(message['text'])
        add_sound_match = add_sound_regex.match(message['text'])

        if play_match: play_mp3()
        elif speak_match: text_to_speech()
        elif play_yt_match: play_youtube()
        elif add_sound_match: download_youtube()

      except:
        print 'Ignoring an error...'
        traceback.print_exc()

    time.sleep(1);
else:
  print 'Connection failed, invalid token?'
