#!/usr/bin/env python
import time, os, re, traceback, urllib, urllib2, platform
from slackclient import SlackClient

base_dir = os.path.dirname(os.path.realpath(__file__))
config = {}
whitelist = {}
channels = {}
last_played = 0

play_regex = re.compile("^play\s([a-z0-9/]+)$")
help_regex = re.compile("^play\shelp\s?([a-z0-9/]*)$")
speak_regex = re.compile("^speak\s([a-zA-Z0-9,'!?\- ]+)$")

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


def get_config():
  default_config  = os.path.join(base_dir, 'config/config-default.txt')
  platform_config = os.path.join(base_dir, 'config/config-%s.txt' % platform.system().lower())
  override_config = os.path.join(base_dir, '../slack-sounds-config.txt')
  config_lines = []
  if not os.path.isfile(default_config):
    print 'Failed to load config from ' + default_config
    exit(1)
  with open(default_config) as f:
    for line in f: config_lines.append(line.strip())

  if not os.path.isfile(platform_config):
    print 'Failed to load config from ' + platform_config
    exit(1)
  with open(platform_config) as f:
    for line in f: config_lines.append(line.strip())

  if os.path.isfile(override_config):
    for line in open(override_config):
      config_lines.append(line.strip())

  return config_lines


def refresh_config():
  global config
  new_config = {}
  for line in get_config():
    (key, value) = line.split()
    new_config[key] = value
  for key, value in new_config.items():
    if not key in config.keys() or not config[key] == value:
      print "Setting %s to %s" % (key, value)
      config[key] = value
refresh_config()


print "Connecting using token " + config['slack_token']
sc = SlackClient(config['slack_token'])



def is_valid_message():
  is_message = 'type' in event and event['type'] == 'message'
  has_text = 'text' in event
  has_channel = 'channel' in event
  has_user = 'user' in event or 'bot_id' in event or 'username' in event
  has_message = 'text' in event
  is_valid_message = is_message and has_text and has_channel and has_user and has_message
  return is_valid_message


def parse_event():
  is_user = 'user' in event
  user = event['user'] if 'user' in event else event['bot_id'] if 'bot_id' in event else event['username']
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
  sound_dir = os.path.join(base_dir, config['sounds_dir'], help_match.group(1))
  if not os.path.isdir(sound_dir):
    post_as_slackbot(message['channel_name'], '`%s` does not exist' % sound_dir.replace(base_dir, ''))
    return
  files = [f for f in os.listdir(sound_dir)]
  available_sounds = [f for f in files if (os.path.isfile(os.path.join(sound_dir, f)) and ".mp3" in f)]
  available_folders = [f for f in files if os.path.isdir(os.path.join(sound_dir, f))]
  available_sounds = [sound.replace('.' + config['filetype'], '') for sound in available_sounds]
  sounds_text = '*Available sounds*:\n```' + ", ".join(available_sounds) + '\n```\n'
  folder_text = '*Folders*:\n```' + ", ".join(available_folders) + '\n```' if available_folders else ''
  help_message = '\n'.join([
    '`play <filename>` (or if you\'re slackbot, just `<filename>`). For help: `play help` or `play help <folder>`',
    sounds_text + folder_text
  ])
  post_as_slackbot(message['channel_name'], help_message)


def print_unknown_user():
  print "Unknown user %s says '%s' (@%s)" % (message['user_name'], message['text'], message['channel_name'])


def print_debug_message():
  print "Message from %s: '%s' (@%s)" % (message['user_name'], message['text'], message['channel_name'])


def post_as_slackbot(channel, message):
  if config['post_as_slackbot'] == 'true':
    url = 'https://' + config['org_name'] + '.slack.com/services/hooks/slackbot?token=' + config['slackbot_token'] + '&channel=' + channel
    req = urllib2.Request(url, message)
    response = urllib2.urlopen(req)
  else:
    print ' -> posting as slackbot disabled'

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
      limit_message = 'rate limit! (%ds remaining)' % (int(config['timeout_duration']) - since_last_played)
      print ' -> ' + limit_message
      post_as_slackbot(message['channel_name'], 'soundbot ' + limit_message)
  else:
    print ' -> file doesnt exist: %s\n' % sound_file.replace(base_dir, '')


def text_to_speech():
  command = '%s "%s"' % (config['text2voice'], speak_match.group(1))
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
        if not is_watched_channel: continue
        if not is_allowed_user:
          print_unknown_user()
          continue
          
        if message['user_name'] == 'slackbot' and len(message['text']) > 20:
          continue

        print_debug_message()

        if message['user_name'] == 'slackbot':
          message['text'] = "play %s" % message['text'] 


        help_match = help_regex.match(message['text'])
        play_match = play_regex.match(message['text'])
        speak_match = speak_regex.match(message['text'])

        if help_match: show_help()
        elif play_match: play_mp3()
        elif speak_match: text_to_speech()

      except:
        print 'Ignoring an error...'
        traceback.print_exc()

    time.sleep(float(config['sync_interval']));
else:
  print 'Connection failed, invalid token?'
