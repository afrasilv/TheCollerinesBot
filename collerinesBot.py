#!/usr/bin/env python
# -*- coding: utf-8 -*-

import telegram
import re
import pickle
from unidecode import unidecode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from random import randint
from datetime import datetime, timedelta
from configparser import ConfigParser
import os
import sys
from threading import Thread
import logging

# Create the EventHandler and pass it your bot's token.
config = ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
updater = Updater(config["main"]["token"])
    
j = updater.job_queue

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


randomMsg = ['qué pasa, jamboide', 'no seas bobo', 'basta', 'no te rayes', 'no te agobies', 'vale', 'qué dices, prim', 'ok', 'geniaaaaaal', 'fataaaaaal', '/geniaaaaaal', '/fataaaaaal', 'Myrath macho', '/jajj', '/jjaj', '/yee', "A topeth!"]
random4GodMsg = ['dime', 'basta', 'déjame', 'ahora no', 'ZzZzzzZzz', '¿qué te pasa?']
mimimimiImgPath = ['/home/pi/Desktop/collerinesBotData/imgs/mimimi.jpg', '/home/pi/Desktop/collerinesBotData/imgs/mimimi1.jpg', '/home/pi/Desktop/collerinesBotData/imgs/mimimi2.jpg']
m3AudiosPath = ['/home/pi/Desktop/collerinesBotData/voices/m3Javi.ogg', '/home/pi/Desktop/collerinesBotData/voices/m3Javig.ogg', '/home/pi/Desktop/collerinesBotData/voices/m3Feli.ogg']
huehuehuePath = ['/home/pi/Desktop/collerinesBotData/gifs/huehuehue.mp4', '/home/pi/Desktop/collerinesBotData/gifs/huehuehue1.mp4']
sectaImgPath = ['/home/pi/Desktop/collerinesBotData/imgs/secta.jpg', '/home/pi/Desktop/collerinesBotData/imgs/secta1.jpg']
lastPoleEstonia = datetime.now() - timedelta(days = 1)
canTalk = True


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Hola prim!', reply_to_message_id=update.message.message_id)
    now = datetime.now() - timedelta(days = 1)
    now = now.replace(hour=19, minute=00)
    job_daily = j.run_daily(callback_andalucia, now.time(), days=(0,1,2,3,4,5,6), context=update.message.chat_id)
    now = now.replace(hour=02, minute=00)
    job_daily = j.run_daily(callback_bye, now.time(), days=(0,1,2,3,4,5,6), context=update.message.chat_id)


def help(bot, update):
    update.message.reply_text('asdqwe')
    
def getRandomByValue(value):
    randomValue = randint(0, value)
    return randomValue

def randomResponse(update, bot):
    randomValue = getRandomByValue(1000)
    if randomValue < 15 and randomValue > 11:
        bot.send_voice(chat_id=update.message.chat_id, voice=open('/home/pi/Desktop/collerinesBotData/voices/yord.ogg', 'rb'), reply_to_message_id=update.message.message_id)
    elif randomValue == 11:
        array = update.message.text.split()
        randomIndex = getRandomByValue(3)
        wasChanged = None
        if randomIndex == 0:
            wasChanged = bool(re.search(r'[VvSs]+', update.message.text))
            update.message.text = re.sub(r'[VvSs]+', 'f', update.message.text)
        elif randomIndex == 1:
            wasChanged = bool(re.search(r'[Vv]+', update.message.text))
            update.message.text = re.sub(r'[Vv]+', 'f', update.message.text)
        else:
            wasChanged = bool(re.search(r'[TtVvSsCc]+', update.message.text))
            update.message.text = re.sub(r'[TtVvSsCc]+', 'f', update.message.text)
        if wasChanged:
            update.message.reply_text(update.message.text, reply_to_message_id=update.message.message_id)
	    bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/pi/Desktop/collerinesBotData/stickers/alef.webp', 'rb'))
    elif randomValue == 10:
	bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/pi/Desktop/collerinesBotData/stickers/approval.webp', 'rb'), reply_to_message_id=update.message.message_id)
    elif randomValue <= 9 and randomValue >= 3:
        randomMsgIndex = getRandomByValue(len(randomMsg) -1)
        update.message.reply_text(randomMsg[randomMsgIndex], reply_to_message_id=update.message.message_id)
    elif randomValue < 2:
        update.message.text = unidecode(update.message.text)
	update.message.text = re.sub(r'[AEOUaeou]+', 'i', update.message.text)
        update.message.reply_text(update.message.text, reply_to_message_id=update.message.message_id)
        randomMsgIndex = getRandomByValue(len(mimimimiImgPath) -1)
        sendImg(bot, update, mimimimiImgPath[randomMsgIndex])
        

def sendGif(bot, update, pathGif):
    bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.UPLOAD_PHOTO)
    bot.sendDocument(chat_id=update.message.chat_id, document=open(pathGif, 'rb'))

def sendVoice(bot, update, pathVoice):
    bot.send_voice(chat_id=update.message.chat_id, voice=open(pathVoice, 'rb'))

def sendImg(bot, update, pathImg):
    bot.send_photo(chat_id=update.message.chat_id, photo=open(pathImg, 'rb'))


def echo(bot, update):
    global canTalk
    
    if update.message.from_user.username != None and update.message.from_user.id in get_admin_ids(bot, update.message.chat_id) and update.message.text != None and "miguelito para" == update.message.text.lower():
        canTalk = None
    elif update.message.from_user.username != None and update.message.from_user.id in get_admin_ids(bot, update.message.chat_id) and update.message.text != None and "miguelito sigue" == update.message.text.lower():
        canTalk = True
    
    if canTalk:
        #voice
        if re.search(r'\bvalencia\b', update.message.text.lower()):
            randomValue = getRandomByValue(3)
            if randomValue <= 1:
                sendVoice(bot, update, '/home/pi/Desktop/collerinesBotData/voices/teamvalencia.ogg')
        elif re.search(r'\<3\b', update.message.text.lower()):
            randomAudioIndex = getRandomByValue(len(m3AudiosPath) -1)
            sendVoice(bot, update, m3AudiosPath[randomAudioIndex])
        elif re.search(r'\bgeni[a]+[a-zA-Z]+\b', update.message.text.lower()):
            sendVoice(bot, update, '/home/pi/Desktop/collerinesBotData/voices/geniaaa.ogg')
        elif re.search(r'\brocoso\b', update.message.text.lower()) or re.search(r'\bciclado\b', update.message.text.lower()) or re.search(r'\bciclao\b', update.message.text.lower()):
            randomValue = getRandomByValue(3)
            if randomValue <= 1:
                sendVoice(bot, update, '/home/pi/Desktop/collerinesBotData/voices/teamvalencia.ogg')
        elif re.search(r'\bmétodo willy\b', update.message.text.lower()) or re.search(r'\bmetodo willy\b', update.message.text.lower()):
            bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/pi/Desktop/collerinesBotData/voice/willy.ogg', 'rb'), reply_to_message_id=update.message.message_id)
            
        #gif
        elif re.search(r'\bpfff[f]+\b', update.message.text.lower()) or '...' == update.message.text:
            randomValue = getRandomByValue(4)
            if randomValue <= 1:
                sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/pffff.mp4')
        elif "gif del fantasma" in update.message.text.lower():
            sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/fantasma.mp4')
        elif "bukkake" in update.message.text.lower():
            sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/perro.mp4')
        elif "no me jodas" in update.message.text.lower() or "no me digas" in update.message.text.lower():
            randomValue = getRandomByValue(4)
            if randomValue <= 1:
                sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/ferran_agua.mp4')
        elif "all right" in update.message.text.lower() or re.search(r'\bestupendo\b', update.message.text.lower()) or re.search(r'\bmaravilloso\b', update.message.text.lower()):
            randomValue = getRandomByValue(4)
            if randomValue <= 1:
                sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/ferran_thumb.mp4')
        elif "momento cabra" in update.message.text.lower():
            sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/momento_cabra.mp4')
        elif re.search(r'\bcabra\b', update.message.text.lower()):
            randomValue = getRandomByValue(4)
            if randomValue <= 1:
                sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/cabra_scream.mp4')
        elif "qué?" == unidecode(update.message.text.lower()) or "que?" == update.message.text.lower():
            sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/cabra.mp4')
        elif re.search(r'\brandom\b', update.message.text.lower()):
            randomValue = getRandomByValue(3)
            if randomValue <= 1:
                sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/random.mp4')
        elif re.search(r'\breviento\b', update.message.text.lower()) or re.search(r'\brebiento\b', update.message.text.lower()):
            sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/acho_reviento.mp4')
        elif re.search(r'\bchoca\b', update.message.text.lower()):
            sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/choca.mp4')
        elif "templo" in update.message.text.lower() or "gimnasio" in update.message.text.lower():
            randomValue = getRandomByValue(4)
            if randomValue <= 1:
                sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/templo.mp4')
        elif re.search(r'\bhuehue[hue]+\b', update.message.text.lower()):
            randomHuehuehueIndex = getRandomByValue(len(huehuehuePath) -1)
            sendGif(bot, update, huehuehuePath[randomHuehuehueIndex])
        elif re.search(r'\byee\b', update.message.text.lower()):
            if "/yee" not in update.message.text.lower():
                sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/yee.mp4')
        elif re.search(r'\bstrike\b', update.message.text.lower()):
            randomValue = getRandomByValue(4)
            if randomValue <= 1:
                sendGif(bot, update, '/home/pi/Desktop/collerinesBotData/gifs/strike.mp4')
                
        #messages
        elif re.search(r'\bsalud\b', update.message.text.lower()):
            update.message.reply_text('El dedo en el culo es la salud y el bienestar', reply_to_message_id=update.message.message_id)
        elif re.search(r'\bllegas tarde\b', update.message.text.lower()) or re.search(r'\bllega tarde\b', update.message.text.lower()):
            update.message.reply_text('como Collera', reply_to_message_id=update.message.message_id)
        elif "eres rápido" in unidecode(update.message.text.lower()) or "eres rapido" in update.message.text.lower():
            update.message.reply_text('no como Collera', reply_to_message_id=update.message.message_id)
        elif re.search(r'\bkele puto\b', update.message.text.lower()):
            update.message.reply_text(' /keleputo ')
        elif re.search(r'\bsum41\b', update.message.text.lower()) or re.search(r'\bsum 41\b', update.message.text.lower()):
            update.message.reply_text('100% confirmados para el Download')
        elif re.search(r'\bjjaj[ja]*\b', update.message.text.lower()):
            update.message.reply_text('/jjaj')
        elif re.search(r'\bjajj[ja]*\b', update.message.text.lower()):
            update.message.reply_text('/jajj')
        elif re.search(r'\bpole estonia\b', update.message.text.lower()):
            global lastPoleEstonia
            now = datetime.now()
            if now.date() != lastPoleEstonia.date() and now.hour >= 23:
                update.message.reply_text('El usuario ' + update.message.from_user.name + ' ha hecho la pole estonia')
                lastPoleEstonia = now
        elif re.search(r'\bzyzz\b', update.message.text.lower()):
            update.message.reply_text(' /zetayzetazeta ')
        elif re.search(r'\bdios\b', update.message.text.lower()):
            randomValue = getRandomByValue(4)
            if randomValue < 1 :
                indexMsg = getRandomByValue(len(random4GodMsg) -1)
                update.message.reply_text(random4GodMsg[indexMsg], reply_to_message_id=update.message.message_id)
        elif re.search(r'\btxumino\b', update.message.text.lower()):
            if "/txumino" not in update.message.text.lower():
                update.message.reply_text(' /txumino ')
        
        # imgs
        elif "kulevra tirano" in update.message.text.lower() or "drop the ban" in update.message.text.lower():
            sendImg(bot, update, '/home/pi/Desktop/collerinesBotData/imgs/dropban.jpg')
        elif re.search(r'\bsecta\b', update.message.text.lower()):
            randomSectaIndex = getRandomByValue(len(sectaImgPath) -1)
            sendImg(bot, update, sectaImgPath[randomSectaIndex])
        elif re.search(r'\bnazi\b', update.message.text.lower()):
            randomValue = getRandomByValue(3)
            if randomValue < 1:
                sendImg(bot, update, '/home/pi/Desktop/collerinesBotData/imgs/nazi.jpg')
        
        #stickers
        elif re.search(r'\bprog\b', update.message.text.lower()):
            bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/pi/Desktop/collerinesBotData/stickers/prog.webp', 'rb'), reply_to_message_id=update.message.message_id)
        elif re.search(r'\bsend nudes\b', update.message.text.lower()) or "send noodles" in update.message.text.lower():
            bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/pi/Desktop/collerinesBotData/stickers/sendnudes.webp', 'rb'), reply_to_message_id=update.message.message_id)
        elif re.search(r'\bficha\b', update.message.text.lower()) or re.search(r'\bfichas\b', update.message.text.lower()):
            bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/pi/Desktop/collerinesBotData/stickers/ficha.webp', 'rb'), reply_to_message_id=update.message.message_id)
        elif re.search(r'\bbutanero\b', update.message.text.lower()) or "bombona" in update.message.text.lower():
            bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/pi/Desktop/collerinesBotData/stickers/butanero.webp', 'rb'), reply_to_message_id=update.message.message_id)
        elif re.search(r'\bkylo\b', update.message.text.lower()):
            bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/pi/Desktop/collerinesBotData/stickers/kylo.webp', 'rb'), reply_to_message_id=update.message.message_id)
        elif re.search(r'\bcostra\b', update.message.text.lower()):
            bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/pi/Desktop/collerinesBotData/stickers/costra.webp', 'rb'), reply_to_message_id=update.message.message_id)
        elif re.search(r'\bhuevo\b', update.message.text.lower()) or re.search(r'\bhuevos\b', update.message.text.lower()):
            randomValue = getRandomByValue(5)
            if randomValue < 1:
                bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/pi/Desktop/collerinesBotData/stickers/huevo.webp', 'rb'), reply_to_message_id=update.message.message_id)
        elif re.search(r'\blp\b', update.message.text.lower()) or re.search(r'\blinkin park\b', update.message.text.lower()):
            bot.send_sticker(chat_id=update.message.chat_id, sticker=open('/home/pi/Desktop/collerinesBotData/stickers/lp.webp', 'rb'), reply_to_message_id=update.message.message_id)
        elif len(update.message.text) > 7: ##mimimimimimi
            randomResponse(update, bot)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def callback_andalucia(bot, job):
    bot.send_message(chat_id=job.context, text="¡Buenos días, Andalucía! :D")
    
def callback_bye(bot, job):
    bot.send_message(chat_id=job.context, text="BYE")
    bot.sendChatAction(chat_id=job.context, action=telegram.ChatAction.UPLOAD_PHOTO)
    bot.sendDocument(chat_id=job.context, document=open('/home/pi/Desktop/collerinesBotData/gifs/bye.mp4', 'rb'))

def stop(bot, update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
        global canTalk
        canTalk = None

def restart(bot, update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
        global canTalk
        canTalk = True
        
def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 1 hour."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]

def main():
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    
    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('seguir', restart))
    dp.add_handler(CommandHandler('parar', stop))
    
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
