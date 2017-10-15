#!/usr/bin/env python
# -*- coding: utf-8 -*-

import telegram
import re
from unidecode import unidecode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from random import randint
from datetime import datetime, timedelta
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

randomMsg = ['qué dices payaso', 'no seas bobo', 'basta', 'no te rayes', 'no te agobies']
lastPoleEstonia = datetime.now() - timedelta(days = 1)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Hola prim!', reply_to_message_id=update.message.message_id)


def help(bot, update):
    update.message.reply_text('asdqwe')
    
def getRandomByValue(value):
    randomValue = randint(0, value)
    return randomValue

def randomResponse(update):
    randomValue = getRandomByValue(1000)
    if randomValue < 5 and randomValue >= 3:
        indexMsg = getRandomByValue(len(randomMsg) -1)
        update.message.reply_text(randomMsg[indexMsg], reply_to_message_id=update.message.message_id)
    elif randomValue < 2:
        update.message.text = unidecode(update.message.text)
	update.message.text = re.sub(r'[AEOUaeou]+', 'i', update.message.text)

        update.message.reply_text(update.message.text, reply_to_message_id=update.message.message_id)

def sendGif(bot, update, pathGif):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.UPLOAD_PHOTO)
    bot.sendDocument(chat_id=update.message.chat_id, document=open(pathGif, 'rb'))

def echo(bot, update):
    if "valencia" in update.message.text.lower():
        randomValue = getRandomByValue(3)
        if randomValue <= 1:
	    bot.send_voice(chat_id=update.message.chat_id, voice=open('/home/pi/Desktop/collerinesBotData/voices/teamvalencia.ogg', 'rb'))
    elif "salud" in update.message.text.lower():
	update.message.reply_text('El dedo en el culo es la salud y el bienestar', reply_to_message_id=update.message.message_id)
    elif "llegas tarde" in update.message.text.lower():
	update.message.reply_text('como Collera', reply_to_message_id=update.message.message_id)
    elif "kele puto" in update.message.text.lower():
	update.message.reply_text(' /keleputo ')
    elif "sum41" in update.message.text.lower() or "sum 41" in update.message.text.lower():
	update.message.reply_text('100% confirmados para el Download')
    elif "pole estonia" in update.message.text.lower():
        global lastPoleEstonia
        now = datetime.now()
        if now.date() != lastPoleEstonia.date():
            update.message.reply_text('El usuario ' + update.message.from_user.name + ' ha hecho la pole estonia')
            lastPoleEstonia = now
    elif "zyzz" in update.message.text.lower():
	update.message.reply_text(' /zetayzetazeta ')
    elif "txumino" in update.message.text.lower():
        if "/txumino" not in update.message.text.lower():
            update.message.reply_text(' /txumino ')
    elif "gif del fantasma" in update.message.text.lower():
        sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/fantasma.mp4')
    elif "momento cabra" in update.message.text.lower():
        sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/momento_cabra.mp4')
    elif "gif del fantasma" in update.message.text.lower():
        sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/fantasma.mp4')
    elif "random" in update.message.text.lower():
        randomValue = getRandomByValue(3)
        if randomValue <= 1:
            sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/random.mp4')
    elif "reviento" in update.message.text.lower():
        sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/acho_reviento.mp4')
    elif "kulevra tirano" in update.message.text.lower() or "drop the ban" in update.message.text.lower():
        bot.send_photo(chat_id=update.message.chat_id, photo=open('/home/pi/Desktop/collerinesBotData/imgs/dropban.jpg', 'rb'))
    elif "templo" in update.message.text.lower() or "gimnasio" in update.message.text.lower():
        randomValue = getRandomByValue(4)
        if randomValue <= 1:
            sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/templo.mp4')
    elif "ficha" in update.message.text.lower():
	bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/pi/Desktop/collerinesBotData/stickers/ficha.webp', 'rb'), reply_to_message_id=update.message.message_id)
    elif len(update.message.text) > 7: ##mimimimimimi
        randomResponse(update)

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
