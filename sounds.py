#!/usr/bin/env python
import time, os, sys, re, traceback, urllib, urllib2, platform, random
from glob import glob
from slackclient import SlackClient
from os.path import getmtime

original_mtime = getmtime(__file__)
base_dir = os.path.dirname(os.path.realpath(__file__))
config = {}
whitelist = {}
channels = {}
last_played = 0

play_regex = re.compile("^play\s([a-z0-9/]+)( \(.*\))?$")
help_regex = re.compile("^play\shelp\s?([a-z0-9/]*)$")
list_regex = re.compile("^play\slist\s?([a-z0-9/]*)$")
search_regex = re.compile("^play\ssearch\s?([a-z0-9/]*)$")
speak_regex = re.compile("^speak\s([a-zA-Z0-9,'!?\- ]+)$")

def action(command):
  print ' -> %s' % command.replace(base_dir, '')
  os.system(command)


def check_if_code_changed():
  if getmtime(__file__) != original_mtime:
    file = os.path.join(base_dir, __file__)
    print ''
    print __file__ + ' changed, restarting!'
    print ''
    os.execv(file, sys.argv)


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
  file_term = help_match.group(1) if help_match.group(1) else '<filename>'
  folder_term = help_match.group(1) if help_match.group(1) else '<folder>'

  play_help = '*Play a sound*: `play %s` (or if you\'re slackbot, just `%s`)' % (file_term, file_term)
  list_help = '*List sounds*: `play list` or `play list %s`' % folder_term
  search_help = '*Search sounds*: `play search %s`' % file_term
  help_message = '\n'.join([play_help, list_help, search_help])
  print ' -> displaying help message'
  post_as_slackbot(message['channel_name'], help_message)

def show_list():
  print ' -> displaying sound list'
  sound_dir = os.path.join(base_dir, config['sounds_dir'], list_match.group(1))
  if not os.path.isdir(sound_dir):
    post_as_slackbot(message['channel_name'], '`%s` does not exist' % sound_dir.replace(base_dir, ''))
    return
  files = [f for f in os.listdir(sound_dir)]
  available_sounds = [f for f in files if (os.path.isfile(os.path.join(sound_dir, f)) and '.%s' % config['filetype'] in f)]
  available_folders = [f for f in files if os.path.isdir(os.path.join(sound_dir, f))]
  available_sounds = [sound.replace('.' + config['filetype'], '') for sound in available_sounds]
  sounds_text = '*Available sounds*:\n```' + ", ".join(available_sounds) + '\n```\n'
  folder_text = '*Folders*:\n```' + ", ".join(available_folders) + '\n```' if available_folders else ''
  help_message = '\n'.join([
    sounds_text + folder_text
  ])
  post_as_slackbot(message['channel_name'], help_message)


def search_sounds(search_term):
  if not search_term or len(search_term) < 3:
    return []

  sound_dir = os.path.join(base_dir, config['sounds_dir'])
  matches = [match for file in os.walk(sound_dir) for match in glob(os.path.join(file[0], '*%s*' % search_term)) if os.path.isfile(match)]
  matches = [match.replace('\\', '/').replace('%s/' % sound_dir.replace('\\', '/'), '').replace('.%s' % config['filetype'], '') for match in matches]
  return matches


def show_search(search_term=None):
  search_term = search_term if search_term != None else search_match.group(1)

  if not search_term:
    print ' -> missing search term!'
    post_as_slackbot(message['channel_name'], 'you must provide a search term')
    return

  if len(search_term) < 3:
    print ' -> search text too short!'
    post_as_slackbot(message['channel_name'], 'could you be a bit more specific than just `%s`?' % search_term)
    return

  sound_dir = os.path.join(base_dir, config['sounds_dir'])
  matches = search_sounds(search_term)
  print ' -> found %d sounds similar to "%s"' % (len(matches), search_term)
  print ' -> results: %s' % (', '.join(matches) if matches else ' - none -')
  if matches:
    results_text = '\n'.join(matches)
    search_message = '\n'.join([
      '*Search results for*: `%s`' % search_term,
      '```',
      results_text,
      '```'
    ])
    post_as_slackbot(message['channel_name'], search_message)
  elif message['channel_name'] == config['main_channel']:
    messages = [
      'thanks for sending me on a wild goose chase for "{search_term}"!',
      'yeah, "{search_term}" doesn\'t exist',
      '"{search_term}" is nowhere to be found',
      'did you really expect "{search_term}" to exist?',
      'is "{search_term}" missing, or are you just bad at spelling?',
    ]
    post_as_slackbot(message['channel_name'], random.choice(messages).format(search_term=search_term))
  else:
    post_as_slackbot(message['channel_name'], "couldn\'t find {search_term}".format(search_term=search_term))


def print_unknown_user():
  if message['user_name'] != config['slackbot_name']:
    print "Unknown user %s says '%s' (@%s)" % (message['user_name'], message['text'], message['channel_name'])


def print_debug_message():
  print "Message from %s: '%s' (@%s)" % (message['user_name'], message['text'], message['channel_name'])


def post_as_slackbot(channel, message):
  if config['post_as_slackbot'] == 'true':
    post_settings = {
      'token': config['slack_token'],
      'channel': channel,
      'username': config['slackbot_name'],
      'as_user': 'false',
      'icon_emoji': ':%s:' % config['slackbot_emoji'],
      'text': message
    }
    url = 'https://slack.com/api/chat.postMessage?' + urllib.urlencode(post_settings)
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
  else:
    print ' -> posting as slackbot disabled'


def find_mp3(name):
  sounds_dir = os.path.join(base_dir, config['sounds_dir'])
  file_name = name + '.' + config['filetype']
  direct_file = os.path.join(sounds_dir, file_name)
  if os.path.isfile(direct_file):
    return direct_file

  folders = [f for f in os.listdir(sounds_dir) if os.path.isdir(os.path.join(config['sounds_dir'], f))]
  for folder in folders:
    categorized_file = os.path.join(sounds_dir, folder, file_name)
    if os.path.isfile(categorized_file):
      print ' -> found sound in the %s folder' % folder
      return categorized_file


def play_mp3():
  global last_played
  sound_name = play_match.group(1)
  sound_file = find_mp3(sound_name)
  if sound_file:
    command = '%s "%s"' % (config['player'], sound_file)
    since_last_played = time.time() - last_played
    if (since_last_played) > int(config['timeout_duration']):
      action(command)
      last_played = time.time()
    else:
      remaining = int(config['timeout_duration']) - since_last_played
      messages = [
        'wooooah, at least wait a _few_ seconds between sounds ({remaining} left)',
        'just take a breath... and wait for {remaining} seconds',
        'it\'s my lunch break. Come back in {remaining} seconds'
      ] if int(since_last_played) < 5 else [
        'hey! it\'s only been {since_last_played} seconds. Come back in {remaining}',
        'calm down, it\'s only been {since_last_played} seconds! ({remaining} left)',
        'we just did this {since_last_played} seconds ago, can\'t we take a little break? ({remaining} left)'
      ]
      limit_message =  random.choice(messages).format(since_last_played=int(since_last_played), remaining=int(remaining))
      if message['channel_name'] == config['main_channel']:
        print ' -> printing limit message'
        post_as_slackbot(message['channel_name'], limit_message)
      else:
        print ' -> not in main channel, being quiet'
  else:
    print ' -> file doesnt exist: %s.%s' % (sound_name, config['filetype'])
    if message['channel_name'] == config['main_channel']:
      similar = search_sounds(sound_name)
      if len(similar) > 0:
        search_message = '\n'.join([
          '*Did you mean*:'
          '```',
          '\n'.join(similar),
          '```'
        ])
        post_as_slackbot(message['channel_name'], search_message)
      else:
        show_search(sound_name)
    else:
      print ' -> not in main channel, being quiet'


def text_to_speech():
  command = '%s "%s"' % (config['text2voice'], speak_match.group(1))
  action(command)



# Actual startup loop and event processor
if sc.rtm_connect():
  print "Connected as: %s\n" % sc.server.username
  while True:
    check_if_code_changed()
    refresh_config()
    refresh_whitelist()
    refresh_channels()
    for event in sc.rtm_read():
      try:
        if not is_valid_message(): continue

        message = parse_event()
        is_allowed_user = message['user_id'] in whitelist.keys()
        is_watched_channel = message['channel_id'] in channels.keys()
        if not is_watched_channel: continue
        if not is_allowed_user:
          print_unknown_user()
          continue
          
        if message['user_name'] == 'slackbot' and len(message['text']) > 90:
          continue

        print_debug_message()

        if message['user_name'] == 'slackbot':
          message['text'] = "play %s" % message['text'] 


        list_match = list_regex.match(message['text'])
        help_match = help_regex.match(message['text'])
        search_match = search_regex.match(message['text'])
        play_match = play_regex.match(message['text'])
        speak_match = speak_regex.match(message['text'])

        if help_match: show_help(); print ''
        elif list_match: show_list(); print ''
        elif search_match: show_search(); print ''
        elif play_match: play_mp3(); print ''
        elif speak_match: text_to_speech(); print ''

      except:
        print 'Ignoring an error...'
        traceback.print_exc()

    time.sleep(float(config['sync_interval']));
else:
  print 'Connection failed, invalid token?'
