from printerserver import PrinterServer
import socket
import time

class PrinterInstances:
	def __init__(self, plist, settings, registerPrinter):

#		self.closed = False
		self.apiKeys = {}
		self.dnslist = [settings.getSetting("dnsname", p) for p in plist]
		self.plist = [p for p in plist]
		for p in plist:
			self.apiKeys[p] = settings.getSetting("apiKey", p)

		self.servers = {}

		self.registerPrinter = registerPrinter
		self.refresh()

	def refresh(self):
		for px in range(len(self.plist)):
			pdns = self.dnslist[px]
			pName = self.plist[px]
			dns = "%s.local" % pdns
			try:
				s = socket.getaddrinfo(dns, 80)
				if len(s) < 1:
					ipAddr = None
				else:
					if s[0][0] == socket.AddressFamily.AF_INET6:
						ipAddr = "[%s]" % s[0][4][0]
					else:
						ipAddr = s[0][4][0]
			except:
				ipAddr = None

			if ipAddr is None:
				if pName in self.servers:
					self.registerPrinter("remove", pName)
					del(self.servers[pName])
				else:
					pass
					#print("Ignoring printer removal of printer that is already removed")
			else:
				if pName not in self.servers:
					ps = PrinterServer(self.apiKeys[pName], ipAddr)
					ps.addPlugin("octolapse")
					ps.addPlugin("softwareupdate")
					self.servers[pName] = ps

					self.registerPrinter("add", pName)
				else:
					pass
					#print("skipping printer already registered")

	def getPrinterServer(self, pName):
		try:
			return self.servers[pName]
		except IndexError:
			return None
