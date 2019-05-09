#!/usr/bin/env python
import requests 
import os
import io

from opclient import Client

TIMEOUT = 0.3
RC_READ_TIMEOUT = 598
RC_CONNECT_TIMEOUT = 599

class PrintHead:
	def __init__(self, printer):
		self.printer = printer
		self.url = "http://%s/api/printer/printhead" % self.printer.getIpAddr()
		self.header = {"X-Api-Key": self.printer.getApiKey()}

	def jog(self, vector, absolute=False, speed=None, to=TIMEOUT):
		x = 0
		y = 0
		z = 0
		if len(vector) >= 1:
			x = vector[0]

		if len(vector) >= 2:
			y = vector[1]

		if len(vector) >= 3:
			z = vector[2]

		payload = {"command": "jog", "x": x, "y": y, "z": z, "absolute": absolute}
		if not speed is None:
			payload["speed"] = speed

		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def home(self, xyz, to=TIMEOUT):
		axes = []
		if xyz[0]:
			axes.append("x")
		if xyz[1]:
			axes.append("y")
		if xyz[2]:
			axes.append("z")

		payload = {"command": "home", "axes": axes}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def feedrate(self, factor, to=TIMEOUT):
		payload = {"command": "feedrate", "factor": factor}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

class Tool:
	def __init__(self, printer):
		self.printer = printer
		self.url = "http://%s/api/printer/tool" % self.printer.getIpAddr()
		self.header = {"X-Api-Key": self.printer.getApiKey()}

	def state(self, to=TIMEOUT):
		try:
			r = requests.get(self.url, data={}, headers=self.header, timeout=to)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None
		try:
			j = r.json()
		except:
			j = None
		return r.status_code, j

	def target(self, targetVals, to=TIMEOUT):
		targets = {}
		for t in targetVals.keys():
			targets["tool%s" % t] = targetVals[t]

		payload = {"command": "target", "targets": targets}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT


	def offset(self, offsetVals, to=TIMEOUT):
		offsets = {}
		for i in range(len(offsetVals)):
			offsets["tool%d" % i] = offsetVals[i]

		payload = {"command": "offset", "offsets": offsets}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT


	def select(self, toolx, to=TIMEOUT):
		payload = {"command": "select", "tool": "tool%d" % toolx}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def selectByName(self, tooln, to=TIMEOUT):
		payload = {"command": "select", "tool": "%s" % tooln}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def extrude(self, length, to=TIMEOUT):
		payload = {"command": "extrude", "amount": length}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def retract(self, length, to=TIMEOUT):
		payload = {"command": "extrude", "amount": -length}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT


class Bed:
	def __init__(self, printer):
		self.printer = printer
		self.url = "http://%s/api/printer/bed" % self.printer.getIpAddr()
		self.header = {"X-Api-Key": self.printer.getApiKey()}

	def state(self, to=TIMEOUT):
		try:
			r = requests.get(self.url, data={}, headers=self.header, timeout=to)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None

		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def target(self, targetVal, to=TIMEOUT):
		payload = {"command": "target", "target": targetVal}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def offset(self, offsetVal, to=TIMEOUT):
		payload = {"command": "offset", "offset": offsetVal}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT


class Job:
	def __init__(self, printer):
		self.printer = printer
		self.url = "http://%s/api/job" % self.printer.getIpAddr()
		self.header = {"X-Api-Key": self.printer.getApiKey()}

	def state(self, to=TIMEOUT):
		try:
			r = requests.get(self.url, data={}, headers=self.header, timeout=to)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None
		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def start(self, to=TIMEOUT):
		payload = {"command": "start"}
		try:
			r = requests.post(self.url, json=payload, headers=self.header, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def cancel(self, to=TIMEOUT):
		payload = {"command": "cancel"}
		try:
			r = requests.post(self.url, json=payload, headers=self.header, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def restart(self, to=TIMEOUT):
		payload = {"command": "restart"}
		try:
			r = requests.post(self.url, json=payload, headers=self.header, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def pause(self, to=TIMEOUT):
		payload = {"command": "pause", "action": "pause"}
		try:
			r = requests.post(self.url, json=payload, headers=self.header, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def resume(self, to=TIMEOUT):
		payload = {"command": "pause", "action": "resume"}
		try:
			r = requests.post(self.url, json=payload, headers=self.header, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def preheat(self, to=TIMEOUT):
		url = "http://%s/api/plugin/preheat" % self.printer.getIpAddr()
		payload = {"command": "preheat"}
		try:
			r = requests.post(url, json=payload, headers=self.header, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT


class Plugin:
	def __init__(self, printer, pname):
		self.printer = printer
		self.name = pname
		self.url = "http://%s/plugin/%s" % (self.printer.getIpAddr(), self.name)
		self.header = {"X-Api-Key": self.printer.getApiKey()}

	def get(self, command, to=TIMEOUT):
		url = "%s/%s" % (self.url, command)
		try:
			r = requests.get(url, data={}, headers=self.header, timeout=to)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None
		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def post(self, command, payload={}, to=TIMEOUT):
		url = "%s/%s" % (self.url, command)
		try:
			r = requests.post(url, json=payload, headers=self.header, timeout=to)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None
		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

class GFile:
	def __init__(self, printer):
		self.printer = printer
		self.url = "http://%s/api/files" % self.printer.getIpAddr()
		self.header = {"X-Api-Key": self.printer.getApiKey()}

	def uploadFile(self, fn, n=None, to=TIMEOUT):
		if n is None:
			bn = os.path.basename(fn)
		else:
			bn = n

		location = "/local"

		files = {'file': (bn, open(fn, 'rb'), 'application/octet-stream')}
		try:
			r = requests.post(self.url + location, files=files, headers=self.header, timeout=to)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None
		
		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def selectFile(self, origin, path, prt=False, to=TIMEOUT):
		location = "/%s" % origin
		if path.startswith("/"):
			location += path
		else:
			location += "/" + path
		payload = {"command": "select", "print": prt}
		try:
			r = requests.post(self.url + location, json=payload, headers=self.header, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def downloadFileByName(self, origin, path, to=TIMEOUT):
		location = "/%s" % origin
		if path.startswith("/"):
			location += path
		else:
			location += "/" + path
		try:
			r = requests.get(self.url + location, headers=self.header, timeout=to)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, "Request for information Failed"
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, "Request for information Failed"
		
		if r.status_code >= 400:
			return r.status_code, "Request for information Failed"

		try:
			j = r.json()
			url = j["refs"]["download"]
		except:
			return 404, "URL not returned"

		return self.downloadFile(url, to=to)

	def deleteFile(self, origin, path, to=TIMEOUT):
		location = "/%s" % origin
		if path.startswith("/"):
			location += path
		else:
			location += "/" + path

		try:
			r = requests.delete(self.url + location, headers=self.header, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def uploadString(self, s, n, to=TIMEOUT):
		files = {'file': (n, io.StringIO(s), 'application/octet-stream')}
		location = "/local"
		try:
			r = requests.post(self.url + location, files=files, headers=self.header, timeout=to)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None
		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def listFiles(self, local=True, sd=False, recursive=False, to=TIMEOUT):
		location = ""
		if local and not sd:
			location = "/local"
		elif sd and not local:
			location = "/sdcard"

		if recursive:
			location += "?recursive=true"

		try:
			req = requests.get(self.url + location, headers=self.header, timeout=to)
		except:
			print("exception")
			return None

		if req.status_code >= 400:
			print("return code %d" % req.status_code)
			return None

		finfo = req.json()
		if "files" not in finfo.keys():
			return {}

		fl = finfo["files"]
		result = {}
		for f in fl:
			if "name" in f.keys():
				if "origin" in f.keys():
					o = f['origin']
				else:
					o = 'local'

				if not o in result.keys():
					result[o] = []

				if "refs" in f.keys() and "download" in f["refs"].keys():
					url = f["refs"]["download"]
				else:
					url = None
				if "size" in f.keys():
					sz = f["size"]
				else:
					sz = 0
				if "date" in f.keys():
					dt = f["date"]
				else:
					dt = 0

				result[o].append((f["name"], url, sz, dt))

		return result

	def downloadFile(self, url, to=TIMEOUT):
		req = requests.get(url, headers=self.header, timeout=to)
		try:
			rv = req.text
		except:
			rv = None

		return req.status_code, rv

class PrinterServer:
	def __init__(self, apiKey, ipAddr):
		self.apiKey = apiKey
		self.ipAddr = ipAddr
		self.header = {"X-Api-Key": self.apiKey}
		self.printHead = PrintHead(self)
		self.tool = Tool(self)
		self.bed = Bed(self)
		self.job = Job(self)
		self.gfile = GFile(self)
		self.plugins = {}
		self.opClient = Client("http://%s" % self.ipAddr, self.apiKey)
		self.opSocket = None

		self.jobUpdate = None
		self.messageUpdate = None
		self.logUpdate = None
		self.progressUpdate = None
		self.stateUpdate = None
		self.pluginUpdate = None

	def addPlugin(self, pname):
		self.plugins[pname] = Plugin(self, pname)
		
	def getPlugin(self, pname):
		if pname in self.plugins:
			return self.plugins[pname]
		
		return None

	def getIpAddr(self):
		return self.ipAddr

	def getApiKey(self):
		return self.apiKey

	def subscribe(self, reportMap):
		try:
			self.jobUpdate = reportMap["job"]
		except KeyError:
			self.jobUpdate = None

		try:
			self.messageUpdate = reportMap["message"]
		except KeyError:
			self.messageUpdate = None

		try:
			self.logUpdate = reportMap["log"]
		except KeyError:
			self.logUpdate = None

		try:
			self.progressUpdate = reportMap["progress"]
		except KeyError:
			self.progressUpdate = None

		try:
			self.stateUpdate = reportMap["state"]
		except KeyError:
			self.stateUpdate = None

		try:
			self.pluginUpdate = reportMap["plugin"]
		except KeyError:
			self.pluginUpdate = None

		if self.opSocket is None:
			self.opSocket = self.opClient.create_socket(on_message=self.onSocketMessage)

	def unsubscribe(self):
		if self.opSocket:
			self.opSocket.disconnect()
			if os.name == 'posix':
				try:
					self.opSocket.wait(1)
				except:
					pass
			else:
				self.opSocket.wait()

		self.opSocket = None

	def onSocketMessage(self, ws, mtype, mbody):
		if mtype == "plugin":
			if callable(self.pluginUpdate):
				self.pluginUpdate(mbody)
				return

		if mtype != "current":
			return

		if callable(self.messageUpdate):
			try:
				ml = mbody["messages"]
			except KeyError:
				ml = []

			for m in ml:
				self.messageUpdate(m)

		if callable(self.logUpdate):
			try:
				logs = mbody["logs"]
			except KeyError:
				logs = []

			self.logUpdate(logs)

		if callable(self.jobUpdate) and "job" in mbody.keys():
			self.jobUpdate(mbody["job"])

		if callable(self.progressUpdate) and "progress" in mbody.keys():
			self.progressUpdate(mbody["progress"])

		if callable(self.stateUpdate) and "state" in mbody.keys():
			self.stateUpdate(mbody["state"])

	def state(self, exclude=[], to=TIMEOUT):
		url = "http://%s/api/printer" % self.ipAddr
		if len(exclude) > 0:
			url += "?exclude=%s" % ",".join(exclude)
		try:
			r = requests.get(url, data={}, headers=self.header, timeout=to)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None
		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def command(self, cmd, to=TIMEOUT):
		url = "http://%s/api/printer/command" % self.ipAddr
		payload = {"command": cmd}
		try:
			r = requests.post(url, json=payload, headers=self.header, timeout=to)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None

		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv
	
	def getConnectionInfo(self, to=TIMEOUT):
		url = "http://%s/api/connection" % self.ipAddr
		try:
			r = requests.get(url, data={}, headers=self.header, timeout=to)
		except requests.exceptions.ReadTimeout:
			return None, None
		except requests.exceptions.ConnectTimeout:
			return None, None

		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def connect(self, port="/dev/ttyACM0", baudrate=115200, to=TIMEOUT):
		url = "http://%s/api/connection" % self.ipAddr
		payload = {"command": "connect",
				"port": port,
				"baudrate": baudrate,
				"save": True,
				"autoconnect": True
				}
		try:
			r = requests.post(url, json=payload, headers=self.header, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT
	
	def disconnect(self, to=TIMEOUT):
		url = "http://%s/api/connection" % self.ipAddr
		payload = {"command": "disconnect"}
		try:
			r = requests.post(url, json=payload, headers=self.header, timeout=to)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def close(self):
		self.unsubscribe()
