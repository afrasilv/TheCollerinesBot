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
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
from youtubeApi import YoutubeAPI
from operator import itemgetter
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


def checkHourToRemember(msg, timeObject):
    # Check if hour
    msgArray = msg.split(" ")
    msgHourData = msgArray[0]
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
    elif isinstance(msgHourData, int):
        timeObject["hour"] = msgHourData
        msg = msg.replace(msgHourData + " ", "", 1)

    return msg, timeObject


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


def replaceStr(msg, str):
    if str in msg:
        msg = msg.replace(str + " ", "", 1)
    return msg


def checkDayDifference(diffDayCount, now, timeObject):
    if diffDayCount == 0 and "hor" in timeObject and now.hour <= int(timeObject["hour"]):
        if "min" in timeObject and now.minute < int(timeObject["min"]):
            print("nice hour")
        else:
            diffDayCount += 1
    return diffDayCount


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


def rememberJobs(bot, update, msg):
    timeObject = checkTimeToRemember(msg)
    usernameToNotify, msg = getUsernameToNotify(msg, update)
    # with key words in config json
    if timeObject != None:
        msg = msg.replace(timeObject["name"] + " ", "", 1)
        msg, timeObject = checkHourToRemember(msg, timeObject)

        msgArray = msg.split(" ")
        msg = replaceStr(msg, "que")

        now = datetime.now()
        now = checkRememberDate(now, timeObject, None)
        if datetime.now() > now:
            now = now + timedelta(days=1)

    # with dd/mm/yyyy config
    elif re.search(r'([0-9]+/[0-9]+/[0-9]+)', msg):
        msgArray = msg.split(" ")
        msg = replaceStr(msg, "el")

        dateWithoutSplit = re.search(r'([0-9]+/[0-9]+/[0-9]+)', msg)
        dateString = dateWithoutSplit.group(0)
        dateSplitted = dateString.split('/')
        now = datetime.now()

        msg = replaceStr(msg, dateString)
        msg = replaceStr(msg, "que")

        now = now.replace(int(dateSplitted[2]), int(
            dateSplitted[1]), int(dateSplitted[0]))
        timeObject = {}
        msg, timeObject = checkHourToRemember(msg, timeObject)
        now = checkRememberDate(now, timeObject, None)
        if datetime.now() > now:
            now = now + timedelta(days=1)

    # with weekday config
    else:
        msgArray = msg.split(" ")
        msg = replaceStr(msg, "el")

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

        msg = replaceStr(msg, "que")

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
    j.run_once(callback_remember, now, context=update.message.chat_id)


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


def gimmeMyMemories():
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


def callback_remember(bot, job):
    msg = gimmeMyMemories()
    bot.send_message(chat_id=job.context, text="EH! " +
                     msg["username"] + " te recuerdo que " + msg["msg"])


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


def getRandomByValue(value):
    randomValue = randint(0, value)
    return randomValue


def randomResponse(update, bot):
    randomValue = getRandomByValue(1400)
    if randomValue < 13 and randomValue > 11:
        bot.send_voice(chat_id=update.message.chat_id, voice=open(
            os.path.join(os.path.dirname(__file__)) +
            '/data' + botDict["audios"][0], 'rb'))
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
            bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
                os.path.join(os.path.dirname(__file__)) +
                '/data' + botDict["stickers"]["dinofaurioPath"][0], 'rb'))
    elif randomValue == 10:
        bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
            os.path.join(os.path.dirname(__file__)) +
            '/data' + botDict["stickers"]["approvalStickerPath"][0], 'rb'), reply_to_message_id=update.message.message_id)
    elif randomValue <= 9 and randomValue >= 3:
        randomMsgIndex = getRandomByValue(len(botDict["randomMsg"]) - 1)
        update.message.reply_text(
            botDict["randomMsg"][randomMsgIndex], reply_to_message_id=update.message.message_id)
    elif randomValue < 2:
        update.message.text = unidecode(update.message.text)
        update.message.text = re.sub(r'[AEOUaeou]+', 'i', update.message.text)
        update.message.reply_text(
            update.message.text, reply_to_message_id=update.message.message_id)
        randomMsgIndex = getRandomByValue(
            len(botDict["stickers"]["mimimimiStickerPath"]) - 1)
        bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
            dataPath + botDict["stickers"]["mimimimiStickerPath"][randomMsgIndex], 'rb'))


def isAdmin(bot, update):
    if update.message.from_user.username != None and update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
        return True
    else:
        return None


def startJobs(bot, update):
    now = datetime.now() - timedelta(days=1)
    now = now.replace(hour=getRandomByValue(24), minute=getRandomByValue(60))
    job_daily = j.run_daily(callback_andalucia, now.time(), days=(
        0, 1, 2, 3, 4, 5, 6), context=update.message.chat_id)
    # now = now.replace(hour=2, minute=00)
    # job_daily = j.run_daily(callback_bye, now.time(), days=(
    #     0, 1, 2, 3, 4, 5, 6), context=update.message.chat_id)
    data = loadMemories()
    for item in data:
        j.run_once(callback_remember, dateutil.parser.parse(
            item["when"]), context=update.message.chat_id)


def gimmeTags(video, videoTags, maxTags):
    tagsIndex = 0
    if video['snippet'].get('tags') != None:
        while tagsIndex < len(video['snippet']['tags']) and tagsIndex < maxTags:
            videoTags += video['snippet']['tags'][tagsIndex] + " "
            tagsIndex += 1
    return videoTags


def saveDataSong(update, sendMessage):
    data = []
    try:
        json_file = open('data.txt', 'r')
        data = json.load(json_file)
    except IOError:
        data = []

    data.append(update.message.text)
    with open('data.txt', 'w') as outfile:
        json.dump(data, outfile)

    if sendMessage:
        update.message.reply_text(
            "No está. :_(", reply_to_message_id=update.message.message_id)


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


def callSpotifyApi(videoTitle, videoTags, video, sp, update):
    try:
        results = sp.search(q=videoTitle, limit=1)
        if int(results['tracks']['total']) == 0:
            results = sp.search(q=videoTags, limit=1)
        if int(results['tracks']['total']) == 0 and video != None:
            videoTags = ""
            videoTags = gimmeTags(video, videoTags, 2)
            results = sp.search(q=videoTags, limit=1)
        if int(results['tracks']['total']) == 0 and video != None:
            videoTags = ""
            videoTags = gimmeTags(video, videoTags, 1)
            results = sp.search(q=videoTags, limit=1)
        return results
    except:
        saveDataSong(update, True)


def addToSpotifyPlaylist(results, update):
    resultTracksList = results['tracks']
    idsToAdd = []

    for j in range(len(results['tracks']['items'])):
        idsToAdd.insert(0, results['tracks']['items'][j]['id'])

    callSpotifyApiToAddSong(idsToAdd)


def callSpotifyApiToAddSong(idsToAdd):
    scope = 'playlist-modify playlist-modify-public user-library-read playlist-modify-private'
    token = util.prompt_for_user_token(settings["spotify"]["spotifyuser"], scope, client_id=settings["spotify"]
                                       ["spotifyclientid"], client_secret=settings["spotify"]["spotifysecret"], redirect_uri='http://localhost:8000')
    sp = spotipy.Spotify(auth=token)
    results = sp.user_playlist_add_tracks(
        settings["spotify"]["spotifyuser"], settings["spotify"]["spotifyplaylist"], idsToAdd)


def recommendAGroup(bot, update):
    scope = 'playlist-modify playlist-modify-public user-library-read playlist-modify-private'
    token = util.prompt_for_user_token(settings["spotify"]["spotifyuser"], scope, client_id=settings["spotify"]
                                       ["spotifyclientid"], client_secret=settings["spotify"]["spotifysecret"], redirect_uri='http://localhost:8000')
    sp = spotipy.Spotify(auth=token)
    offsetPlaylist = getRandomByValue(1100)
    # user_playlist_tracks(user, playlist_id=None, fields=None, limit=100, offset=0, market=None)
    results = sp.user_playlist_tracks(
        settings["spotify"]["spotifyuser"], settings["spotify"]["spotifyplaylist"], None, 100, offsetPlaylist)
    playlistData = json.dumps(results)
    playlistData = json.loads(playlistData)
    if len(playlistData["items"]) > 0:
        index = getRandomByValue(len(playlistData["items"]) - 1)
        track = playlistData["items"][index]["track"]
        sendMsg(bot, update, "Ahí te va " +
                track["external_urls"]["spotify"], True)
    else:
        sendMsg(bot, update, "BOOM, me salí de la lista :/", True)


def gimmeTheSpotifyPlaylistLink(bot, update):
    update.message.reply_text(
        'ahí te va! ' + settings["spotify"]["spotifyplaylistlink"])


def replaceYouTubeVideoName(videoTitle):
    videoTitle = re.sub(r'\([\[a-zA-Z :\'0-9\]]+\)', '', videoTitle)
    videoTitle = re.sub(r'\[[\[a-zA-Z :\'0-9\]]+\]', '', videoTitle)
    videoTitle = videoTitle.lower().replace("official video", "")
    videoTitle = videoTitle.lower().replace("official music video", "")
    videoTitle = videoTitle.lower().replace("videoclip oficiai", "")
    videoTitle = videoTitle.lower().replace("video clip oficiai", "")
    videoTitle = videoTitle.lower().replace("videoclip", "")
    videoTitle = videoTitle.lower().replace("\"", "")
    return videoTitle


def connectToSpotifyAndCheckAPI(update, videoTitle, videoTags, video):
    client_credentials_manager = SpotifyClientCredentials(
        client_id=settings["spotify"]["spotifyclientid"], client_secret=settings["spotify"]["spotifysecret"])
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    sp.trace = False
    results = callSpotifyApi(videoTitle, videoTags, video, sp, update)

    if results == None or (results['tracks']['total'] != None and results['tracks']['total'] == 0):
        saveDataSong(update, None)
        return False
    else:
        addToSpotifyPlaylist(results, update)
        return True


def censorYoutubeVideo(videoTitle):
    json_file = open(os.path.join(os.path.dirname(
        __file__), "youtubeCensor.json"), 'r')
    youtubeCensorData = json.load(json_file)

    for item in youtubeCensorData:
        if item in videoTitle:
            return True
    return None


def sendGif(bot, update, pathGif):
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=telegram.ChatAction.UPLOAD_PHOTO)
    bot.sendDocument(chat_id=update.message.chat_id,
                     document=open(pathGif, 'rb'))


def sendVoice(bot, update, pathVoice):
    bot.send_voice(chat_id=update.message.chat_id, voice=open(pathVoice, 'rb'))


def sendImg(bot, update, pathImg):
    bot.send_photo(chat_id=update.message.chat_id, photo=open(pathImg, 'rb'))


def sendMsg(bot, update, text, isReply):
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


def sendData(bot, update, object):
    if object["type"] == "voice":
        sendVoice(
            bot, update, dataPath + getPath(object["path"]))
    elif object["type"] == "gif":
        sendGif(
            bot, update, dataPath + getPath(object["path"]))
    elif object["type"] == "text":
        sendMsg(
            bot, update, getPath(object["path"]), object["isReply"])
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
        return checkRememberDate(now, timeObject, None).isoformat()
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


def youtubeLink(bot, update):
    try:
        videoid = ""
        if 'youtu.be' not in update.message.text.lower():
            videoid = update.message.text.split('v=')
            videoid = videoid[1].split(' ')[0]
            videoid = videoid.split('&')[0]
        else:
            videoid = update.message.text.split('youtu.be/')
            videoid = videoid[1].split(' ')[0]
            videoid = videoid.split('&')[0]
        youtube = YoutubeAPI(
            {'key': settings["main"]["youtubeapikey"]})
        video = youtube.get_video_info(videoid)
        videoTitle = video['snippet']['title'].lower()
        videoTitle = replaceYouTubeVideoName(videoTitle)

        if censorYoutubeVideo(videoTitle):
            update.message.reply_text(
                '...', reply_to_message_id=update.message.message_id)
        else:
            videoTags = ""
            tagsIndex = 0
            videoTags = gimmeTags(video, videoTags, 3)
            if videoTitle != None and videoTags != None:
                return connectToSpotifyAndCheckAPI(
                    update, videoTitle, videoTags, video)
            else:
                saveDataSong(update, None)
    except:
        saveDataSong(update, None)
    return False


def spotifyLink(bot, update):
    try:
        trackid = update.message.text.split("track/")
        trackid = trackid[1].split(" ")
        if "?" in trackid:
            trackid = trackid[1].split("?")
        trackid = trackid[0]
        callSpotifyApiToAddSong([trackid])
        return True
    except:
        saveDataSong(update, None)
    return False


def checkYoutubeSpotifyLinks(bot, update):
    for i in range(len(update.message.entities)):
        if update.message.entities[i].type == 'url' and ('youtu.be' in update.message.text.lower() or 'youtube.com' in update.message.text.lower()):
            return youtubeLink(bot, update)
        elif update.message.entities[i].type == 'url' and 'spotify.com' in update.message.text:
            return spotifyLink(bot, update)

## miguelito mete text##hola__in#0##0#min###huehuehuehue
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


@run_async
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
        wasAdded = checkYoutubeSpotifyLinks(bot, update)

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
            rememberJobs(bot, update, msg)

        elif "miguelito dame la lista" in update.message.text.lower():
            gimmeTheSpotifyPlaylistLink(bot, update)
        elif "miguelito añade" in update.message.text.lower() and wasAdded is not True:
            hasUrl = False
            videoTitle = update.message.text.lower().replace("miguelito añade ", "")
            for i in range(len(update.message.entities)):
                if update.message.entities[i].type == 'url':
                    hasUrl = True

            if hasUrl == False:
                if censorYoutubeVideo(videoTitle):
                    update.message.reply_text(
                        'No. :)', reply_to_message_id=update.message.message_id)
                else:
                    connectToSpotifyAndCheckAPI(
                        update, videoTitle, [], None)
            else:
                checkYoutubeSpotifyLinks(bot, update)
        elif "miguelito recomienda" in update.message.text.lower():
            recommendAGroup(bot, update)

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
                    indexRandom = getRandomByValue(len(botDict["keywords"]))
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
