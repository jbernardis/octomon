
"""Created on Jun 19, 2018

@author: Jeff
"""
import re

gcRegex = re.compile("[-]?\d+[.]?\d*")

def buildMap(hasZProbe, useM205Q):
	fwmap = {"M92" : ["X", "Y", "Z", "E"],
		"M201" : ["X", "Y", "Z", "E"],
		"M203" : ["X", "Y", "Z", "E"],
		"M204" : ["P", "R", "T"],
		"M301" : ["P", "I", "D"] }

	if useM205Q:
		fwmap["M205"] = ["S", "T", "Q", "X", "Z", "E"]
	else:
		fwmap["M205"] = ["S", "T", "B", "X", "Z", "E"]

	if hasZProbe:
		fwmap["M851"] = ["Z"]

	return fwmap

class FwCollector:
	def __init__(self, hasZProbe, useM205Q):
		self.container = None
		self.hasZProbe = hasZProbe
		self.useM205Q = useM205Q
		self.FwMsgMap = buildMap(hasZProbe, useM205Q)

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

		if cmd in self.FwMsgMap.keys():
			self.container.parseCmd(cmd, msg, self.FwMsgMap[cmd])

	def collectionComplete(self):
		if self.container is None:
			return True

		if self.container.hasAllValues():
			self.container = None
			return True

		return False

def get_float(paramStr, which):
	try:
		v = float(gcRegex.findall(paramStr.split(which)[1])[0])
		return v
	except:
		return None

class FwSettings(object):
	def __init__(self, hasZProbe, useM205Q):
		self.hasZProbe = hasZProbe
		self.useM205Q = useM205Q
		self.FwMsgMap = buildMap(hasZProbe, useM205Q)
		self.hasValues = {}
		self.values = {}
		self.empty()

	def empty(self):
		self.hasValues = {}
		for k in self.FwMsgMap.keys():
			self.hasValues[k] = False

		self.values = {}

	def getValue(self, k):
		try:
			return self.values[k.lower()]
		except:
			return None

	def setValue(self, k, v):
		self.values[k.lower()] = v

	def hasAllValues(self):
		for k in self.hasValues.keys():
			if not self.hasValues[k]:
				return False

		return True

	def parseCmd(self, cmd, msg, tags):
		for p in tags:
			self.setValue("%s_%s" % (cmd, p), get_float(msg, p))
		self.hasValues[cmd] = True
