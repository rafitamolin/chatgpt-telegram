#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
"""

import logging
import os

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
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


def is_allowed(update: Update) -> bool:
    """Check if the user is sane."""
    if update.effective_user.username not in os.getenv("ALLOWED_USERS").split(","):
        update.message.reply_text(
            "You are not allowed to use this bot. Contact @Klingefjord to get access."
        )
        return False
    return True


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    if not is_allowed(update):
        return

    user = update.effective_user
    update.message.reply_markdown_v2(
        rf"Hi {user.mention_markdown_v2()}\!",
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text("Help!")


def reply(update: Update, context: CallbackContext) -> None:
    """Call the OpenAI API."""
    if not is_allowed(update):
        return

    try:
        update.message.reply_text(update.message.text)
        response = chatbot.get_chat_response(update.message.text)
        update.message.reply_text(response["message"])
    except Exception as e:
        print(e)
        update.message.reply_text(
            "Sorry, something went wrong. Please try again later."
        )


def reset(update: Update, context: CallbackContext) -> None:
    """Reset the chatbot."""
    if not is_allowed(update):
        return

    chatbot.reset_chat()  # Forgets conversation
    chatbot.refresh_session()  # Uses the session_token to get a new bearer token
    update.message.reply_text("Yep, I don't remember a thing.")


def start_bot() -> None:
    """Start the bot."""
    chatbot.reset_chat()  # Forgets conversation
    chatbot.refresh_session()  # Uses the session_token to get a new bearer token

    # Create the Updater and pass it your bot's token.
    updater = Updater(os.getenv("TELEGRAM_TOKEN"))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("reset", reset))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, reply))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    start_bot()
