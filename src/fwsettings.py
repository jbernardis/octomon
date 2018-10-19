
"""Created on Jun 19, 2018

@author: Jeff
"""
import re

FwMsgMap = {"M92": ["X", "Y", "Z", "E"],
            "M201": ["X", "Y", "Z", "E"],
            "M203": ["X", "Y", "Z", "E"],
            "M204": ["P", "R", "T"],
            "M205": ["S", "T", "B", "X", "Z", "E"],
            "M301": ["P", "I", "D"]}

gcRegex = re.compile("[-]?\d+[.]?\d*")


class FwCollector:
    def __init__(self):
        self.container = None

    def start(self, container):
        self.container = container
        self.container.empty()

    def checkFwCommand(self, msg):
        if self.container is None:
            return
        try:
            cmd = msg.split()[0].upper()
        except IndexError:
            return

        if cmd in FwMsgMap.keys():
            self.container.parseCmd(cmd, msg)

    def collectionComplete(self):
        if self.container is None:
            return True

        if self.container.hasAllValues():
            self.container = None
            return True

        return False


FWC = FwCollector()


class FwSettings(object):
    def __init__(self):
        self.empty()

    def empty(self):
        self.hasValues = {}
        for k in FwMsgMap.keys():
            self.hasValues[k] = False

        self.values = {}

    def getValue(self, k):
        try:
            return self.values[k.lower()]
        except Exception:
            return None

    def setValue(self, k, v):
        self.values[k.lower()] = v

    def hasAllValues(self):
        for k in self.hasValues.keys():
            if not self.hasValues[k]:
                return False

        return True

    def parseCmd(self, cmd, msg):
        if cmd in FwMsgMap.keys():
            for p in FwMsgMap[cmd]:
                self.setValue("%s_%s" % (cmd, p), self.__get_float(msg, p))
            self.hasValues[cmd] = True

    def __get_float(self, paramStr, which):
        try:
            v = float(gcRegex.findall(paramStr.split(which)[1])[0])
            return v
        except:
            return None

