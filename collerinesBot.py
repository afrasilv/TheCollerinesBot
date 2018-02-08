#!/usr/bin/env python
# -*- coding: utf-8 -*-

import telegram
import re
import pickle
from unidecode import unidecode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from datetime import datetime, timedelta
import dateutil.parser
from configparser import ConfigParser
from collections import OrderedDict
import json
import os
import sys
from threading import Thread
import logging
from classes.spotifyYouTubeClass import SpotifyYouTubeClass
from classes.checkAndSendDataClass import CheckAndSendDataClass
from classes.utils import Utils

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


# Load the config file with keys and tokens
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


config = ConfigParser()
settings = ini_to_dict(os.path.join(os.path.dirname(__file__), "config.ini"))
updater = Updater(settings["main"]["token"])

# Init the job_queue
j = updater.job_queue

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.


def start(bot, update):
    update.message.reply_text(
        'Hola prim!', reply_to_message_id=update.message.message_id)


def help(bot, update):
    update.message.reply_text('asdqwe')

# Check if user is an admin
def isAdmin(bot, update):
    if update.message.from_user.username != None and update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
        return True
    else:
        return None

# start rememberjobs and other callbacks
def startJobs(bot, update):
    now = datetime.now() - timedelta(days=1)
    restTime = Utils.getRandomByValue(2)
    now = now.replace(hour=17 + restTime, minute=Utils.getRandomByValue(59))
    job_daily = j.run_daily(callback_andalucia, now.time(), days=(
        0, 1, 2, 3, 4, 5, 6), context=update.message.chat_id)
    # now = now.replace(hour=2, minute=00)
    # job_daily = j.run_daily(callback_bye, now.time(), days=(
    #     0, 1, 2, 3, 4, 5, 6), context=update.message.chat_id)
    data = loadMemories()
    for item in data:
        j.run_once(callback_remember(bot, update.message.chat_id),
                   dateutil.parser.parse(item["when"]), context=update.message.chat_id)


def savePoleStats(update):
    username = update.message.from_user.name.replace("@", "")
    data = Utils.loadFile('polestats.json', True, [
                          {'username': username, 'count': 0}])

    found = None
    i = 0
    while i < len(data):
        if data[i]['username'] == username:
            data[i]['count'] += 1
            found = True
        i += 1
    if found == None:
        data.append({'username': username, 'count': 1})

    Utils.saveFile('polestats.json', data)


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

# Load dictionary data with all bot data
def loadDictionary(bot, update):
    global botDict
    botDict = Utils.loadFile('dataDictionary.json', False, {})

# compare the hour that user set in the message
def checkHourToRemember(msg, timeObject):
    # Check if hour
    msgArray = msg.split(" ")
    msgHourData = msgArray[0]
    # remove "a la" or "a las" of the msg
    if (msgArray[0] == "a" and ("la" in msgArray[1] or "las" in msgArray[1])):
        msgHourData = msgArray[2]
        msg = msg.replace(msgArray[0] + " " + msgArray[1] + " ", "", 1)
    if ":" in msgHourData:
        hourDataSplitted = msgHourData.split(":")
        timeObject["hour"] = hourDataSplitted[0]
        timeObject["min"] = hourDataSplitted[1]
        msg = msg.replace(msgHourData + " ", "", 1)
        if int(timeObject["min"]) > 59:
            hours = int(timeObject["hour"]) + 1
            mins = int(timeObject["min"]) - 59
            timeObject["hour"] = hours
            timeObject["min"] = mins
    # just the hour
    elif isinstance(msgHourData, int):
        timeObject["hour"] = msgHourData
        msg = msg.replace(msgHourData + " ", "", 1)

    return msg, timeObject

# set the right datetime to remember by weekday and/or hh:mm dataParsed
def checkRememberDate(now, timeObject, isWeekday):
    if isWeekday == None:
        if "type" in timeObject and timeObject["type"] == "day":
            now = now + timedelta(days=int(timeObject["value"]))
        elif "type" in timeObject and timeObject["type"] == "hour":
            now = now + timedelta(hours=int(timeObject["value"]))

    if "hour" in timeObject and timeObject["hour"] != None:
        now = now.replace(hour=int(timeObject["hour"]))
        if timeObject["min"] != None:
            now = now.replace(minute=int(timeObject["min"]))
    return now

# check if hh:mm selected is > than actual to increment a day
def checkDayDifference(diffDayCount, now, timeObject):
    if diffDayCount == 0 and "hor" in timeObject and now.hour <= int(timeObject["hour"]):
        if "min" in timeObject and now.minute < int(timeObject["min"]):
            print("nice hour")
        else:
            diffDayCount += 1
    return diffDayCount

# check if introduced name is in the json to get the username
def getUsernameToNotify(msg, update):
    data = []
    try:
        json_file = open('userNames.json', 'r')
        data = json.load(json_file)
    except IOError:
        data = []

    msgArray = msg.split(" ")
    index = 0
    while index < len(data):
        if data[index]["name"] in msgArray[1]:
            msg = msg.replace(msgArray[0] + " " + msgArray[1] + " ", "", 1)
            return data[index]["value"], msg
        index += 1
    return update.message.from_user.name, msg

# Parse message to get all data
def rememberJobs(bot, job_queue, update, msg):
    #compare time with the dateConfig.json
    timeObject = checkTimeToRemember(msg)
    # check is have username in the msg
    usernameToNotify, msg = getUsernameToNotify(msg, update)
    # with key words in config json
    if timeObject != None:
        msg = msg.replace(timeObject["name"] + " ", "", 1)
        msg, timeObject = checkHourToRemember(msg, timeObject)

        msgArray = msg.split(" ")
        msg = Utils.replaceStr(msg, "que")

        now = datetime.now()
        now = checkRememberDate(now, timeObject, None)
        if datetime.now() > now:
            now = now + timedelta(days=1)

    # with dd/mm/yyyy config
    elif re.search(r'([0-9]+/[0-9]+/[0-9]+)', msg):
        msgArray = msg.split(" ")
        msg = Utils.replaceStr(msg, "el")

        dateWithoutSplit = re.search(r'([0-9]+/[0-9]+/[0-9]+)', msg)
        dateString = dateWithoutSplit.group(0)
        dateSplitted = dateString.split('/')
        now = datetime.now()

        msg = Utils.replaceStr(msg, dateString)
        msg = Utils.replaceStr(msg, "que")

        now = now.replace(int(dateSplitted[2]), int(
            dateSplitted[1]), int(dateSplitted[0]))
        timeObject = {}
        msg, timeObject = checkHourToRemember(msg, timeObject)
        now = checkRememberDate(now, timeObject, None)
        if datetime.now() > now:
            now = now + timedelta(days=1)

    # with weekday config or hh:mm
    else:
        msgArray = msg.split(" ")
        msg = Utils.replaceStr(msg, "el")

        found = None
        index = 0
        while index < len(weekdayConstant) and found != True:
            if weekdayConstant[index] in msg:
                found = True
                msg = msg.replace(weekdayConstant[index] + " ", "", 1)
            else:
                index += 1
        now = datetime.now()
        todayNumber = now.weekday()
        diffDayCount = 0
        # check how many days is from today
        if found:
            if int(todayNumber) < index:
                diffDayCount = index - int(todayNumber) + 1
            else:
                diffDayCount = (6 - int(todayNumber)) + index + 1

        msg = Utils.replaceStr(msg, "que")

        timeObject = {}
        msg, timeObject = checkHourToRemember(msg, timeObject)
        now = checkRememberDate(now, timeObject, True)
        diffDayCount = checkDayDifference(
            diffDayCount, datetime.now(), timeObject)
        now = now + timedelta(days=diffDayCount)

    update.message.reply_text(
        "Vale", reply_to_message_id=update.message.message_id)
    now = now.replace(second=0)
    saveMessageToRemember(
        usernameToNotify, msg, now.isoformat())
    return now

# save message in a json_file
def saveMessageToRemember(username, msg, when):
    data = []
    try:
        json_file = open('memories.json', 'r')
        data = json.load(json_file)
        data.append({'username': username, 'msg': msg, 'when': when})
    except IOError:
        data = [{'username': username, 'msg': msg, 'when': when}]

    with open('memories.json', 'w') as outfile:
        json.dump(data, outfile)

# load memories to execute the jobs
def loadMemories():
    try:
        json_file = open('memories.json', 'r')
        data = json.load(json_file)
    except IOError:
        data = {}
    data = json.dumps(
        {'data': data})
    data = json.loads(data)
    return data["data"]

# get the first memory
def gimmeMyMemories(self):
    data = loadMemories()
    data = sorted(
        data,
        key=lambda x: datetime.strptime(x['when'], '%Y-%m-%dT%H:%M:%S.%f'), reverse=True
    )
    # msg = data[0]
    msg = data.pop()
    with open('memories.json', 'w') as outfile:
        json.dump(data, outfile)
    return msg


def callback_remember(bot, chat_id):
    msg = gimmeMyMemories()
    bot.send_message(chat_id=chat_id, text="EH! " +
                     msg["username"] + " te recuerdo que " + msg["msg"])

# Load dateConfig file and check if some key is in the msg
def checkTimeToRemember(msg):
    data = []
    try:
        json_file = open('dateConfig.json', 'r')
        data = json.load(json_file)
    except IOError:
        return None
    index = 0
    while index < len(data):
        if data[index]["name"] in msg:
            return data[index]
        index += 1
    return None


# miguelito mete text##hola__in#0##0#min###huehuehuehue
def addDataToJson(text):
    global downloadData
    msg = Utils.replaceStr(text, "miguelito mete")
    msgSplitted = msg.split("#")
    msg = Utils.replaceStr(msg, msgSplitted[0])
    # add randoms messages
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
    Utils.saveFile('dataDictionary.json', botDict)


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

        spotifyAPI = SpotifyYouTubeClass()
        wasAdded = False
        wasAdded = spotifyAPI.checkYoutubeSpotifyLinks(update)

        # startJobs
        if firstMsg:
            # load config data and jobs
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
            responseTime = rememberJobs(bot, j, update, msg)
            j.run_once(callback_remember(
                bot, update.message.chat_id), responseTime, context=update.message.chat_id)

        elif "miguelito dame la lista" in update.message.text.lower():
            gimmeTheSpotifyPlaylistLink(bot, update)
        elif "miguelito añade" in update.message.text.lower() and wasAdded is not True:
            hasUrl = False
            videoTitle = update.message.text.lower().replace("miguelito añade ", "")
            # check if there is an url in the msg
            for i in range(len(update.message.entities)):
                if update.message.entities[i].type == 'url':
                    hasUrl = True

            if hasUrl == False:
                if spotifyAPI.censorYoutubeVideo(videoTitle):
                    update.message.reply_text(
                        'No. :)', reply_to_message_id=update.message.message_id)
                else:
                    # check if msg is like <song> <band> // numb linkin park to search in spotify api
                    spotifyAPI.connectToSpotifyAndCheckAPI(
                        update, videoTitle, [], None)
            else:
                spotifyAPI.checkYoutubeSpotifyLinks(update)
        elif "miguelito recomienda" in update.message.text.lower():
            #send a random song of the spotify playlist
            sendMsg(update, spotifyAPI.recommendAGroup(update), True)

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

        elif godMode and canTalk:
            CheckAndSendDataClass().checkIfIsInDictionary(bot, update, botDict)

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
    # download all photos of the group
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
