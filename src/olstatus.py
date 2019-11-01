"""
Created on May 11, 2018

@author: Jeff
"""
import wx
import os

BMPDIM = (48, 48)

olEnabled = "OctoLapse is enabled"
olNotEnabled = "Octolapse is NOT enabled"
olActive = "OctoLapse is active:"
olNotActive = "OctoLapse is NOT active"
olSnapshot = "OctoLapse is taking a snapshot"
olNotSnapshot = "OctoLapse is Not taking a snapshot"
olRender = "OctoLapse is rendering"
olNotRender = "OctoLapse is NOT rendering"

class OLStatus(wx.Window):
	def __init__(self, parent, images):
		self.parent = parent
		self.images = images
		wx.Window.__init__(self, parent, wx.ID_ANY, size=(BMPDIM[0]*4, BMPDIM[1]), style=wx.NO_BORDER)
		self.SetBackgroundColour("white")

		sz = wx.BoxSizer(wx.HORIZONTAL)

		self.bEnabled = wx.StaticBitmap(self, wx.ID_ANY, self.images.pngEnabled_red, size=BMPDIM)
		self.bEnabled.SetToolTip(olNotEnabled)
		sz.Add(self.bEnabled)
		self.enabled = False

		self.bActive = wx.StaticBitmap(self, wx.ID_ANY, self.images.pngActive_off, size=BMPDIM)
		self.bActive.SetToolTip(olNotEnabled)
		sz.Add(self.bActive)
		self.active = False

		self.bSnapshot = wx.StaticBitmap(self, wx.ID_ANY, self.images.pngSnapshot_off, size=BMPDIM)
		self.bSnapshot.SetToolTip(olNotEnabled)
		sz.Add(self.bSnapshot)
		self.snapshot = False

		self.bRender = wx.StaticBitmap(self, wx.ID_ANY, self.images.pngRender_off, size=BMPDIM)
		self.bRender.SetToolTip(olNotEnabled)
		sz.Add(self.bRender)
		self.render = False

		self.SetSizer(sz)
		self.Layout()

	def updateDisplay(self):
		if self.enabled:
			self.bEnabled.SetToolTip(olEnabled)
			self.bEnabled.SetBitmap(self.images.pngEnabled_green)
			if self.active:
				self.bActive.SetToolTip(olActive)
				self.bActive.SetBitmap(self.images.pngActive_green)
				if self.snapshot:
					self.bSnapshot.SetToolTip(olSnapshot)
					self.bSnapshot.SetBitmap(self.images.pngSnapshot_green)
				else:
					self.bSnapshot.SetToolTip(olNotSnapshot)
					self.bSnapshot.SetBitmap(self.images.pngSnapshot_yellow)

				if self.render:
					self.bRender.SetToolTip(olRender)
					self.bRender.SetBitmap(self.images.pngRender_green)
				else:
					self.bRender.SetToolTip(olNotRender)
					self.bRender.SetBitmap(self.images.pngRender_yellow)

			else:
				self.bActive.SetToolTip(olNotActive)
				self.bActive.SetBitmap(self.images.pngActive_red)
				self.bSnapshot.SetToolTip(olNotActive)
				self.bSnapshot.SetBitmap(self.images.pngSnapshot_off)
				self.bRender.SetToolTip(olNotActive)
				self.bRender.SetBitmap(self.images.pngRender_off)


		else:
			self.bEnabled.SetToolTip(olNotEnabled)
			self.bEnabled.SetBitmap(self.images.pngEnabled_red)
			self.bActive.SetToolTip(olNotEnabled)
			self.bActive.SetBitmap(self.images.pngActive_off)
			self.bSnapshot.SetToolTip(olNotEnabled)
			self.bSnapshot.SetBitmap(self.images.pngSnapshot_off)
			self.bRender.SetToolTip(olNotEnabled)
			self.bRender.SetBitmap(self.images.pngRender_off)

	def setEnabled(self, flag=True):
		if self.enabled == flag:
			return

		self.enabled = flag
		self.updateDisplay()

	def setActive(self, flag=True):
		if self.active == flag:
			return

		self.active = flag
		self.updateDisplay()

	def setSnapshot(self, flag=True):
		if self.snapshot == flag:
			return

		self.snapshot = flag
		self.updateDisplay()

	def setRender(self, flag=True):
		if self.render == flag:
			return

		self.render = flag
		self.updateDisplay()
