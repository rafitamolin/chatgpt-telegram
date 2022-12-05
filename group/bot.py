#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Group bot for telegram.
"""

import json
import logging
import os

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    ChatJoinRequestHandler,
    CallbackContext,
)

from revChatGPT.revChatGPT import Chatbot

load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

config = {
    "Authorization": os.getenv("OPENAI_API_KEY"),
    "session_token": os.getenv("SESSION_TOKEN"),
}

chatbot = Chatbot(config, conversation_id=None)
members = []


def add_member(name: str) -> None:
    """Add a member to the group."""
    if name and name not in members:
        members.append(name)
        with open("members.txt", "a") as f:
            f.write(json.dumps(members))


def remove_member(name: str) -> None:
    """Remove a member from the group."""
    if name and name in members:
        members.remove(name)
        with open("members.txt", "w") as f:
            f.write(json.dumps(members))


def is_allowed(update: Update) -> bool:
    """Check if the user is whitelisted."""
    if update.effective_user.username not in os.getenv("ALLOWED_USERS").split(","):
        update.message.reply_text(
            "You are not allowed to use this bot. Contact @Klingefjord to get access."
        )
        return False
    return True


def reply(update: Update, context: CallbackContext) -> None:
    """Call the OpenAI API."""
    if not is_allowed(update):
        return

    try:
        prompt = (
            update.effective_user.first_name
            if update.effective_user.first_name
            else update.effective_user.username
        ) + f" says: {update.message.text.replace('/bot ', '')}"
        response = chatbot.get_chat_response(prompt)
        update.message.reply_text(response["message"])
    except Exception as e:
        print(e)
        update.message.reply_text(
            "Sorry, something went wrong. Please try again later."
        )


def join(update: Update, context: CallbackContext) -> None:
    """Add a member to the group."""
    if not is_allowed(update):
        return

    add_member(update.effective_user.first_name)


def leave(update: Update, context: CallbackContext) -> None:
    """Remove a member from the group."""
    if not is_allowed(update):
        return

    remove_member(update.effective_user.first_name)


def main() -> None:
    # load members
    if os.path.exists("members.txt"):
        with open("members.txt", "r") as f:
            members = json.loads(f.read())

    chatbot.reset_chat()  # Forgets conversation
    chatbot.refresh_session()  # Uses the session_token to get a new bearer token

    # Create the Updater and pass it your bot's token.
    updater = Updater(os.getenv("TELEGRAM_TOKEN"))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("bot", reply, pass_user_data=True))
    dispatcher.add_handler(ChatJoinRequestHandler(join))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
