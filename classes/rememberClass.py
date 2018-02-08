#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
from .utils import Utils
from datetime import datetime, timedelta
import dateutil.parser
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

class RememberClass:

    weekdayConstant = ['lunes', 'martes', 'miércoles',
                       'jueves', 'viernes', 'sábado', 'domingo']

    def checkHourToRemember(self, msg, timeObject):
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

    def checkRememberDate(self, now, timeObject, isWeekday):
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

    def checkDayDifference(self, diffDayCount, now, timeObject):
        if diffDayCount == 0 and "hor" in timeObject and now.hour <= int(timeObject["hour"]):
            if "min" in timeObject and now.minute < int(timeObject["min"]):
                print("nice hour")
            else:
                diffDayCount += 1
        return diffDayCount

    def getUsernameToNotify(self, msg, update):
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


    def rememberJobs(self, bot, job_queue, update, msg):
        timeObject = self.checkTimeToRemember(msg)
        usernameToNotify, msg = self.getUsernameToNotify(msg, update)
        # with key words in config json
        if timeObject != None:
            msg = msg.replace(timeObject["name"] + " ", "", 1)
            msg, timeObject = self.checkHourToRemember(msg, timeObject)

            msgArray = msg.split(" ")
            msg = Utils.replaceStr(msg, "que")

            now = datetime.now()
            now = self.checkRememberDate(now, timeObject, None)
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
            msg, timeObject = self.checkHourToRemember(msg, timeObject)
            now = self.checkRememberDate(now, timeObject, None)
            if datetime.now() > now:
                now = now + timedelta(days=1)

        # with weekday config
        else:
            msgArray = msg.split(" ")
            msg = Utils.replaceStr(msg, "el")

            found = None
            index = 0
            while index < len(self.weekdayConstant) and found != True:
                if self.weekdayConstant[index] in msg:
                    found = True
                    msg = msg.replace(self.weekdayConstant[index] + " ", "", 1)
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
            msg, timeObject = self.checkHourToRemember(msg, timeObject)
            now = self.checkRememberDate(now, timeObject, True)
            diffDayCount = self.checkDayDifference(
                diffDayCount, datetime.now(), timeObject)
            now = now + timedelta(days=diffDayCount)

        update.message.reply_text(
            "Vale", reply_to_message_id=update.message.message_id)
        now = now.replace(second=0)
        self.saveMessageToRemember(
            usernameToNotify, msg, now.isoformat())
        return now

    @staticmethod
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

    @staticmethod
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

    def gimmeMyMemories(self):
        data = self.loadMemories()
        data = sorted(
            data,
            key=lambda x: datetime.strptime(x['when'], '%Y-%m-%dT%H:%M:%S.%f'), reverse=True
        )
        # msg = data[0]
        msg = data.pop()
        with open('memories.json', 'w') as outfile:
            json.dump(data, outfile)
        return msg

    def callback_remember(self, bot, chat_id):
        msg = self.gimmeMyMemories()
        bot.send_message(chat_id=chat_id, text="EH! " +
                         msg["username"] + " te recuerdo que " + msg["msg"])

    @staticmethod
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
