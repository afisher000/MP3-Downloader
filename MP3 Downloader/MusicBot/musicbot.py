# -*- coding: utf-8 -*-
"""
Created on Sun Sep  4 11:09:49 2022

@author: afish
"""

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from Handler import Handler
import os

# Tokens
SLACK_BOT_TOKEN = os.environ['MUSICBOT_BOT_TOKEN']
SLACK_BOT_USER_TOKEN = os.environ['MUSICBOT_BOT_USER_TOKEN']
app = App(token=SLACK_BOT_TOKEN)

# Initialize classes
HANDLER = Handler(app, SLACK_BOT_TOKEN, SLACK_BOT_USER_TOKEN)

# Connect event decorators with functions calling class functions.
@app.event("message")
def handle_message_events(body, logger):
    HANDLER.handle_message_events(body, logger)

@app.event("app_mention")
def handle_app_mention_events(event, say, ack):
    HANDLER.handle_app_mention_events(event, say, ack)
    
    
@app.action("download_song")
def handle_song_download(ack, body, logger, say):
    HANDLER.handle_song_download(ack, body, logger, say)
    logger.info(body)
    
@app.action("cancel_message")
def handle_cancellation(ack, body, logger):
    HANDLER.handle_cancellation(ack, body, logger)
    
    
# Dummy events to avoid warnings
@app.action("checkboxes-action")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)
    
    
if __name__=="__main__":
    SocketModeHandler(app, SLACK_BOT_TOKEN).start()