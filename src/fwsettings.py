
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

ZProbeMap = {"M851": ["Z"]}

gcRegex = re.compile("[-]?\d+[.]?\d*")


class FwCollector:
	def __init__(self):
		self.container = None

	def start(self, container, haszprobe):
		self.container = container
		self.haszprobe = haszprobe
		self.container.empty()

	def checkFwCommand(self, msg):
		if self.container is None:
			return
		try:
			cmd = msg.split()[0].upper()
		except IndexError:
			return

		if cmd in FwMsgMap.keys():
			self.container.parseCmd(cmd, msg, FwMsgMap[cmd])
		elif self.haszprobe and cmd in ZProbeMap.keys():
			self.container.parseCmd(cmd, msg, ZProbeMap[cmd])

	def collectionComplete(self):
		if self.container is None:
			return True

		if self.container.hasAllValues():
			self.container = None
			return True

		return False


FWC = FwCollector()


class FwSettings(object):
	def __init__(self, hasZProbe):
		self.hasZProbe = hasZProbe
		self.empty()

	def empty(self):
		self.hasValues = {}
		for k in FwMsgMap.keys():
			self.hasValues[k] = False
		if self.hasZProbe:
			for k in ZProbeMap.keys():
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

	def parseCmd(self, cmd, msg, tags):
		for p in tags:
			self.setValue("%s_%s" % (cmd, p), self.__get_float(msg, p))
		self.hasValues[cmd] = True

	def __get_float(self, paramStr, which):
		try:
			v = float(gcRegex.findall(paramStr.split(which)[1])[0])
			return v
		except:
			return None
