import configparser
import re
import os
import subprocess
import shlex

INIFILE = "tools.ini"

class ToolBox:
	def __init__(self, folder):
		inifile = os.path.join(folder, INIFILE)
		cfg = configparser.ConfigParser()
		cfg.optionxform = str
		self.json = {}
		if not cfg.read(inifile):
			return

		for section in cfg.sections():
			self.json[section] = {}
			for (k, v) in cfg.items(section):
				if k == "order":
					self.json[section][k] = re.split("\s*,\s*", v)
				else:
					tl = re.split("\s*,\s*", v)
					if len(tl) == 4:
						if tl[3].lower() == "true":
							needsshell = True
						else:
							needsshell = False
						self.json[section][k] = {"command": tl[0], "icon": tl[1], "helptext": tl[2], "needsshell": needsshell}
					elif len(tl) == 3:
						self.json[section][k] = {"command": tl[0], "icon": tl[1], "helptext": tl[2], "needsshell": False}
					elif len(tl) == 2:
						self.json[section][k] = {"command": tl[0], "icon": tl[1], "helptext": "", "needsshell": False}
					else:
						pass

	def getTools(self):
		return self.json

	def execute(self, section, tool):
		args = shlex.split(self.json[section][tool]["command"])
		shell = self.json[section][tool]["needsshell"]
		try:
			subprocess.Popen(args, shell=shell)
		except:
			pass

		return
