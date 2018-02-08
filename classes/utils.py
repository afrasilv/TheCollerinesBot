#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
from random import randint

class Utils:

    @staticmethod
    def getRandomByValue(value):
        # get random value to 0 <= value
        randomValue = randint(0, value)
        return randomValue

    @staticmethod
    def loadFile(fileName, isOrdered, errorInit):
        data = {}
        try:
            if isOrdered:
                json_file = open(fileName, 'r')
                data = json.load(json_file, object_pairs_hook=OrderedDict)
            else:
                json_file = open(fileName, encoding="utf-8")
                data = json.load(json_file)
                data = json.dumps(
                    {'data': data})
                data = json.loads(data)
                data = data["data"]
        except IOError:
            data = errorInit
        return data

    @staticmethod
    def saveFile(fileName, fileData):
        with open('dataDictionary.json', 'w') as outfile:
            json.dump(botDict, outfile)

    @staticmethod
    def replaceStr(msg, str):
        # remove the first (or selected number) occurrence of str and a empty space
        if str in msg:
            msg = msg.replace(str + " ", "", 1)
        return msg
