import configparser
import re
import os
import subprocess
import shlex

import pprint

INIFILE = "tools.ini"

class ToolBox:
	def __init__(self, folder):
		inifile = os.path.join(folder, INIFILE)
		cfg = configparser.ConfigParser()
		cfg.optionxform = str
		if not cfg.read(inifile):
			print("Settings file %s does not exist." % INIFILE)
			
		self.json = {}
		
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
						print("Unable to parse tool: {}/{}".format(section, k))

	def getTools(self):	
		return self.json
	
	def execute(self, section, tool):
		print("executing tool ({}) from section ({})".format(tool, section))
		args = shlex.split(self.json[section][tool]["command"])
		pprint.pprint(args)
		shell = self.json[section][tool]["needsshell"]
		try:
			#subprocess.Popen(args, shell=shell, stdin=None, stdout=None, stderr=None, close_fds=True)
			subprocess.Popen(args, shell=shell)
		except:
			print("Exception occurred trying to spawn tool process ({}):({})".format(section, tool))
		return
