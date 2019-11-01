"""
Created on May 11, 2018

@author: Jeff
"""
import wx
import os

BTNDIM = (48, 48) if os.name == 'posix' else (32, 32)


class Fan(wx.Window):
	def __init__(self, parent, server):
		self.parent = parent
		self.images = parent.images
		self.server = server
		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.NO_BORDER)
		self.SetBackgroundColour("white")

		szFan = wx.BoxSizer(wx.HORIZONTAL)
		szFan.AddSpacer(10)

		self.bPowerOff = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFanoff, size=BTNDIM, style=wx.NO_BORDER)
		self.bPowerOff.SetToolTip("Turn fan off")
		self.bPowerOff.SetBackgroundColour("white")
		self.Bind(wx.EVT_BUTTON, self.onBPowerOff, self.bPowerOff)
		szFan.Add(self.bPowerOff)
		szFan.AddSpacer(10 if os.name == 'posix' else 5)

		self.slSpeed = wx.Slider(self, id=wx.ID_ANY, value=0, minValue=0, maxValue=255, size=(250, -1),
								 style=wx.SL_HORIZONTAL + wx.SL_LABELS)
		szFan.Add(self.slSpeed)

		szFan.AddSpacer(10 if os.name == 'posix' else 5)
		self.bPower = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFan, size=BTNDIM, style=wx.NO_BORDER)
		self.bPower.SetToolTip("Set fan power")
		self.bPower.SetBackgroundColour("white")
		self.Bind(wx.EVT_BUTTON, self.onBPower, self.bPower)
		szFan.Add(self.bPower)

		szFan.AddSpacer(10)
		self.SetSizer(szFan)
		self.Layout()

	def enableControls(self, flag):
		self.bPowerOff.Enable(flag)
		self.bPower.Enable(flag)

	def onBPowerOff(self, _):
		self.slSpeed.SetValue(0)
		try:
			self.server.command("M106 S0")
		except:
			self.parent.askToSever("Unable to set fan power level")

	def onBPower(self, _):
		try:
			self.server.command("M106 S%d" % self.slSpeed.GetValue())
		except:
			self.parent.askToSever("Unable to set fan power level")
