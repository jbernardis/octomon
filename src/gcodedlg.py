"""
Created on May 4, 2018

@author: Jeff
"""
import wx
import os
from utils import formatElapsed

BTNDIM = (32, 32) if os.name == 'posix' else (16, 16)

from gcframe import GcFrame

class GCodeDlg(wx.Frame):
	def __init__(self, parent, server, gcode, filenm, pname, settings, images, cbexit):
		wx.Frame.__init__(self, None, wx.ID_ANY, self.formatTitle(pname, filenm))
		self.SetBackgroundColour("white")
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.server = server
		self.gcode = gcode
		self.filenm = filenm
		self.pname = pname
		self.settings = settings
		self.images = images
		self.exitDlg = cbexit
		self.nExtr = self.parent.nExtr
		self.layerCount = 0
		if self.gcode:
			self.sTotalTime = " / " + formatElapsed(self.gcode.getPrintTime())
			self.filament = self.gcode.getFilament()
		else:
			self.sTotalTime = ""
			self.filament = [[0.0, 0.0]]

		self.printPosition = 0
		self.followPrint = True

		self.lx = 0

		lbFont = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

		self.gcf = GcFrame(self, self.pname, self.gcode, self.settings)
		self.stHeight = wx.StaticText(self, wx.ID_ANY, "")
		self.stHeight.SetFont(lbFont)
		self.stTime = wx.StaticText(self, wx.ID_ANY, "")
		self.stTime.SetFont(lbFont)
		self.stFilament = wx.StaticText(self, wx.ID_ANY, "")
		self.stFilament.SetFont(lbFont)
		self.slLayer = wx.Slider(self, wx.ID_ANY, 1, 1, 10, style=wx.SL_VERTICAL+wx.SL_LABELS+wx.SL_INVERSE)
		self.Bind(wx.EVT_SLIDER, self.onSlLayer, self.slLayer)
		self.bUp =  wx.BitmapButton(self, wx.ID_ANY, self.images.pngUp, size=BTNDIM, style=wx.NO_BORDER)
		self.bUp.SetBackgroundColour("white")
		self.Bind(wx.EVT_BUTTON, self.onBUp, self.bUp)
		self.bDown =  wx.BitmapButton(self, wx.ID_ANY, self.images.pngDown, size=BTNDIM, style=wx.NO_BORDER)
		self.bDown.SetBackgroundColour("white")
		self.Bind(wx.EVT_BUTTON, self.onBDown, self.bDown)

		self.setSliderRange()

		self.cbSync = wx.CheckBox(self, wx.ID_ANY, "Sync with print")
		self.cbSync.SetValue(True)
		self.Bind(wx.EVT_CHECKBOX, self.onCbSync, self.cbSync)
		self.cbPrintedOnly = wx.CheckBox(self, wx.ID_ANY, "Only show printed")
		self.cbPrintedOnly.SetValue(self.settings.getSetting("showprintedonly", self.pname, "False"))
		self.Bind(wx.EVT_CHECKBOX, self.onCbShowPrintedOnly, self.cbPrintedOnly)
		self.cbShowPrev = wx.CheckBox(self, wx.ID_ANY, "Show previous layer")
		self.cbShowPrev.SetValue(self.settings.getSetting("showprevious", self.pname, "False"))
		self.Bind(wx.EVT_CHECKBOX, self.onCbShowPrev, self.cbShowPrev)
		self.cbShowMoves = wx.CheckBox(self, wx.ID_ANY, "Show moves")
		self.cbShowMoves.SetValue(self.settings.getSetting("showmoves", self.pname, "False"))
		self.Bind(wx.EVT_CHECKBOX, self.onCbShowMoves, self.cbShowMoves)
		self.cbShowRetr = wx.CheckBox(self, wx.ID_ANY, "Show retractions")
		self.cbShowRetr.SetValue(self.settings.getSetting("showretractions", self.pname, "False"))
		self.Bind(wx.EVT_CHECKBOX, self.onCbShowRetr, self.cbShowRetr)
		self.cbShowRevRetr = wx.CheckBox(self, wx.ID_ANY, "Show reverse retractions")
		self.cbShowRevRetr.SetValue(self.settings.getSetting("showrevretractions", self.pname, "False"))
		self.Bind(wx.EVT_CHECKBOX, self.onCbShowRevRetr, self.cbShowRevRetr)

		sznavgc = wx.BoxSizer(wx.VERTICAL)
		sznavgc.Add(self.bUp, 0, wx.LEFT, 12 if os.name == 'posix' else 25)
		sznavgc.Add(self.slLayer, 1, wx.GROW)
		sznavgc.Add(self.bDown, 0, wx.LEFT, 12 if os.name == 'posix' else 25)

		szgcf = wx.BoxSizer(wx.VERTICAL)
		szgcf.Add(self.gcf)
		szgcf.AddSpacer(5)
		szgcf.Add(self.stHeight, 0, wx.ALIGN_CENTER)
		szgcf.AddSpacer(5)
		szgcf.Add(self.stTime, 0, wx.ALIGN_CENTER)
		szgcf.AddSpacer(5)
		szgcf.Add(self.stFilament, 0, wx.ALIGN_CENTER)

		szgc = wx.BoxSizer(wx.HORIZONTAL)
		szgc.AddSpacer(15)
		szgc.Add(szgcf)
		if os.name == 'posix':
			szgc.AddSpacer(10)
		szgc.Add(sznavgc, 1, wx.GROW)
		szgc.AddSpacer(15)

		szopt1 = wx.BoxSizer(wx.VERTICAL)
		szopt1.Add(self.cbSync, 1, wx.EXPAND)
		szopt1.Add(self.cbPrintedOnly, 1, wx.EXPAND)

		szopt2 = wx.BoxSizer(wx.VERTICAL)
		szopt2.Add(self.cbShowPrev, 1, wx.EXPAND)
		szopt2.Add(self.cbShowMoves, 1, wx.EXPAND)

		szopt3 = wx.BoxSizer(wx.VERTICAL)
		szopt3.Add(self.cbShowRetr, 1, wx.EXPAND)
		szopt3.Add(self.cbShowRevRetr, 1, wx.EXPAND)

		szoptions = wx.BoxSizer(wx.HORIZONTAL)
		szoptions.AddSpacer(20)
		szoptions.Add(szopt1, 1, wx.EXPAND)
		szoptions.AddSpacer(5)
		szoptions.Add(szopt2, 1, wx.EXPAND)
		szoptions.AddSpacer(5)
		szoptions.Add(szopt3, 1, wx.EXPAND)
		szoptions.AddSpacer(10)

		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer(10)
		sz.Add(szgc)
		sz.AddSpacer(5)
		sz.Add(szoptions)
		sz.AddSpacer(10)

		self.showLayerInfo()

		self.SetSizer(sz)
		self.Fit()
		self.Layout()

	@staticmethod
	def formatTitle(pname, filenm):

		if filenm is None:
			return "%s - GCode Monitor - (no file loaded)" % pname
		else:
			return "%s - GCode monitor - %s" % (pname, filenm)

	def reloadGCode(self, gcode, filenm):
		self.filenm = filenm
		self.SetTitle(self.formatTitle(self.pname, filenm))
		self.gcode = gcode
		if self.gcode:
			self.sTotalTime = " / " + formatElapsed(self.gcode.getPrintTime())
			self.filament = self.gcode.getFilament()
		else:
			self.sTotalTime = ""
			self.filament = 0.0

		self.setSliderRange()

		# send new gcode to gcf
		self.printPosition = 0
		self.gcf.loadGCode(gcode)
		self.showLayerInfo()

	def setSliderRange(self):
		n = self.gcode.layerCount()
		self.slLayer.SetRange(1, 10 if n == 0 else n)
		self.slLayer.SetValue(1)
		self.slLayer.Enable(n != 0)
		self.bUp.Enable(n != 0)
		self.bDown.Enable(n != 0)
		self.layerCount = n

	def setPrintPosition(self, pos):
		if pos is None:
			return False, None, None
		self.printPosition = 0 if pos is None else pos
		self.gcf.setPrintPosition(self.printPosition)

		pLayer, lpct = self.gcode.findLayerByOffset(self.printPosition)
		cLayer = self.gcf.getCurrentLayerNum()

		if not self.followPrint:
			return cLayer != pLayer, pLayer, lpct
		
		if cLayer != pLayer:
			self.gcf.setLayer(pLayer)
			self.slLayer.SetValue(pLayer+1)
			self.showLayerInfo()
			return True, pLayer, lpct

		return False, pLayer, lpct

	def showLayerInfo(self):
		l = self.gcf.getCurrentLayer()
		if l is None:
			lblHt = ""
			lblTime = ""
			lblFilament = ""
		else:
			lx = self.gcf.getCurrentLayerNum()
			lblHt, lblTime, lblFilament = self.formatLayerInfo(l, lx)
			
		self.stHeight.SetLabel(lblHt)
		self.stTime.SetLabel(lblTime)
		self.stFilament.SetLabel(lblFilament)
		
	def formatLayerInfo(self, l, lx):
		sHt = "Height: {:.2f}  Layer: {:d} / {:d}".format(l.getHeight(), lx+1, self.layerCount)
		
		sTm = "  Print time: {:s}{:s}".format(formatElapsed(l.getLayerTime()), self.sTotalTime)
		o = l.getOffsets()
		if self.printPosition < o[0]:
			lyrs = self.gcode.getLayersBetweenOffsets(self.printPosition, o[0])
			untilTime = 0.0
			for ly in lyrs:
				untilTime += ly.getLayerTime()
			sTm += " ({:s} until)".format(formatElapsed(untilTime))

		sFi = "  Filament: "
		lf = l.getFilament()
		for i in range(self.nExtr):
			if i > 0:
				sFi += " / "
				
			if self.nExtr > 1:
				if i > 0:
					sFi += " - "
				sFi += "{:d}: ".format(i)
			sFi += "{:.2f}mm ({:.2f}cm3) / {:.2f}mm".format(lf[i][0], lf[i][1], self.filament[i][0])
			
		return sHt, sTm, sFi

	def onSlLayer(self, _):
		self.followPrintOff()
		v = self.slLayer.GetValue()-1
		self.gcf.setLayer(v)
		self.showLayerInfo()

	def onBUp(self, _):
		v = self.slLayer.GetValue()
		if v < self.gcode.layerCount():
			self.followPrintOff()
			v += 1
			self.slLayer.SetValue(v)
			self.gcf.setLayer(v-1)
			self.showLayerInfo()

	def onBDown(self, _):
		v = self.slLayer.GetValue()
		if v > 1:
			self.followPrintOff()
			v -= 1
			self.slLayer.SetValue(v)
			self.gcf.setLayer(v-1)
			self.showLayerInfo()

	def followPrintOff(self):
		if self.followPrint:
			self.cbSync.SetValue(False)
			self.followPrint = False
			self.gcf.setFollowPrint(False)

	def onCbSync(self, _):
		self.followPrint = self.cbSync.GetValue()
		self.gcf.setFollowPrint(self.followPrint)

	def onCbShowPrintedOnly(self, _):
		v = self.cbPrintedOnly.GetValue()
		self.settings.setSetting("showprintedonly", str(v), self.pname)
		self.gcf.setShowPrintedOnly(v)

	def onCbShowPrev(self, _):
		v = self.cbShowPrev.GetValue()
		self.settings.setSetting("showprevious", str(v), self.pname)
		self.gcf.setShowPrevious(v)

	def onCbShowMoves(self, _):
		v = self.cbShowMoves.GetValue()
		self.settings.setSetting("showmoves", str(v), self.pname)
		self.gcf.setShowMoves(v)

	def onCbShowRetr(self, _):
		v = self.cbShowRetr.GetValue()
		self.settings.setSetting("showretractions", str(v), self.pname)
		self.gcf.setShowRetractions(v)

	def onCbShowRevRetr(self, _):
		v = self.cbShowRevRetr.GetValue()
		self.settings.setSetting("showrevretractions", str(v), self.pname)
		self.gcf.setShowRevRetractions(v)

	def onClose(self, _):
		self.exitDlg()
