#!/usr/bin/env python
# -*- coding: utf-8 -*-

import telegram
import re
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from random import randint
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Hola prim!')


def help(bot, update):
    update.message.reply_text('asdqwe')

def echo(bot, update):
    if "valencia" in update.message.text.lower():
	bot.send_voice(chat_id=update.message.chat_id, voice=open('/home/afrasilv/Desktop/ferran.ogg', 'rb'))
    elif "salud" in update.message.text.lower():
	update.message.reply_text('El dedo en el culo es la salud y el bienestar')
    elif "momento cabra" in update.message.text.lower():
        bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.UPLOAD_PHOTO)
        bot.sendDocument(chat_id=update.message.chat_id, document=open('/home/afrasilv/Desktop/momento_cabra.mp4', 'rb'))
    elif "ficha" in update.message.text.lower():
	bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/afrasilv/Desktop/sticker.webp', 'rb'))
    elif len(update.message.text) > 7: ##mimimimimimi
        randomValue = randint(0, 100)
        if randomValue < 10:
	    update.message.reply_text(update.message.text)
        elif randomValue < 5:
            update.message.text = re.sub(r'qu[aeiou]|c[aou]|gu[ei]|g[aou]|gü|z[aeou]|[aeou]', 'i', update.message.text)
            update.message.text = re.sub(r'[áéóú]', 'í', update.message.text)
	    update.message.reply_text(update.message.text)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("476217954:AAGpClsrvtCICifhF8yKdDghG8UUofHLTAA")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
