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

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

dataPath = os.path.join(os.path.dirname(__file__)) + '/data'

randomMsg = ['qué pasa, jamboide', 'no seas bobo', 'basta', 'no te rayes', 'no te agobies', 'vale', 'qué dices, prim',
             'ok', 'geniaaaaaal', 'fataaaaaal', '/geniaaaaaal', '/fataaaaaal', 'Myrath macho', '/jajj', '/jjaj', '/yee', "A topeth!"]
random4GodMsg = ['dime', 'basta', 'déjame',
                 'ahora no', 'ZzZzzzZzz', '¿qué te pasa?']
mimimimiStickerPath = ['/stickers/mimimi.webp',
                       '/stickers/mimimi1.webp', '/stickers/mimimi2.webp']
m3AudiosPath = ['/voices/m3Javi.ogg',
                '/voices/m3Javig.ogg', '/voices/m3Feli.ogg']
huehuehuePath = ['/gifs/huehuehue.mp4',
                 '/gifs/huehuehue1.mp4']
sectaImgPath = ['/imgs/secta.jpg',
                '/imgs/secta1.jpg']
lastPoleEstonia = datetime.now() - timedelta(days=1)
canTalk = True
godMode = True
firstMsg = True
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
    if (msgArray[0] == "a" and "la" in msgArray[1]):
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
    if randomValue < 15 and randomValue > 11:
        bot.send_voice(chat_id=update.message.chat_id, voice=open(
            os.path.join(os.path.dirname(__file__)) +
            '/data' + '/voices/yord.ogg', 'rb'))
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
                '/data' + '/stickers/alef.webp', 'rb'))
    elif randomValue == 10:
        bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
            os.path.join(os.path.dirname(__file__)) +
            '/data' + '/stickers/approval.webp', 'rb'), reply_to_message_id=update.message.message_id)
    elif randomValue <= 9 and randomValue >= 3:
        randomMsgIndex = getRandomByValue(len(randomMsg) - 1)
        update.message.reply_text(
            randomMsg[randomMsgIndex], reply_to_message_id=update.message.message_id)
    elif randomValue < 2:
        update.message.text = unidecode(update.message.text)
        update.message.text = re.sub(r'[AEOUaeou]+', 'i', update.message.text)
        update.message.reply_text(
            update.message.text, reply_to_message_id=update.message.message_id)
        randomMsgIndex = getRandomByValue(len(mimimimiStickerPath) - 1)
        bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
            dataPath + mimimimiStickerPath[randomMsgIndex], 'rb'))


def sendGif(bot, update, pathGif):
    bot.sendChatAction(chat_id=update.message.chat_id,
                       action=telegram.ChatAction.UPLOAD_PHOTO)
    bot.sendDocument(chat_id=update.message.chat_id,
                     document=open(pathGif, 'rb'))


def sendVoice(bot, update, pathVoice):
    bot.send_voice(chat_id=update.message.chat_id, voice=open(pathVoice, 'rb'))


def sendImg(bot, update, pathImg):
    bot.send_photo(chat_id=update.message.chat_id, photo=open(pathImg, 'rb'))


def isAdmin(bot, update):
    if update.message.from_user.username != None and update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
        return True
    else:
        return None


def startJobs(bot, update):
    now = datetime.now() - timedelta(days=1)
    now = now.replace(hour=19, minute=00)
    job_daily = j.run_daily(callback_andalucia, now.time(), days=(
        0, 1, 2, 3, 4, 5, 6), context=update.message.chat_id)
    now = now.replace(hour=2, minute=00)
    job_daily = j.run_daily(callback_bye, now.time(), days=(
        0, 1, 2, 3, 4, 5, 6), context=update.message.chat_id)
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
        if results['tracks']['total'] == 0:
            results = sp.search(q=videoTags, limit=1)
        if results['tracks']['total'] == 0 and video != None:
            videoTags = ""
            videoTags = gimmeTags(video, videoTags, 2)
            results = sp.search(q=videoTags, limit=1)
        if results['tracks']['total'] == 0 and video != None:
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

    scope = 'playlist-modify playlist-modify-public user-library-read playlist-modify-private'
    token = util.prompt_for_user_token(settings["spotify"]["spotifyuser"], scope, client_id=settings["spotify"]
                                       ["spotifyclientid"], client_secret=settings["spotify"]["spotifysecret"], redirect_uri='http://localhost:8000')
    sp = spotipy.Spotify(auth=token)
    results = sp.user_playlist_add_tracks(
        settings["spotify"]["spotifyuser"], settings["spotify"]["spotifyplaylist"], idsToAdd)


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
    return videoTitle


def connectToSpotifyAndCheckAPI(update, videoTitle, videoTags, video):
    client_credentials_manager = SpotifyClientCredentials(
        client_id=settings["spotify"]["spotifyclientid"], client_secret=settings["spotify"]["spotifysecret"])
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    sp.trace = False
    results = callSpotifyApi(videoTitle, videoTags, video, sp, update)

    if results == None or (results['tracks']['total'] != None and results['tracks']['total'] == 0):
        saveDataSong(update, None)
    else:
        addToSpotifyPlaylist(results, update)


def censorYoutubeVideo(videoTitle):
    json_file = open(os.path.join(os.path.dirname(
        __file__), "youtubeCensor.json"), 'r')
    youtubeCensorData = json.load(json_file)

    for item in youtubeCensorData:
        if item in videoTitle:
            return True
    return None


def echo(bot, update):
    global canTalk
    global firstMsg
    global godMode

    if str(update.message.chat_id) == str(settings["main"]["groupid"]):
        if update.message.text != None and "miguelito para" == update.message.text.lower():
            stop(bot, update)
        elif update.message.text != None and "miguelito sigue" == update.message.text.lower():
            restart(bot, update)
        elif update.message.text != None and "miguelito al coma" == update.message.text.lower() and update.message.from_user.username == settings["main"]["fatherid"]:
            godMode = None
        elif update.message.text != None and "miguelito vuelve" == update.message.text.lower() and update.message.from_user.username == settings["main"]["fatherid"]:
            godMode = True

        if godMode and canTalk:
            for i in range(len(update.message.entities)):
                if update.message.entities[i].type == 'url' and ('youtu.be' in update.message.text.lower() or 'youtube.com' in update.message.text.lower()):
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
                                connectToSpotifyAndCheckAPI(
                                    update, videoTitle, videoTags, video)
                            else:
                                saveDataSong(update, None)
                    except:
                        saveDataSong(update, None)

            # startJobs
            if firstMsg:
                startJobs(bot, update)
                firstMsg = None

            if "miguelito recuerda" in update.message.text.lower() or "miguelito recuerdame" in update.message.text.lower() or "miguelito recuérdame" in update.message.text.lower():
                msg = update.message.text.lower()
                msgSplit = msg.split(" ")
                msg = msg.replace(
                    msgSplit[0] + " " + msgSplit[1] + " ", "")
                rememberJobs(bot, update, msg)

            # voice
            elif re.search(r'\bvalencia\b', update.message.text.lower()):
                randomValue = getRandomByValue(4)
                if randomValue <= 1:
                    sendVoice(
                        bot, update, dataPath + '/voices/teamvalencia.ogg')
            elif re.search(r'\<3\b', update.message.text.lower()):
                randomAudioIndex = getRandomByValue(len(m3AudiosPath) - 1)
                sendVoice(bot, update, dataPath + m3AudiosPath[randomAudioIndex])
            elif re.search(r'\bgeni[a]+[a-zA-Z]+\b', update.message.text.lower()):
                randomValue = getRandomByValue(5)
                if randomValue <= 1:
                    sendVoice(
                        bot, update, dataPath + '/voices/geniaaa.ogg')
            elif re.search(r'\brocoso\b', update.message.text.lower()) or re.search(r'\bciclado\b', update.message.text.lower()) or re.search(r'\bciclao\b', update.message.text.lower()):
                randomValue = getRandomByValue(3)
                if randomValue <= 1:
                    sendVoice(
                        bot, update, dataPath + '/voices/rocoso.ogg')
            elif re.search(r'\bmétodo willy\b', update.message.text.lower()) or re.search(r'\bmetodo willy\b', update.message.text.lower()):
                sendVoice(
                    bot, update, dataPath + '/voices/willy.ogg')

            # gif
            elif re.search(r'\bpfff[f]+\b', update.message.text.lower()) or '...' == update.message.text:
                randomValue = getRandomByValue(5)
                if randomValue <= 1:
                    sendGif(
                        bot, update,  dataPath + '/gifs/pffff.mp4')
            elif "gif del fantasma" in update.message.text.lower():
                sendGif(bot, update,
                        dataPath + '/gifs/fantasma.mp4')
            elif "bukkake" in update.message.text.lower() or "galletitas" in update.message.text.lower():
                sendGif(bot, update,
                        dataPath + '/gifs/perro.mp4')
            elif "no me jodas" in update.message.text.lower() or "no me digas" in update.message.text.lower():
                randomValue = getRandomByValue(5)
                if randomValue <= 1:
                    sendGif(
                        bot, update, dataPath + '/gifs/ferran_agua.mp4')
            elif "tengo cara de que me importe" in update.message.text.lower():
                sendGif(bot, update, dataPath+
                        '/gifs/importar.mp4')
            elif "all right" in update.message.text.lower() or re.search(r'\bestupendo\b', update.message.text.lower()) or re.search(r'\bmaravilloso\b', update.message.text.lower()):
                randomValue = getRandomByValue(5)
                if randomValue <= 1:
                    sendGif(
                        bot, update, dataPath + '/gifs/ferran_thumb.mp4')
            elif "momento cabra" in update.message.text.lower():
                sendGif(
                    bot, update, dataPath + '/gifs/momento_cabra.mp4')
            elif re.search(r'\bcabra\b', update.message.text.lower()):
                randomValue = getRandomByValue(4)
                if randomValue <= 1:
                    sendGif(
                        bot, update, dataPath + '/gifs/cabra_scream.mp4')
            elif unidecode(u'qué?') == unidecode(update.message.text.lower()) or "que?" == update.message.text.lower():
                sendGif(bot, update,
                        dataPath+ '/gifs/cabra.mp4')
            elif re.search(r'\brandom\b', update.message.text.lower()):
                randomValue = getRandomByValue(4)
                if randomValue <= 1:
                    sendGif(
                        bot, update, dataPath + '/gifs/random.mp4')
            elif re.search(r'\breviento\b', update.message.text.lower()) or re.search(r'\brebiento\b', update.message.text.lower()):
                randomValue = getRandomByValue(2)
                if randomValue <= 1:
                    sendGif(
                        bot, update, dataPath + '/gifs/acho_reviento.mp4')
            elif re.search(r'\bpatriarcado\b', update.message.text.lower()):
                randomValue = getRandomByValue(3)
                if randomValue <= 1:
                    sendGif(
                        bot, update, dataPath + '/gifs/patriarcado.mp4')
            elif re.search(r'\bchoca\b', update.message.text.lower()):
                sendGif(bot, update,
                        dataPath + '/gifs/choca.mp4')
            elif re.search(r'\bbro\b', update.message.text.lower()):
                sendGif(bot, update,
                        dataPath+ '/gifs/cat_bro.mp4')
            elif "templo" in update.message.text.lower() or "gimnasio" in update.message.text.lower():
                randomValue = getRandomByValue(4)
                if randomValue <= 1:
                    sendGif(
                        bot, update,  dataPath + '/gifs/templo.mp4')
            elif re.search(r'\bhuehue[hue]+\b', update.message.text.lower()):
                randomHuehuehueIndex = getRandomByValue(len(huehuehuePath) - 1)
                sendGif(bot, update, dataPath + huehuehuePath[randomHuehuehueIndex])
            elif re.search(r'\byee\b', update.message.text.lower()):
                if "/yee" not in update.message.text.lower():
                    sendGif(bot, update,
                            dataPath + '/gifs/yee.mp4')
            elif re.search(r'\bstrike\b', update.message.text.lower()) or re.search(r'\breport\b', update.message.text.lower()):
                randomValue = getRandomByValue(4)
                if randomValue <= 1:
                    sendGif(
                        bot, update, dataPath+ '/gifs/strike.mp4')

            # messages
            elif re.search(r'\bsalud\b', update.message.text.lower()):
                randomValue = getRandomByValue(3)
                if randomValue <= 1:
                    update.message.reply_text(
                        'El dedo en el culo es la salud y el bienestar', reply_to_message_id=update.message.message_id)
            elif re.search(r'\bllegas tarde\b', update.message.text.lower()) or re.search(r'\bllega tarde\b', update.message.text.lower()):
                update.message.reply_text(
                    'como Collera', reply_to_message_id=update.message.message_id)
            elif unidecode(u'eres rápido') in unidecode(update.message.text.lower()) or "eres rapido" in update.message.text.lower():
                update.message.reply_text(
                    'no como Collera', reply_to_message_id=update.message.message_id)
            elif re.search(r'\bkele puto\b', update.message.text.lower()):
                update.message.reply_text(' /keleputo ')
            elif re.search(r'\bsum41\b', update.message.text.lower()) or re.search(r'\bsum 41\b', update.message.text.lower()):
                update.message.reply_text('100% confirmados para el Download')
            elif re.search(r'\bjjaj[ja]*\b', update.message.text.lower()):
                update.message.reply_text('/jjaj')
            elif re.search(r'\bjajj[ja]*\b', update.message.text.lower()):
                update.message.reply_text('/jajj')
            elif "miguelito dame la lista" in update.message.text.lower():
                gimmeTheSpotifyPlaylistLink(bot, update)
            elif "miguelito añade" in update.message.text.lower():
                videoTitle = update.message.text.lower().replace("miguelito añade ", "")

                if censorYoutubeVideo(videoTitle):
                    update.message.reply_text(
                        'No. :)', reply_to_message_id=update.message.message_id)
                else:
                    connectToSpotifyAndCheckAPI(update, videoTitle, [], None)
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
            elif re.search(r'\bzyzz\b', update.message.text.lower()):
                randomValue = getRandomByValue(3)
                if randomValue <= 1:
                    update.message.reply_text(' /zetayzetazeta ')
            elif re.search(r'\bdios\b', update.message.text.lower()):
                randomValue = getRandomByValue(5)
                if randomValue < 1:
                    indexMsg = getRandomByValue(len(random4GodMsg) - 1)
                    update.message.reply_text(
                        random4GodMsg[indexMsg], reply_to_message_id=update.message.message_id)
            elif re.search(r'\btxumino\b', update.message.text.lower()):
                if "/txumino" not in update.message.text.lower():
                    update.message.reply_text(' /txumino ')

            # imgs
            elif "kulevra tirano" in update.message.text.lower() or "drop the ban" in update.message.text.lower():
                sendImg(bot, update,
                        dataPath+ '/imgs/dropban.jpg')
            elif re.search(r'\bsecta\b', update.message.text.lower()):
                randomSectaIndex = getRandomByValue(len(sectaImgPath) - 1)
                sendImg(bot, update, dataPath + sectaImgPath[randomSectaIndex])
            elif re.search(r'\bnazi\b', update.message.text.lower()):
                randomValue = getRandomByValue(3)
                if randomValue < 1:
                    sendImg(bot, update,
                            dataPath + '/imgs/nazi.jpg')

            # stickers
            elif re.search(r'\bprog\b', update.message.text.lower()):
                bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
                    dataPath + '/stickers/prog.webp', 'rb'), reply_to_message_id=update.message.message_id)
            elif re.search(r'\bsend nudes\b', update.message.text.lower()) or "send noodles" in update.message.text.lower():
                bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
                    dataPath + '/stickers/sendnudes.webp', 'rb'), reply_to_message_id=update.message.message_id)
            elif re.search(r'\bficha\b', update.message.text.lower()) or re.search(r'\bfichas\b', update.message.text.lower()):
                bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
                    dataPath + '/stickers/ficha.webp', 'rb'), reply_to_message_id=update.message.message_id)
            elif re.search(r'\bbutanero\b', update.message.text.lower()) or "bombona" in update.message.text.lower():
                bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
                    dataPath + '/stickers/butanero.webp', 'rb'), reply_to_message_id=update.message.message_id)
            elif re.search(r'\bkylo\b', update.message.text.lower()):
                bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
                    dataPath + '/stickers/kylo.webp', 'rb'), reply_to_message_id=update.message.message_id)
            elif re.search(r'\bkostra\b', update.message.text.lower()):
                bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
                    dataPath + '/stickers/costra.webp', 'rb'), reply_to_message_id=update.message.message_id)
            elif re.search(r'\bhuevo\b', update.message.text.lower()) or re.search(r'\bhuevos\b', update.message.text.lower()):
                randomValue = getRandomByValue(5)
                if randomValue < 1:
                    bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
                        dataPath + '/stickers/huevo.webp', 'rb'), reply_to_message_id=update.message.message_id)
            elif re.search(r'\blp\b', update.message.text.lower()) or re.search(r'\blinkin park\b', update.message.text.lower()):
                randomValue = getRandomByValue(3)
                if randomValue <= 1:
                    bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
                        dataPath + '/stickers/lp.webp', 'rb'), reply_to_message_id=update.message.message_id)
            elif len(update.message.text) > 7:  # mimimimimimi
                randomResponse(update, bot)


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
