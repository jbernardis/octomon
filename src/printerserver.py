#!/usr/bin/env python
import requests 
import os
import io

import pprint

from opclient import Client

TIMEOUT = 0.3
RC_READ_TIMEOUT = 598
RC_CONNECT_TIMEOUT = 599

class PrintHead:
	def __init__(self, printer):
		self.printer = printer
		self.url = "http://%s/api/printer/printhead" % self.printer.getIpAddr()
		self.header = {"X-Api-Key": self.printer.getApiKey()}

	def jog(self, vector, absolute=False, speed=None):
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
			r = requests.post(self.url, headers=self.header, json=payload, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def home(self, xyz):
		axes = []
		if xyz[0]:
			axes.append("x")
		if xyz[1]:
			axes.append("y")
		if xyz[2]:
			axes.append("z")

		payload = {"command": "home", "axes": axes}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def feedrate(self, factor):
		payload = {"command": "feedrate", "factor": factor}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=TIMEOUT)
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

	def state(self):
		try:
			r = requests.get(self.url, data={}, headers=self.header, timeout=TIMEOUT)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None
		try:
			j = r.json()
		except:
			j = None
		return r.status_code, j

	def target(self, targetVals):
		targets = {}
		for t in targetVals.keys():
			targets["tool%s" % t] = targetVals[t]

		payload = {"command": "target", "targets": targets}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT


	def offset(self, offsetVals):
		offsets = {}
		for i in range(len(offsetVals)):
			offsets["tool%d" % i] = offsetVals[i]

		payload = {"command": "offset", "offsets": offsets}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT


	def select(self, toolx):
		payload = {"command": "select", "tool": "tool%d" % toolx}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def selectByName(self, tooln):
		payload = {"command": "select", "tool": "%s" % tooln}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def extrude(self, length):
		payload = {"command": "extrude", "amount": length}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def retract(self, length):
		payload = {"command": "extrude", "amount": -length}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=TIMEOUT)
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

	def state(self):
		try:
			r = requests.get(self.url, data={}, headers=self.header, timeout=TIMEOUT)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None

		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def target(self, targetVal):
		payload = {"command": "target", "target": targetVal}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def offset(self, offsetVal):
		payload = {"command": "offset", "offset": offsetVal}
		try:
			r = requests.post(self.url, headers=self.header, json=payload, timeout=TIMEOUT)
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

	def state(self):
		try:
			r = requests.get(self.url, data={}, headers=self.header, timeout=TIMEOUT)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None
		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def start(self):
		payload = {"command": "start"}
		try:
			r = requests.post(self.url, json=payload, headers=self.header, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def cancel(self):
		payload = {"command": "cancel"}
		try:
			r = requests.post(self.url, json=payload, headers=self.header, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def restart(self):
		payload = {"command": "restart"}
		try:
			r = requests.post(self.url, json=payload, headers=self.header, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def pause(self):
		payload = {"command": "pause", "action": "pause"}
		try:
			r = requests.post(self.url, json=payload, headers=self.header, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def resume(self):
		payload = {"command": "pause", "action": "resume"}
		try:
			r = requests.post(self.url, json=payload, headers=self.header, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def preheat(self):
		url = "http://%s/api/plugin/preheat" % self.printer.getIpAddr()
		payload = {"command": "preheat"}
		try:
			r = requests.post(url, json=payload, headers=self.header, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT


class GFile:
	def __init__(self, printer):
		self.printer = printer
		self.url = "http://%s/api/files" % self.printer.getIpAddr()
		self.header = {"X-Api-Key": self.printer.getApiKey()}

	def uploadFile(self, fn, n=None):
		if n is None:
			bn = os.path.basename(fn)
		else:
			bn = n

		location = "/local"

		files = {'file': (bn, open(fn, 'rb'), 'application/octet-stream')}
		try:
			r = requests.post(self.url + location, files=files, headers=self.header, timeout=5)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None
		
		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def selectFile(self, origin, path, prt=False):
		location = "/%s" % origin
		if path.startswith("/"):
			location += path
		else:
			location += "/" + path
		payload = {"command": "select", "print": prt}
		try:
			r = requests.post(self.url + location, json=payload, headers=self.header, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def downloadFileByName(self, origin, path):
		location = "/%s" % origin
		if path.startswith("/"):
			location += path
		else:
			location += "/" + path
		try:
			r = requests.get(self.url + location, headers=self.header, timeout=TIMEOUT)
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

		return self.downloadFile(url)

	def deleteFile(self, origin, path):
		location = "/%s" % origin
		if path.startswith("/"):
			location += path
		else:
			location += "/" + path

		try:
			r = requests.delete(self.url + location, headers=self.header, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT

	def uploadString(self, s, n):
		files = {'file': (n, io.StringIO.StringIO(s), 'application/octet-stream')}
		location = "/local"
		try:
			r = requests.post(self.url + location, files=files, headers=self.header, timeout=5)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None
		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def listFiles(self, local=True, sd=False, recursive=False):
		location = ""
		if local and not sd:
			location = "/local"
		elif sd and not local:
			location = "/sdcard"

		if recursive:
			location += "?recursive=true"

		try:
			req = requests.get(self.url + location, headers=self.header, timeout=TIMEOUT)
		except:
			return None

		if req.status_code >= 400:
			return None

		finfo = req.json()
		if "files" not in finfo.keys():
			return []

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
					result[o].append((f["name"], f["refs"]["download"]))
				else:
					result[o].append((f["name"], None))

		return result

	def downloadFile(self, url):
		req = requests.get(url, headers=self.header, timeout=5)
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
		self.opClient = Client("http://%s" % self.ipAddr, self.apiKey)
		self.opSocket = None

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

		#pprint.pprint(mbody)

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

	def state(self, exclude=[]):
		url = "http://%s/api/printer" % self.ipAddr
		if len(exclude) > 0:
			url += "?exclude=%s" % ",".join(exclude)
		try:
			r = requests.get(url, data={}, headers=self.header, timeout=TIMEOUT)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None
		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def command(self, cmd):
		url = "http://%s/api/printer/command" % self.ipAddr
		payload = {"command": cmd}
		try:
			r = requests.post(url, json=payload, headers=self.header, timeout=TIMEOUT)
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT, None
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT, None

		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv
	
	def getConnectionInfo(self):
		url = "http://%s/api/connection" % self.ipAddr
		try:
			r = requests.get(url, data={}, headers=self.header, timeout=TIMEOUT)
		except requests.exceptions.ReadTimeout:
			return None, None
		except requests.exceptions.ConnectTimeout:
			return None, None

		try:
			rv = r.json()
		except:
			rv = None
		return r.status_code, rv

	def connect(self, port="/dev/ttyACM0", baudrate=115200):
		url = "http://%s/api/connection" % self.ipAddr
		payload = {"command": "connect",
				"port": port,
				"baudrate": baudrate,
				"save": True,
				"autoconnect": True
				}
		try:
			r = requests.post(url, json=payload, headers=self.header, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT
	
	def disconnect(self):
		url = "http://%s/api/connection" % self.ipAddr
		payload = {"command": "disconnect"}
		try:
			r = requests.post(url, json=payload, headers=self.header, timeout=TIMEOUT)
			return r.status_code
		except requests.exceptions.ReadTimeout:
			return RC_READ_TIMEOUT
		except requests.exceptions.ConnectTimeout:
			return RC_CONNECT_TIMEOUT
	

	def close(self):
		self.unsubscribe()
