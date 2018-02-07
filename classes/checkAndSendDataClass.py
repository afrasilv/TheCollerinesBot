#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
from telegram.ext.dispatcher import run_async
from .utils import Utils
from datetime import datetime, timedelta
import dateutil.parser
from unidecode import unidecode

class CheckAndSendDataClass:

    def randomResponse(update, bot):
        randomValue = Utils.getRandomByValue(1400)
        if randomValue < 13 and randomValue > 11:
            sendVoice(bot, update, os.path.join(os.path.dirname(__file__)) +
                      '/data' + botDict["audios"][0])
        elif randomValue == 11:
            array = update.message.text.split()
            randomIndex = Utils.getRandomByValue(3)
            wasChanged = None
            if randomIndex == 0:
                wasChanged = bool(re.search(r'[VvSs]+', update.message.text))
                update.message.text = re.sub(
                    r'[VvSs]+', 'f', update.message.text)
            elif randomIndex == 1:
                wasChanged = bool(re.search(r'[Vv]+', update.message.text))
                update.message.text = re.sub(
                    r'[Vv]+', 'f', update.message.text)
            else:
                wasChanged = bool(
                    re.search(r'[TtVvSsCc]+', update.message.text))
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
            randomMsgIndex = Utils.getRandomByValue(len(botDict["randomMsg"]) - 1)
            sendMsg(update, botDict["randomMsg"][randomMsgIndex], False)
        elif randomValue < 2:
            update.message.text = unidecode(update.message.text)
            update.message.text = re.sub(
                r'[AEOUaeou]+', 'i', update.message.text)
            update.message.reply_text(
                update.message.text, reply_to_message_id=update.message.message_id)
            randomMsgIndex = Utils.getRandomByValue(
                len(botDict["stickers"]["mimimimiStickerPath"]) - 1)
            sendSticker(bot, update, dataPath + botDict["stickers"], False)

    def sendGif(bot, update, pathGif):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=telegram.ChatAction.UPLOAD_PHOTO)
        bot.sendDocument(chat_id=update.message.chat_id,
                         document=open(pathGif, 'rb'))

    def sendVoice(bot, update, pathVoice):
        bot.send_voice(chat_id=update.message.chat_id,
                       voice=open(pathVoice, 'rb'))

    def sendImg(bot, update, pathImg):
        bot.send_photo(chat_id=update.message.chat_id,
                       photo=open(pathImg, 'rb'))

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


    def getPath(arrayData):
        index = Utils.getRandomByValue(len(arrayData) - 1)
        return arrayData[index]


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



    def checkIfSendData(bot, update, object):
        if len(object["lastTimeSentIt"]) is not 0:
            lastTimeSentIt = datetime.strptime(
                object["lastTimeSentIt"], '%Y-%m-%dT%H:%M:%S.%f')
            now = datetime.now()
            if now.date() > lastTimeSentIt.date():
                if object["randomMaxValue"] is not 0:
                    randomValue = Utils.getRandomByValue(object["randomMaxValue"])
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


    def checkIfIsInDictionary(bot, update, botDict):
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
                indexRandom = Utils.getRandomByValue(
                    len(botDict["keywords"]) - 1)
                sendData(bot, update, botDict["keywords"][indexRandom])
                if botDict["keywords"][indexRandom]["doubleMsg"] is True:
                    sendData(bot, update, object["doubleObj"])

            elif len(update.message.text) > 7:  # mimimimimimi
                randomResponse(update, bot)
