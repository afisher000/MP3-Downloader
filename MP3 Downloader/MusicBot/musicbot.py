# -*- coding: utf-8 -*-
"""
Created on Sun Sep  4 11:09:49 2022

@author: afish
"""
# %%
#%%

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
import utils_bot as ub

# Define tokens and start app
# Put tokens in tokens.txt file?
SLACK_BOT_TOKEN = os.environ['MUSICBOT_BOT_TOKEN']
SLACK_BOT_USER_TOKEN = os.environ['MUSICBOT_BOT_USER_TOKEN']
app = App(token=SLACK_BOT_TOKEN)


# Connect event decorators with functions calling class functions.
@app.event("message")
def handle_message_events(event, say, ack):
    # Only respond to Andrew messages
    Andrew_ID = 'U041KR1G9TJ'
    if 'user' not in event.keys() or event['user'] != Andrew_ID:
        return

    # Only respond to direct messages
    if event['channel'][0] != 'D':
        return

    # Parse slackbot call
    function, argument = ub.parse_slackbot_call(event['text'])
    if hasattr(ub, 'function_'+function):
        post_object = getattr(ub, 'function_' + function)(argument)
        say(token = SLACK_BOT_USER_TOKEN, **post_object)
    else:
        say(
            token = SLACK_BOT_USER_TOKEN,
            text = (
                'Could not parse message, remember to use the format "function(argument)".\n'
                'Try "help()" for suggestions.'
            )
        )
    
    
@app.action("download_song")
def handle_song_download(ack, body, logger, say):
    ack()

    # Replace chat with submission message
    app.client.chat_delete( 
        token = SLACK_BOT_USER_TOKEN,
        channel = body['channel']['id'],
        ts = body['message']['ts'],
        blocks = None
    )
    say(token = SLACK_BOT_USER_TOKEN, text = 'Submission received, updates to follow...')

    # Attempt to download songs, return updates
    selected_songs = body['state']['values']['checkbox_id']['checkboxes-action']['selected_options']
    songs_to_download = [option['value'] for option in selected_songs]
    for song_description in songs_to_download:
        post_object = ub.download_song(song_description)
        say(token = SLACK_BOT_USER_TOKEN, **post_object)
    return

    
@app.action("cancel_message")
def handle_cancellation(ack, body, logger):
    ack()
    app.client.chat_delete( 
        token = SLACK_BOT_USER_TOKEN,
        channel = body['channel']['id'],
        ts = body['message']['ts'],
        blocks = None
    )
    
# Dummy events to avoid warnings
@app.action("checkboxes-action")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)
    
    
if __name__=="__main__":
    SocketModeHandler(app, SLACK_BOT_TOKEN).start()
# %%
