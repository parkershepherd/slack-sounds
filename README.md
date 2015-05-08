slack-sounds
================
A client for Slack.com, that plays sound files on request e.g. `play trololo`.

This is designed to run on a box in your office hooked up to speakers. That way everyone in your slack channel can enjoy its magic.

Overview
---------
This plugin implements the python-slackclient to listen to channels its in (or direct messages) and responds to requests to play sounds of the format:

    play filename

Installation
----------

#### Automatic w/ PyPI

    $ sudo apt-get install python-dev
    $ sudo pip install websocket
    $ sudo pip install slackclient

You'll also need an audio player that can handle the format

    $ player path/to/file.mp3

I recommend mpg123 because it 'just works' with mp3s. Alternatives are aplay, paplay, mplayer, etc.

    $ sudo apt-get install mpg123

Usage
-----
_Note:_ You must obtain a token for the user/bot. You can find or generate these at the [Slack API](https://api.slack.com/web) page. You also need to create the bot for that matter.

Put the token in a file called token.txt in the same directory as sounds.py

Run the bot:

    $ python sounds.py

Chat with the bot directly, or post in a channel its a member of:

    play rollout

_Note:_ The default sounds were lifted directly from here: http://www.emoji-cheat-sheet.com/ (thanks campfire!)
