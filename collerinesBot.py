#!/usr/bin/env python
# -*- coding: utf-8 -*-

import telegram
import re
import pickle
from unidecode import unidecode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from random import randint
from datetime import datetime, timedelta
import dateutil.parser
from configparser import ConfigParser
from collections import OrderedDict
import json
import os
import sys
from threading import Thread
import logging
from SpotifyYouTubeClass import spotifyYouTubeClass
from RememberClass import rememberClass
from telegram.ext.dispatcher import run_async

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

dataPath = os.path.join(os.path.dirname(__file__)) + '/data'

lastPoleEstonia = datetime.now() - timedelta(days=1)
canTalk = True
godMode = True
firstMsg = True
botDict = {}
downloadData = None
lastFileDownloadedCount = 0
weekdayConstant = ['lunes', 'martes', 'miércoles',
                   'jueves', 'viernes', 'sábado', 'domingo']


def ini_to_dict(path):
    """ Read an ini path in to a dict
    :param path: Path to file
    :return: an OrderedDict of that path ini data
    """
    config = ConfigParser()
    config.read(path)
    return_value = OrderedDict()
    for section in reversed(config.sections()):
        return_value[section] = OrderedDict()
        section_tuples = config.items(section)
        for itemTurple in reversed(section_tuples):
            return_value[section][itemTurple[0]] = itemTurple[1]
    return return_value


# Create the EventHandler and pass it your bot's token.
config = ConfigParser()
settings = ini_to_dict(os.path.join(os.path.dirname(__file__), "config.ini"))
updater = Updater(settings["main"]["token"])

j = updater.job_queue

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.


def start(bot, update):
    update.message.reply_text(
        'Hola prim!', reply_to_message_id=update.message.message_id)


def help(bot, update):
    update.message.reply_text('asdqwe')


def replaceStr(msg, str):
    if str in msg:
        msg = msg.replace(str + " ", "", 1)
    return msg


def getRandomByValue(value):
    randomValue = randint(0, value)
    return randomValue


def randomResponse(update, bot):
    randomValue = getRandomByValue(1400)
    if randomValue < 13 and randomValue > 11:
        sendVoice(bot, update, os.path.join(os.path.dirname(__file__)) +
            '/data' + botDict["audios"][0])
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
            update.message.text = re.sub(
                r'[TtVvSsCc]+', 'f', update.message.text)
        if wasChanged:
            update.message.reply_text(
                update.message.text, reply_to_message_id=update.message.message_id)
            sendSticker(bot, update, os.path.join(os.path.dirname(__file__)) +
                '/data' + botDict["stickers"]["dinofaurioPath"][0], False)
    elif randomValue == 10:
        sendSticker(bot, update, os.path.join(os.path.dirname(__file__)) +
            '/data' + botDict["stickers"]["approvalStickerPath"][0], True)
    elif randomValue <= 9 and randomValue >= 3:
        randomMsgIndex = getRandomByValue(len(botDict["randomMsg"]) - 1)
        sendMsg(update, botDict["randomMsg"][randomMsgIndex], False)
    elif randomValue < 2:
        update.message.text = unidecode(update.message.text)
        update.message.text = re.sub(r'[AEOUaeou]+', 'i', update.message.text)
        update.message.reply_text(
            update.message.text, reply_to_message_id=update.message.message_id)
        randomMsgIndex = getRandomByValue(
            len(botDict["stickers"]["mimimimiStickerPath"]) - 1)
        sendSticker(bot, update, dataPath + botDict["stickers"], False)


def isAdmin(bot, update):
    if update.message.from_user.username != None and update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
        return True
    else:
        return None


def startJobs(bot, update):
    now = datetime.now() - timedelta(days=1)
    restTime = getRandomByValue(2)
    now = now.replace(hour=17 + restTime, minute=getRandomByValue(59))
    job_daily = j.run_daily(callback_andalucia, now.time(), days=(
        0, 1, 2, 3, 4, 5, 6), context=update.message.chat_id)
    # now = now.replace(hour=2, minute=00)
    # job_daily = j.run_daily(callback_bye, now.time(), days=(
    #     0, 1, 2, 3, 4, 5, 6), context=update.message.chat_id)
    data = rememberClass.loadMemories()
    for item in data:
        j.run_once(callback_remember, dateutil.parser.parse(
            item["when"]), context=update.message.chat_id)


def savePoleStats(update):
    username = update.message.from_user.name.replace("@", "")
    try:
        json_file = open('polestats.json', 'r')
        data = json.load(json_file, object_pairs_hook=OrderedDict)
    except IOError:
        data = [{'username': username, 'count': 0}]

    found = None
    i = 0
    while i < len(data):
        if data[i]['username'] == username:
            data[i]['count'] += 1
            found = True
        i += 1
    if found == None:
        data.append({'username': username, 'count': 1})

    with open('polestats.json', 'w') as outfile:
        json.dump(data, outfile)


def gimmeTheRank(update):
    try:
        json_file = open('polestats.json', 'r')
        data = json.load(json_file, object_pairs_hook=OrderedDict)
    except IOError:
        data = {}

    data = json.dumps(
        {'data': sorted(data, key=lambda x: x['count'], reverse=True)})
    data = json.loads(data)
    messageValue = ""
    index = 0
    data = data['data']
    while index < len(data):
        messageValue += data[index]['username'] + \
            " ---> " + str(data[index]['count']) + "\n"
        index += 1

    update.message.reply_text(
        messageValue, reply_to_message_id=update.message.message_id)


def sendGif(bot, update, pathGif):
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=telegram.ChatAction.UPLOAD_PHOTO)
    bot.sendDocument(chat_id=update.message.chat_id,
                     document=open(pathGif, 'rb'))


def sendVoice(bot, update, pathVoice):
    bot.send_voice(chat_id=update.message.chat_id, voice=open(pathVoice, 'rb'))


def sendImg(bot, update, pathImg):
    bot.send_photo(chat_id=update.message.chat_id, photo=open(pathImg, 'rb'))


def sendMsg(update, text, isReply):
    if isReply:
        update.message.reply_text(
            text, reply_to_message_id=update.message.message_id)
    else:
        update.message.reply_text(
            text)


def sendSticker(bot, update, pathSticker, isReply):
    if isReply:
        bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
            pathSticker, 'rb'), reply_to_message_id=update.message.message_id)
    else:
        bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
            pathSticker, 'rb'))


@run_async
def sendData(bot, update, object):
    if object["type"] == "voice":
        sendVoice(
            bot, update, dataPath + getPath(object["path"]))
    elif object["type"] == "gif":
        sendGif(
            bot, update, dataPath + getPath(object["path"]))
    elif object["type"] == "text":
        sendMsg(
            update, getPath(object["path"]), object["isReply"])
    elif object["type"] == "img":
        sendImg(bot, update, dataPath + getPath(object["path"]))
    elif object["type"] == "sticker":
        sendSticker(bot, update, dataPath +
                    getPath(object["path"]), object["isReply"])


def getPath(arrayData):
    index = getRandomByValue(len(arrayData) - 1)
    return arrayData[index]


def checkIfSendData(bot, update, object):
    if len(object["lastTimeSentIt"]) is not 0:
        lastTimeSentIt = datetime.strptime(
            object["lastTimeSentIt"], '%Y-%m-%dT%H:%M:%S.%f')
        now = datetime.now()
        if now.date() > lastTimeSentIt.date():
            if object["randomMaxValue"] is not 0:
                randomValue = getRandomByValue(object["randomMaxValue"])
                if randomValue <= 1:
                    sendData(bot, update, object)
                    if object["doubleMsg"] is True:
                        sendData(bot, update, object["doubleObj"])
                    return True
            else:
                sendData(bot, update, object)
                if object["doubleMsg"] is True:
                    sendData(bot, update, object["doubleObj"])
                return True
    else:
        sendData(bot, update, object)
        if object["doubleMsg"] is True:
            sendData(bot, update, object["doubleObj"])
        return True
    return False


def addTime(now, object):
    if object["timeToIncrement"] is not 0:
        timeObject = {'type': object["kindTime"],
                      'value':  object["timeToIncrement"]}
        return rememberClass.checkRememberDate(now, timeObject, None).isoformat()
    else:
        return ""


def loadDictionary(bot, update):
    global botDict
    try:
        json_file = open('dataDictionary.json', encoding="utf-8")
        botDict = json.load(json_file)
        data = json.dumps(
            {'data': botDict})
        botDict = json.loads(data)
        botDict = botDict["data"]
    except IOError:
        botDict = {}


# miguelito mete text##hola__in#0##0#min###huehuehuehue
def addDataToJson(text):
    global downloadData
    msg = replaceStr(text, "miguelito mete")
    msgSplitted = msg.split("#")
    msg = replaceStr(msg, msgSplitted[0])
    if msgSplitted[0] == "random":
        botDict['randomMsg'].append(msg)
    elif msgSplitted[0] == "dinosaurio":
        botDict['dinofaurioPath'].append(msg)
    elif msgSplitted[0] == "mimimi":
        botDict['mimimimiStickerPath'].append(msg)
    else:
        msgToCheck = []
        for item in msgSplitted[2].split("--"):
            print(item)
            itemSplitted = item.split("__")
            print(itemSplitted)
            msgToCheck.append(
                {"text": itemSplitted[0], "type": itemSplitted[1]})

        downloadData = {
            "type": msgSplitted[0],
            "regexpValue": [msgSplitted[1].split("--")] if len(msgSplitted[1]) > 0 else [],
            "msgToCheck": msgToCheck,
            "randomMaxValue": int(msgSplitted[3]),
            "lastTimeSentIt": msgSplitted[4],
            "timeToIncrement": int(msgSplitted[5]),
            "kindTime": msgSplitted[6],
            "doubleMsg": bool(msgSplitted[7]),
            "doubleObj": {},
            "notIn": [msgSplitted[8].split("--")] if len(msgSplitted[1]) > 0 else [],
            "isReply": False
        }
        if len(msgSplitted) > 10 and msgSplitted[10] == "true":
            downloadData["doubleObj"] = {
                "type": msgSplitted[11],
                "path": [],
                "isReply": false
            }

    if msgSplitted[0] == "text":
        downloadData["path"] = msgSplitted[9].split("--")
        botDict["keywords"].append(downloadData)

    saveDictionary()


def saveDictionary():
    with open('dataDictionary.json', 'w') as outfile:
        json.dump(botDict, outfile)


def gimmeTheSpotifyPlaylistLink(bot, update):
    update.message.reply_text(
        'ahí te va! ' + settings["spotify"]["spotifyplaylistlink"])


def echo(bot, update):
    global canTalk
    global firstMsg
    global godMode
    global botDict
    global downloadData

    # if downloadData is not None and update.message.from_user.username == settings["main"]["fatherid"]:
    # if downloadData.type == "voice"
    #     file_id = message.voice.file_id
    #     newFile = bot.get_file(file_id)
    #     newFile.download('voice.ogg')

    if str(update.message.chat_id) == str(settings["main"]["groupid"]):
        if update.message.text != None and "miguelito para" == update.message.text.lower():
            stop(bot, update)
        elif update.message.text != None and "miguelito sigue" == update.message.text.lower():
            restart(bot, update)
        elif update.message.text != None and "miguelito al coma" == update.message.text.lower() and update.message.from_user.username == settings["main"]["fatherid"]:
            godMode = None
        elif update.message.text != None and "miguelito vuelve" == update.message.text.lower() and update.message.from_user.username == settings["main"]["fatherid"]:
            godMode = True

        wasAdded = False
        wasAdded = spotifyYouTubeClass.checkYoutubeSpotifyLinks(update)

        # startJobs
        if firstMsg:
            startJobs(bot, update)
            loadDictionary(bot, update)
            firstMsg = None

        if "miguelito recuerda" in update.message.text.lower() or "miguelito recuerdame" in update.message.text.lower() or "miguelito recuérdame" in update.message.text.lower():
            msg = update.message.text.lower()
            msgSplit = msg.split(" ")
            msg = msg.replace(
                msgSplit[0] + " " + msgSplit[1] + " ", "")
            for i in range(len(update.message.entities)):
                if update.message.entities[i].type == 'url':
                    url = update.message.text[int(update.message.entities[i]["offset"]):int(int(
                        update.message.entities[i]["offset"]) + int(update.message.entities[i]["length"]))]
                    msg = msg.replace(url.lower(), url)
            rememberClass.rememberJobs(j, update, msg)

        elif "miguelito dame la lista" in update.message.text.lower():
            gimmeTheSpotifyPlaylistLink(bot, update)
        elif "miguelito añade" in update.message.text.lower() and wasAdded is not True:
            hasUrl = False
            videoTitle = update.message.text.lower().replace("miguelito añade ", "")
            for i in range(len(update.message.entities)):
                if update.message.entities[i].type == 'url':
                    hasUrl = True

            if hasUrl == False:
                if spotifyYouTubeClass.censorYoutubeVideo(videoTitle):
                    update.message.reply_text(
                        'No. :)', reply_to_message_id=update.message.message_id)
                else:
                    spotifyYouTubeClass.connectToSpotifyAndCheckAPI(
                        update, videoTitle, [], None)
            else:
                spotifyYouTubeClass.checkYoutubeSpotifyLinks(update)
        elif "miguelito recomienda" in update.message.text.lower():
            sendMsg(update, spotifyYouTubeClass.recommendAGroup(update), True)

        elif re.search(r'\bpole estonia\b', update.message.text.lower()):
            global lastPoleEstonia
            now = datetime.now()
            if now.date() != lastPoleEstonia.date() and now.hour >= 23:
                update.message.reply_text(
                    'El usuario ' + update.message.from_user.name + ' ha hecho la pole estonia')
                savePoleStats(update)
                lastPoleEstonia = now
        elif "estoniarank" in update.message.text.lower():
            gimmeTheRank(update)

        if godMode and canTalk:
            foundKey = False
            indexArray = 0
            dictionaryIndex = 0
            now = datetime.now()
            while dictionaryIndex < len(botDict["keywords"]) and foundKey is not True:
                if len(botDict["keywords"][dictionaryIndex]["regexpValue"]) > 0:
                    while indexArray < len(botDict["keywords"][dictionaryIndex]["regexpValue"]) and foundKey is not True:
                        regexr = re.compile(
                            botDict["keywords"][dictionaryIndex]["regexpValue"][indexArray])
                        if regexr.search(update.message.text.lower()):
                            if checkIfSendData(bot, update, botDict["keywords"][dictionaryIndex]):
                                botDict["keywords"][dictionaryIndex]["lastTimeSentIt"] = addTime(
                                    now, botDict["keywords"][dictionaryIndex])
                            foundKey = True
                        indexArray += 1
                indexArray = 0
                if len(botDict["keywords"][dictionaryIndex]["msgToCheck"]) > 0:
                    while indexArray < len(botDict["keywords"][dictionaryIndex]["msgToCheck"]) and foundKey is not True:
                        if botDict["keywords"][dictionaryIndex]["msgToCheck"][indexArray]["type"] == "in":
                            if botDict["keywords"][dictionaryIndex]["msgToCheck"][indexArray]["text"] in update.message.text.lower():
                                if checkIfSendData(bot, update, botDict["keywords"][dictionaryIndex]):
                                    botDict["keywords"][dictionaryIndex]["lastTimeSentIt"] = addTime(
                                        now, botDict["keywords"][dictionaryIndex])
                                foundKey = True
                        elif botDict["keywords"][dictionaryIndex]["msgToCheck"][indexArray]["text"] == update.message.text:
                            if checkIfSendData(bot, update, botDict["keywords"][dictionaryIndex]):
                                botDict["keywords"][dictionaryIndex]["lastTimeSentIt"] = addTime(
                                    now, botDict["keywords"][dictionaryIndex])
                            foundKey = True
                        indexArray += 1
                dictionaryIndex += 1

            if foundKey is not True:
                if "random" in update.message.text.lower():
                    indexRandom = getRandomByValue(
                        len(botDict["keywords"]) - 1)
                    sendData(bot, update, botDict["keywords"][indexRandom])
                    if botDict["keywords"][indexRandom]["doubleMsg"] is True:
                        sendData(bot, update, object["doubleObj"])

                elif len(update.message.text) > 7:  # mimimimimimi
                    randomResponse(update, bot)

        if "miguelito mete" in update.message.text.lower():
            addDataToJson(update.message.text.lower())


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def callback_andalucia(bot, job):
    if str(job.context) == str(settings["main"]["groupid"]):
        bot.send_message(chat_id=job.context,
                         text="¡Buenos días, Andalucía! :D")


def callback_bye(bot, job):
    if str(job.context) == str(settings["main"]["groupid"]):
        bot.send_message(chat_id=job.context, text="BYE")
        bot.sendChatAction(chat_id=job.context,
                           action=telegram.ChatAction.UPLOAD_PHOTO)
        bot.sendDocument(chat_id=job.context, document=open(
            dataPath + '/gifs/bye.mp4', 'rb'))


def stop(bot, update):
    if str(update.message.chat_id) == str(settings["main"]["groupid"]) and isAdmin(bot, update):
        global canTalk
        canTalk = None
    else:
        bot.send_message(chat_id=update.message.chat_id, text="JA! No :)")


def restart(bot, update):
    if str(update.message.chat_id) == str(settings["main"]["groupid"]) and isAdmin(bot, update):
        global canTalk
        canTalk = True
    else:
        bot.send_message(chat_id=update.message.chat_id, text="JA! No :)")


def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 1 hour."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]


def downloadPhotos(bot, update):
    if str(update.message.chat_id) == str(settings["main"]["group4photos"]):
        global lastFileDownloadedCount
        file_id = update.message.photo[-1].file_id
        photo = bot.getFile(file_id)
        photo.download(os.path.join(os.path.dirname(__file__)) +
                       '/photos/' + str(lastFileDownloadedCount) + '.jpg')
        lastFileDownloadedCount += 1


def main():
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('seguir', restart))
    dp.add_handler(CommandHandler('parar', stop))
    dp.add_handler(CommandHandler('damelalista', gimmeTheSpotifyPlaylistLink))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))
    dp.add_handler(MessageHandler(Filters.photo, downloadPhotos))

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
