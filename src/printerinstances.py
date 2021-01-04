from zeroconf import ServiceBrowser, Zeroconf
from printerserver import PrinterServer
import threading


class MyListener(object):
	def __init__(self, register, apiKeys):
		self.apiKeys = apiKeys
		self.register = register

	def remove_service(self, zeroconf, stype, name):
		pass

	def add_service(self, zeroconf, stype, name):
		info = zeroconf.get_service_info(stype, name)
		if info is not None:
			s = name.split("\"")
			if len(s) >= 3:
				pName = s[1]
				if pName in self.apiKeys.keys():
					ipaddr = "%d.%d.%d.%d" % (
						info.address[0], info.address[1], info.address[2], info.address[3])
					ps = PrinterServer(self.apiKeys[pName], ipaddr)
					ps.addPlugin("octolapse")
					ps.addPlugin("softwareupdate")
					self.register(pName, ps)
				else:
					print ("Skipping unknown printer: %s - no associated API key" % pName)
			else:
				print ("Unable to parse printer name from (%s)" % name)


class PrinterInstances:
	def __init__(self, plist, settings, registerPrinter):
		self.servers = {}
		self.staticServers = {}
		self.priorServers = {}
		self.apiKeys = {}
		for p in plist:
			apikey= settings.getSetting("apiKey", p)
			ip = settings.getSetting("ip", p)
			if ip is not None:
				ps = PrinterServer(apikey, ip)
				ps.addPlugin("octolapse")
				ps.addPlugin("softwareupdate")
				self.staticServers[p] = ps
			else:
				self.apiKeys[p] = apikey

		self.registerPrinter = registerPrinter
		self.zeroconf = None
		self.newServers = {}
		self.listener = None
		self.browser = None
		self.dtmr = None
		self.tmr = None
		self.refresh()
		for p in self.staticServers.keys():
			self.registerPrinter("add", p)

	def refresh(self):
		if self.zeroconf:
			self.zeroconf.close()

		self.priorServers = self.servers.copy()
		self.newServers = {}

		self.zeroconf = Zeroconf()
		self.listener = MyListener(self.register, self.apiKeys)
		self.browser = ServiceBrowser(self.zeroconf, "_octoprint._tcp.local.", self.listener)

		self.dtmr = threading.Timer(10, self.commit)
		self.dtmr.start()
		self.tmr = threading.Timer(30, self.refresh)
		self.tmr.start()

	def commit(self):
		newSvr = self.newServers.keys()
		priorSvr = self.priorServers.keys()

		for p in priorSvr:
			if p not in newSvr:
				self.registerPrinter("remove", p)

		self.servers = self.newServers.copy()

	def register(self, pName, ps):
		self.newServers[pName] = ps
		if not pName in self.servers.keys():
			self.servers[pName] = ps
			self.registerPrinter("add", pName)

	def getPrinterServer(self, pName):
		try:
			return self.servers[pName]
		except KeyError:
			try:
				return self.staticServers[pName]
			except KeyError:
				return None

	def close(self):
		self.tmr.cancel()
		self.dtmr.cancel()
		self.zeroconf.close()
