#!/bin/env python

# TODO
#
#  need to figure out what error I'm seeing if I turn the printer off while still connected - it's causing a hang
#
#  web cam
#
#  file upload - allow directory creation/traversal
#  allow upload to sd - also allow delete and select - also, the printer status report tells us if the sd is ready -
#  should use that to enable/disable - update marlin on cuboid
#
#  clear file selection
#
#  Need to make sure when downloading the selected file for gcode monitor that subdirectories are represented in the
#  job update.   Right now, I see origin and name, not path
#
#  question - if I select a new file while paused, does the printer state move to operational, or does it stay paused?
#  This is a potential issue because I need to know when to enable print versus restart.
#
#  figure out how to deal with printer connection - connect/disconnect 
#
# mplayer command line thus far - image still a little fuzzy:
# ./mplayer -vf 'flip,mirror,dsize=800:600:0,scale=600:800' 'http://192.168.1.110/webcam/?action=stream'


import os
import inspect

from printerinstances import PrinterInstances
from printerdlg import PrinterDlg
from images import Images
from settings import Settings
from toolbox import ToolBox
import wx.lib

BTNDIM = (48, 48)

cmdFolder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))

(RegisterEvent, EVT_REGISTER) = wx.lib.newevent.NewEvent()  # @UndefinedVariable

class MyFrame(wx.Frame):
	def __init__(self):
		self.destroyed = False
		self.t = 0
		self.seq = 1

		self.images = Images(os.path.join(cmdFolder, "images"))
		self.toolicons = Images(os.path.join(cmdFolder, "images", "tools"))

		self.printerList = []
		self.settings = Settings(cmdFolder)

		wx.Frame.__init__(self, None, -1, "Octoprint Monitor", size=(300, 300))
		self.Bind(wx.EVT_CLOSE, self.onClose)

		ico = wx.Icon(os.path.join(cmdFolder, "images", "octomon.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcon(ico)

		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer(20)
		
		box = wx.StaticBox(self, -1, "Printers")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

		self.buttons = {}
		self.dialogs = {}

		self.plist = self.settings.getSetting("printers")
		for pn in self.plist:
			b = wx.Button(self, wx.ID_ANY, pn)
			self.Bind(wx.EVT_BUTTON, self.pressPrinter, b)
			bsizer.Add(b, 0, wx.ALL, 5)
			self.buttons[pn] = b

		sz.Add(bsizer)
		sz.AddSpacer(10)
		
		self.tbx = ToolBox(cmdFolder)
		tools = self.tbx.getTools()
		
		for s in tools.keys():
			box = wx.StaticBox(self, wx.ID_ANY, s)
			bxsz = wx.StaticBoxSizer(box, wx.HORIZONTAL)
			try:
				ordr = tools[s]["order"]
			except KeyError:
				ordr = list(tools[s].keys())
			for t in ordr:
				i = tools[s][t]["icon"]
				png = self.toolicons.getByName(i)
					
				b = wx.BitmapButton(self, wx.ID_ANY, png, size=BTNDIM)
				bxsz.Add(b, 0, wx.ALL, 5)
				b.SetToolTip(tools[s][t]["helptext"])
				l = lambda evt, section=s, tool=t: self.onToolButton(evt, section, tool)
				self.Bind(wx.EVT_BUTTON, l, b)
				
			sz.Add(bxsz)
			sz.AddSpacer(10)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(20)
		hsz.Add(sz)
		hsz.AddSpacer(20)

		hsz.Fit(self)
		self.SetSizer(hsz)
		self.Layout()
		self.Fit()

		self.enableButtons()
		self.printerInstances = PrinterInstances(self.plist, self.settings, self.registerPrinter)

		self.Bind(EVT_REGISTER, self.printerRegistration)


		self.Show()
		
	def onToolButton(self, _, section, tool):
		self.tbx.execute(section, tool)

	def enableButtons(self):
		for pn in self.plist:
			self.buttons[pn].Enable(pn in self.printerList and pn not in self.dialogs.keys())

	def pressPrinter(self, evt):
		pName = evt.GetEventObject().GetLabel()
		if pName in self.dialogs.keys():
			return

		try:
			svr = self.printerInstances.getPrinterServer(pName)
		except:
			dlg = wx.MessageDialog(self, "Unable to obtain printer server for %s" % pName,
								   "Printer Initialization Error", wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()
			return

		try:
			rc, json = svr.state(exclude=["temperature", "sd"])
		except:
			dlg = wx.MessageDialog(self, "Unable to obtain initial printer state from %s" % pName,
								   "Printer Initialization Error", wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()
			return

		d = PrinterDlg(self, svr, pName, self.settings, self.images)
		self.dialogs[pName] = d
		self.enableButtons()

		d.Show()

	def registerPrinter(self, action, pName):
		if self.destroyed:
			print(" printer registration after window has been destroyed - terminating thread")
			exit(0)
		evt = RegisterEvent(action=action, pname=pName)
		wx.PostEvent(self, evt)

	def printerRegistration(self, evt):
		action = evt.action
		pName = evt.pname

		if action == "add":
			if pName in self.printerList:
				pass
			else:
				self.printerList.append(pName)

		elif action == "remove":
			if pName not in self.printerList:
				pass
			else:
				self.printerList.remove(pName)
				if pName in self.dialogs.keys():
					self.dialogs[pName].sever()
					self.dialogs[pName].Destroy()
					del self.dialogs[pName]

		self.enableButtons()

	def onClose(self, _):
		if self.destroyed:
			return
		
		self.destroyed = True
		for p in self.dialogs.keys():
			self.dialogs[p].sever()
			self.dialogs[p].Destroy()

		self.printerInstances.close()
		self.Destroy()

	def connectionSevered(self, pName):
		if pName in self.dialogs.keys():
			self.dialogs[pName].sever()
			self.dialogs[pName].Destroy()
			del self.dialogs[pName]
			self.enableButtons()


if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			self.frame = MyFrame()
			self.frame.Show()
			self.SetTopWindow(self.frame)
			return True


	app = App(False)
	app.MainLoop()
