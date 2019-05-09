"""
Created on May 4, 2018

@author: Jeff
"""
import wx
from utils import formatElapsed

class TimesDlg(wx.Frame):
	def __init__(self, parent, pname, images, cbexit):
		wx.Frame.__init__(self, None, wx.ID_ANY, "Print Time Analysis for %s" % pname)
		self.SetBackgroundColour("white")
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.images = images
		self.exitDlg = cbexit

		self.clt = None
		self.prevLayers = None
		self.afterLayers = None
		self.layerx = 0

		font = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer(10)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)

		szReport = wx.BoxSizer(wx.VERTICAL)
		szReport.AddSpacer(20)

		box = wx.StaticBox(self, wx.ID_ANY, " Octoprint ")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Total estimated print time:", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalPTOct = t
		szRptLine.Add(self.totalPTOct)
		bsizer.Add(szRptLine)

		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Estimated remaining print time:", style=wx.ALIGN_RIGHT,
						  size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalRemainOct = t
		szRptLine.Add(self.totalRemainOct)
		bsizer.Add(szRptLine)

		bsizer.AddSpacer(5)
		szReport.Add(bsizer)

		szReport.AddSpacer(10)

		box = wx.StaticBox(self, wx.ID_ANY, " Calculated ")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Total print time:", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalPTCalc = t
		szRptLine.Add(self.totalPTCalc)
		bsizer.Add(szRptLine)

		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Current layer print time:", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalCurrentLayer = t
		szRptLine.Add(self.totalCurrentLayer)
		bsizer.Add(szRptLine)

		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Estimated print time to current position:", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalPrevLayers = t
		szRptLine.Add(self.totalPrevLayers)
		bsizer.Add(szRptLine)

		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Estimated print time remaining:", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalRemainCalc = t
		szRptLine.Add(self.totalRemainCalc)
		bsizer.Add(szRptLine)

		bsizer.AddSpacer(5)

		szReport.Add(bsizer)

		szReport.AddSpacer(10)

		box = wx.StaticBox(self, wx.ID_ANY, " Actuals ")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Current Position:", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.currentPosition = t
		szRptLine.Add(self.currentPosition)
		bsizer.Add(szRptLine)

		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Elapsed time:", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalElapsed = t
		szRptLine.Add(self.totalElapsed)
		bsizer.Add(szRptLine)

		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Difference from calculated:", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalDifference = t
		szRptLine.Add(self.totalDifference)
		bsizer.Add(szRptLine)

		bsizer.AddSpacer(5)

		szReport.Add(bsizer)

		szReport.AddSpacer(10)


		szbtn = wx.BoxSizer(wx.HORIZONTAL)	
		self.bExit= wx.BitmapButton(self, wx.ID_ANY, self.images.pngOk, size=(48,48))
		self.bExit.SetToolTip("Exit Dialog")
		self.Bind(wx.EVT_BUTTON, self.onClose, self.bExit)
		szbtn.Add(self.bExit)

		hsz.Add(szReport)
		hsz.AddSpacer(10)
		sz.Add(hsz)
		sz.AddSpacer(10)
		sz.Add(szbtn, 1, wx.ALIGN_CENTER, 0)
		sz.AddSpacer(10)

		self.SetSizer(sz)
		self.Fit()

	def updateTimesNewObject(self, totOct, totCalc):
		if totOct is None:
			self.totalPTOct.SetLabel("??")
		else:
			self.totalPTOct.SetLabel(formatElapsed(totOct))

		self.totalPTCalc.SetLabel(formatElapsed(totCalc))
		self.totalDifference.SetLabel("??")
		self.totalCurrentLayer.SetLabel("??")
		self.totalRemainOct.SetLabel("??")
		self.totalRemainCalc.SetLabel("??")
		self.currentPosition.SetLabel("")
		self.layerx = 0

	def updateTimesNewLayer(self, layerx, elapsed, prevLayers, currentLayer, afterLayers, timeLeftOct):
		self.layerx = layerx
		if elapsed is None:
			self.totalElapsed.SetLabel("??")
		else:
			self.totalElapsed.SetLabel(formatElapsed(elapsed))
			
		self.totalPrevLayers.SetLabel(formatElapsed(prevLayers))

		if currentLayer is None:
			self.totalCurrentLayer.SetLabel("NA")
			self.clt = None
		else:
			self.totalCurrentLayer.SetLabel(formatElapsed(currentLayer))
			self.clt = currentLayer

		if timeLeftOct is None:		
			self.totalRemainOct.SetLabel("??")
		else:
			self.totalRemainOct.SetLabel(formatElapsed(timeLeftOct))
		
		self.totalRemainCalc.SetLabel(formatElapsed(afterLayers))
		self.afterLayers = afterLayers

		self.totalPrevLayers.SetLabel(formatElapsed(prevLayers))
		self.prevLayers = prevLayers

		self.currentPosition.SetLabel(self.positionString(0))

	def updateTimesMidLayer(self, elapsed, lpct, timeLeftOct):
		if elapsed is None:
			self.totalElapsed.SetLabel("??")
		else:
			self.totalElapsed.SetLabel(formatElapsed(elapsed))

		if timeLeftOct is None:
			self.totalRemainOct.SetLabel("??")
		else:
			self.totalRemainOct.SetLabel(formatElapsed(timeLeftOct))

		if lpct is None or self.clt is None:
			self.totalPrevLayers.SetLabel("??")
			self.totalRemainCalc.SetLabel("??")
			self.totalDifference.SetLabel("??")
			self.currentPosition.SetLabel("")
		else:
			self.currentPosition.SetLabel(self.positionString(lpct))
			calcElapsed = self.prevLayers + lpct*self.clt
			self.totalPrevLayers.SetLabel(formatElapsed(calcElapsed))
			self.totalRemainCalc.SetLabel(formatElapsed(self.afterLayers + (1-lpct)*self.clt))
			if elapsed is None:
				self.totalDifference.SetLabel("??")
			else:
				diff = elapsed - calcElapsed
				if diff < 0:
					text = " (ahead)"
				elif diff > 0:
					text = " (behind)"
				else:
					text = ""
				self.totalDifference.SetLabel(formatElapsed(elapsed-calcElapsed) + text)

	def positionString(self, lpct):
		return "Layer: %.2f" % (float(self.layerx+1) + float(lpct))

	def onClose(self, _):
		self.exitDlg()
