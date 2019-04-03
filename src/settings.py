import configparser
import os

INIFILE = "octo.ini"

LOOKBACKMINUTES = 10
XCOUNT = LOOKBACKMINUTES * 60


def parseBoolean(val, defaultVal):
	lval = val.lower()

	if lval == 'true' or lval == 't' or lval == 'yes' or lval == 'y':
		return True

	if lval == 'false' or lval == 'f' or lval == 'no' or lval == 'n':
		return False

	return defaultVal


class Settings:
	def __init__(self, folder):
		self.cmdfolder = folder
		self.inifile = os.path.join(folder, INIFILE)
		self.cfg = None
		self.reinit()

	def reinit(self):
		self.cfg = configparser.ConfigParser()
		self.cfg.optionxform = str
		if not self.cfg.read(self.inifile):
			print("Settings file %s does not exist." % INIFILE)

	def getSetting(self, setting, section="global", dftValue=None):
		try:
			v = self.cfg.get(section, setting)
		except configparser.NoOptionError:
			if section != "global":
				# setting does not exist for the printer - see if there is a global setting behind it
				try:
					v = self.cfg.get("global", setting)
				except configparser.NoOptionError:
					self.setSetting(setting, str(dftValue), section)
					return dftValue
					
			else:
				self.setSetting(setting, str(dftValue), section)
				return dftValue

		try:
			return eval(v)
		except:
			if v == "true":
				return True
			elif v == "false":
				return False

			return eval("\"%s\"" % v)

	def setSetting(self, setting, val, section="global"):
		try:
			self.cfg.add_section(section)
		except configparser.DuplicateSectionError:
			pass

		self.cfg.set(section, setting, val)

		try:
			cfp = open(self.inifile, 'w')
		except:
			print ("Unable to open settings file %s for writing" % self.inifile)
			return

		self.cfg.write(cfp)
		cfp.close()
		self.reinit()

	def save(self):
		try:
			cfp = open(self.inifile, 'wb')
		except:
			print ("Unable to open settings file %s for writing" % self.inifile)
			return
		self.cfg.write(cfp)
		cfp.close()
