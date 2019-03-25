"""
Created on May 4, 2018

@author: Jeff
"""
import wx
from utils import formatElapsed

class TimesDlg(wx.Frame):
	def __init__(self, parent, pname, images, cbexit, cbrefresh):
		wx.Frame.__init__(self, None, wx.ID_ANY, "Print Time Analysis for %s" % pname)
		self.SetBackgroundColour("white")
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.images = images
		self.exitDlg = cbexit
		self.refreshDlg = cbrefresh
		
		font = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer(10)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)

		szReport = wx.BoxSizer(wx.VERTICAL)
		szReport.AddSpacer(20)
		
		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Total Estimated Print Time (Octoprint):", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalPTOct = t
		szRptLine.Add(self.totalPTOct)
		szReport.Add(szRptLine)
		
		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "(Calculated):", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalPTCalc = t
		szRptLine.Add(self.totalPTCalc)
		szReport.Add(szRptLine)
		
		szReport.AddSpacer(10)
		
		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Actual Elapsed Time:", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalElapsed = t
		szRptLine.Add(self.totalElapsed)
		szReport.Add(szRptLine)
		
		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Estimated time to start of current layer:", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalPrevLayers = t
		szRptLine.Add(self.totalPrevLayers)
		szReport.Add(szRptLine)
		
		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Difference:", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalDifference = t
		szRptLine.Add(self.totalDifference)
		szReport.Add(szRptLine)
		
		szReport.AddSpacer(10)
		
		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Current Layer Estimate:", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalCurrentLayer = t
		szRptLine.Add(self.totalCurrentLayer)
		szReport.Add(szRptLine)
		
		szReport.AddSpacer(10)
		
		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "Estimated remaining print time (Octoprint):", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalRemainOct = t
		szRptLine.Add(self.totalRemainOct)
		szReport.Add(szRptLine)
		
		szRptLine = wx.BoxSizer(wx.HORIZONTAL)
		t = wx.StaticText(self, wx.ID_ANY, "(Calculated):", style=wx.ALIGN_RIGHT, size=(300, -1))
		t.SetFont(font)
		szRptLine.Add(t)
		szRptLine.AddSpacer(5)
		t = wx.StaticText(self, wx.ID_ANY, "", size=(100, -1))
		t.SetFont(font)
		self.totalRemainCalc = t
		szRptLine.Add(self.totalRemainCalc)
		szReport.Add(szRptLine)
		
		szReport.AddSpacer(20)	
		
		szbtn = wx.BoxSizer(wx.HORIZONTAL)	
		self.bExit= wx.BitmapButton(self, wx.ID_ANY, self.images.pngOk, size=(48,48))
		self.bExit.SetToolTip("Exit Dialog")
		self.Bind(wx.EVT_BUTTON, self.onClose, self.bExit)
		szbtn.Add(self.bExit)
		
		szbtn.AddSpacer(30)
		
		self.bRefresh= wx.BitmapButton(self, wx.ID_ANY, self.images.pngRefresh, size=(48,48))
		self.bRefresh.SetToolTip("Refresh Dialog")
		self.Bind(wx.EVT_BUTTON, self.onRefresh, self.bRefresh)
		szbtn.Add(self.bRefresh)
		
		szReport.Add(szbtn, 0, wx.ALIGN_CENTER)
		
		hsz.Add(szReport)
		sz.Add(hsz)
		sz.AddSpacer(10)

		self.SetSizer(sz)
		self.Fit()

	def updateTimes(self, totCalc, totOct, elapsed, prevLayers, currentLayer, timeLeftCalc, timeLeftOct):
		if totOct is None:
			self.totalPTOct.SetLabel("??")
		else:
			self.totalPTOct.SetLabel(formatElapsed(totOct))
			
		self.totalPTCalc.SetLabel(formatElapsed(totCalc))	
		
		if elapsed is None:	
			self.totalElapsed.SetLabel("??")
		else:
			self.totalElapsed.SetLabel(formatElapsed(elapsed))
			
		self.totalPrevLayers.SetLabel(formatElapsed(prevLayers))
		
		if elapsed is None:
			self.totalDifference.SetLabel("??")
		else:
			self.totalDifference.SetLabel(formatElapsed(elapsed-prevLayers))
			
		if currentLayer is None:
			self.totalCurrentLayer.SetLabel("NA")
		else:
			self.totalCurrentLayer.SetLabel(formatElapsed(currentLayer))

		if timeLeftOct is None:		
			self.totalRemainOct.SetLabel("??")
		else:
			self.totalRemainOct.SetLabel(formatElapsed(timeLeftOct))
		
		self.totalRemainCalc.SetLabel(formatElapsed(timeLeftCalc))
	
	def onRefresh(self, evt):
		self.refreshDlg()
	
	def onClose(self, evt):
		self.exitDlg()
