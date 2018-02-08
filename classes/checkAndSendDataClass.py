#!/usr/bin/env python
# -*- coding: utf-8 -*-

import telegram
import json
import os
import re
from telegram.ext.dispatcher import run_async
from .utils import Utils
from .rememberClass import RememberClass
from datetime import datetime, timedelta
import dateutil.parser
from unidecode import unidecode

class CheckAndSendDataClass:

    # send a random response to the msg
    def randomResponse(self, update, bot):
        randomValue = Utils().getRandomByValue(1400)
        if randomValue < 13 and randomValue > 11:
            self.sendVoice(bot, update, os.path.join(os.path.dirname(__file__)) +
                      '/data' + botDict["audios"][0])
        elif randomValue == 11:
            # dinofaurio feature
            array = update.message.text.split()
            randomIndex = Utils().getRandomByValue(3)
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
                self.sendSticker(bot, update, os.path.join(os.path.dirname(__file__)) +
                            '/data' + botDict["stickers"]["dinofaurioPath"][0], False)
        elif randomValue == 10:
            self.sendSticker(bot, update, os.path.join(os.path.dirname(__file__)) +
                        '/data' + botDict["stickers"]["approvalStickerPath"][0], True)
        elif randomValue <= 9 and randomValue >= 3:
            # send a randomMsg
            randomMsgIndex = Utils().getRandomByValue(len(botDict["randomMsg"]) - 1)
            self.sendMsg(update, botDict["randomMsg"][randomMsgIndex], False)
        elif randomValue < 2:
            # replace vowels to "i"
            update.message.text = unidecode(update.message.text)
            update.message.text = re.sub(
                r'[AEOUaeou]+', 'i', update.message.text)
            update.message.reply_text(
                update.message.text, reply_to_message_id=update.message.message_id)
            randomMsgIndex = Utils.getRandomByValue(
                len(botDict["stickers"]["mimimimiStickerPath"]) - 1)
            dataPath = os.path.join(os.path.dirname(__file__)) + '/data'
            self.sendSticker(bot, update, dataPath + botDict["stickers"], False)

    @staticmethod
    def sendGif(bot, update, pathGif):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=telegram.ChatAction.UPLOAD_PHOTO)
        bot.sendDocument(chat_id=update.message.chat_id,
                         document=open(pathGif, 'rb'))

    @staticmethod
    def sendVoice(bot, update, pathVoice):
        bot.send_voice(chat_id=update.message.chat_id,
                       voice=open(pathVoice, 'rb'))

    @staticmethod
    def sendImg(bot, update, pathImg):
        bot.send_photo(chat_id=update.message.chat_id,
                       photo=open(pathImg, 'rb'))

    @staticmethod
    def sendMsg(update, text, isReply):
        if isReply:
            update.message.reply_text(
                text, reply_to_message_id=update.message.message_id)
        else:
            update.message.reply_text(
                text)

    @staticmethod
    def sendSticker(bot, update, pathSticker, isReply):
        if isReply:
            bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
                pathSticker, 'rb'), reply_to_message_id=update.message.message_id)
        else:
            bot.send_sticker(chat_id=update.message.chat_id, sticker=open(
                pathSticker, 'rb'))

    @staticmethod
    def getPath(arrayData):
        index = Utils().getRandomByValue(len(arrayData) - 1)
        return arrayData[index]


    @run_async
    def sendData(self, bot, update, object):
        dataPath = os.path.join(os.path.dirname(__file__)) + '/data'
        if object["type"] == "voice":
            self.sendVoice(
                bot, update, dataPath + self.getPath(object["path"]))
        elif object["type"] == "gif":
            self.sendGif(
                bot, update, dataPath + self.getPath(object["path"]))
        elif object["type"] == "text":
            self.sendMsg(
                update, self.getPath(object["path"]), object["isReply"])
        elif object["type"] == "img":
            self.sendImg(bot, update, dataPath + self.getPath(object["path"]))
        elif object["type"] == "sticker":
            self.sendSticker(bot, update, dataPath +
                        self.getPath(object["path"]), object["isReply"])



    def checkIfSendData(self, bot, update, object):
        # compare the next time sent it // TODO change keyname
        if len(object["lastTimeSentIt"]) is not 0:
            lastTimeSentIt = datetime.strptime(
                object["lastTimeSentIt"], '%Y-%m-%dT%H:%M:%S.%f')
            now = datetime.now()
            if now.date() > lastTimeSentIt.date():
                # get a randomValue to check if it have to send it or no
                if object["randomMaxValue"] is not 0:
                    randomValue = Utils().getRandomByValue(object["randomMaxValue"])
                    if randomValue <= 1:
                        self.sendData(bot, update, object)
                        if object["doubleMsg"] is True:
                            self.sendData(bot, update, object["doubleObj"])
                        return True
                else:
                    # if randomMaxValue is 0 the data is not censored
                    self.sendData(bot, update, object)
                    if object["doubleMsg"] is True:
                        self.sendData(bot, update, object["doubleObj"])
                    return True
        else:
            # if time is 0 the data is not censored
            self.sendData(bot, update, object)
            if object["doubleMsg"] is True:
                self.sendData(bot, update, object["doubleObj"])
            return True
        return False


    @staticmethod
    def addTime(now, object):
        # increment nextTimeToShowIt
        if object["timeToIncrement"] is not 0:
            timeObject = {'type': object["kindTime"],
                          'value':  object["timeToIncrement"]}
            return RememberClass().checkRememberDate(now, timeObject, None).isoformat()
        else:
            return ""


    def checkIfIsInDictionary(self, bot, update, botDict):
        # check if some keyword of the dictionary is in the msg
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
                        if self.checkIfSendData(bot, update, botDict["keywords"][dictionaryIndex]):
                            botDict["keywords"][dictionaryIndex]["lastTimeSentIt"] = self.addTime(
                                now, botDict["keywords"][dictionaryIndex])
                        foundKey = True
                    indexArray += 1
            indexArray = 0
            if len(botDict["keywords"][dictionaryIndex]["msgToCheck"]) > 0:
                while indexArray < len(botDict["keywords"][dictionaryIndex]["msgToCheck"]) and foundKey is not True:
                    if botDict["keywords"][dictionaryIndex]["msgToCheck"][indexArray]["type"] == "in":
                        if botDict["keywords"][dictionaryIndex]["msgToCheck"][indexArray]["text"] in update.message.text.lower():
                            if self.checkIfSendData(bot, update, botDict["keywords"][dictionaryIndex]):
                                botDict["keywords"][dictionaryIndex]["lastTimeSentIt"] = self.addTime(
                                    now, botDict["keywords"][dictionaryIndex])
                            foundKey = True
                    elif botDict["keywords"][dictionaryIndex]["msgToCheck"][indexArray]["text"] == update.message.text:
                        if self.checkIfSendData(bot, update, botDict["keywords"][dictionaryIndex]):
                            botDict["keywords"][dictionaryIndex]["lastTimeSentIt"] = self.addTime(
                                now, botDict["keywords"][dictionaryIndex])
                        foundKey = True
                    indexArray += 1
            dictionaryIndex += 1

        if foundKey is not True:
            if "random" in update.message.text.lower():
                indexRandom = Utils().getRandomByValue(
                    len(botDict["keywords"]) - 1)
                self.sendData(bot, update, botDict["keywords"][indexRandom])
                if botDict["keywords"][indexRandom]["doubleMsg"] is True:
                    self.sendData(bot, update, object["doubleObj"])

            elif len(update.message.text) > 7:  # mimimimimimi
                self.randomResponse(update, bot)
