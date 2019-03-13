"""
Created on May 4, 2018

@author: Jeff
"""
import os
import wx.lib
import subprocess

import pprint

from imagemap import ImageMap
from heater import Heater
from tools import formatElapsed, approximateValue
from fan import Fan
from filedlg import FileDlg
from uploaddest import UploadDestinationDlg
from tempgraph import TempGraph
from gcode import GCode
from gcodedlg import GCodeDlg
from termdlg import TerminalDlg
from firmwaremarlin import FirmwareDlg
from fwsettings import FwSettings, FWC
from settings import XCOUNT
from connectdlg import ConnectDlg
from printerserver import RC_READ_TIMEOUT, RC_CONNECT_TIMEOUT
from octolapsedlg import OctolapseDlg

(FirmwareEvent, EVT_FIRMWARE) = wx.lib.newevent.NewEvent()  # @UndefinedVariable
(TerminalEvent, EVT_TERMMSG) = wx.lib.newevent.NewEvent()   # @UndefinedVariable
(LogEvent, EVT_LOGMSG) = wx.lib.newevent.NewEvent()		 # @UndefinedVariable
(ErrorEvent, EVT_ERRMSG) = wx.lib.newevent.NewEvent()	   # @UndefinedVariable
(GCodeEvent, EVT_GCODE) = wx.lib.newevent.NewEvent()	   # @UndefinedVariable

labelWidth = 180 if os.name == 'posix' else 120
fieldWidth = 200
spacerWidth = 5
stStyle = wx.ST_NO_AUTORESIZE + wx.ALIGN_RIGHT

BTNDIM = (48, 48) if os.name == 'posix' else (32, 32)
MENU_FILE_LIST = 101
MENU_FILE_UPLOAD = 102
MENU_FILE_UPDATE = 103
MENU_VIEW_TEMPERATURES = 201
MENU_VIEW_GCODE = 202
MENU_VIEW_TERMINAL = 203
MENU_VIEW_FIRMWARE = 204
MENU_VIEW_WEBCAM = 205
MENU_CONNECT = 301
MENU_DISCONNECT = 302
MENU_OCTOLAPSE = 401

MAX_READ_TIMEOUTS = 15

imageMapXY = [[10, 10, 50, 50, "HX"], [201, 192, 239, 230, "HY"], [201, 10, 239, 50, "HZ"], [10, 192, 50, 230, "HA"],
			  [216, 86, 235, 156, "X+4"], [193, 86, 212, 156, "X+3"], [168, 86, 190, 156, "X+2"],
			  [143, 104, 164, 136, "X+1"],
			  [83, 104, 105, 136, "X-1"], [58, 86, 79, 156, "X-2"], [33, 86, 56, 156, "X-3"], [11, 86, 29, 156, "X-4"],
			  [98, 214, 152, 231, "Y-4"], [98, 188, 152, 209, "Y-3"], [98, 163, 152, 185, "Y-2"],
			  [110, 139, 140, 161, "Y-1"],
			  [110, 79, 140, 101, "Y+1"], [98, 53, 152, 78, "Y+2"], [98, 28, 152, 52, "Y+3"], [98, 7, 152, 27, "Y+4"]]

imageMapZ = [[11, 39, 47, 62, "Z+3"], [11, 67, 47, 88, "Z+2"], [11, 91, 47, 109, "Z+1"],
			 [11, 126, 47, 145, "Z-1"], [11, 148, 47, 170, "Z-2"], [11, 172, 47, 197, "Z-3"]]

imageMapE = [[11, 10, 46, 46, "Retr"], [11, 93, 46, 129, "Extr"]]


class PrinterDlg(wx.Frame):
	def __init__(self, parent, server, pname, settings, images):
		self.ipAddr = server.getIpAddr()
		wx.Frame.__init__(self, None, wx.ID_ANY, "%s - %s" % (pname, self.ipAddr))
		self.SetBackgroundColour("white")

		self.parent = parent
		self.server = server
		self.pname = pname
		self.settings = settings
		self.images = images
		self.pWebcam = None

		self.hasZProbe = self.settings.getSetting("haszprobe", pname, False)
		self.flash = FwSettings(self.hasZProbe)
		self.collectingFw = False

		self.fileDlg = None
		self.tempGraph = None
		self.gcdlg = None
		self.termdlg = None
		self.fwdlg = None
		self.fwc = None
		self.msgTimer = 0
		
		self.toRead = 0

		self.xySpeed = self.settings.getSetting("xySpeed", pname, 300)
		self.zSpeed = self.settings.getSetting("zSpeed", pname, 300)
		self.eLength = self.settings.getSetting("eLength", pname, 5)
		self.nExtr = self.settings.getSetting("nExtr", pname, 1)
		self.bedPresets = self.settings.getSetting("bedPresets", pname,
							[["off", 0], ["PLA (60)", 60], ["ABS (110)", 110]])
		self.toolPresets = self.settings.getSetting("toolPresets", pname,
							[["off", 0], ["PLA (205)", 205], ["ABS (225)", 225]])
		self.acceleration = self.settings.getSetting("acceleration", pname, 1500)
		self.filamentDiameter = self.settings.getSetting("filamentDiameter", pname, 1.75)

		self.printerState = "unknown"
		self.lastReportedPrinterState = "unknown"

		self.printFileName = None
		self.lastReportedFileName = None
		self.selectedFileOrigin = None
		self.selectedFilePath = None

		self.movementEnabled = True
		self.temperatureEnabled = True

		self.filamentData = {}
		self.reportedFilamentData = {}
		self.tools = ["tool%d" % i for i in range(self.nExtr)]
		self.currentTemps = {'bed': {'actual': 0, 'target': 0}}
		for t in self.tools:
			self.filamentData[t] = None
			self.reportedFilamentData[t] = None
			self.currentTemps[t] = {'actual': 0, 'target': 0}
		self.tempHistory = [self.currentTemps.copy()]

		self.currentTool = 0

		self.estimatedPrintTime = 0
		self.lastReportedEstPrintTime = 0

		self.completion = None
		self.lastReportedCompletion = None

		self.printTime = None
		self.lastReportedPrintTime = None

		self.printTimeLeft = None
		self.lastReportedPrintTimeLeft = None
		self.printTimeLeftOrigin = None
		self.lastReportedPrintTimeLeftOrigin = None

		self.fileSize = None
		self.filePos = 0
		self.lastReportedFilePos = 0

		self.layerInfo = None
		self.lastReportedLayerInfo = None

		self.heightInfo = None
		self.lastReportedHeightInfo = None

		self.doPreheat = True

		self.Bind(wx.EVT_CLOSE, self.onClose)

		lbFont = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		lFont = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

		self.CreateStatusBar()
		self.SetStatusText("")

		menuBar = wx.MenuBar()

		menu1 = wx.Menu()
		menu1.Append(MENU_FILE_LIST, "&List", "list available files on printer")
		menu1.Append(MENU_FILE_UPLOAD, "&Upload", "upload a GCode file to printer")
		menu1.Append(MENU_FILE_UPDATE, "&Check for Updates", "check for octoprint/plugin updates")
		menuBar.Append(menu1, "&File")

		menu2 = wx.Menu()
		menu2.Append(MENU_VIEW_TEMPERATURES, "&Temperatures", "Graphcal display of temperatures")
		menu2.Append(MENU_VIEW_GCODE, "&G Code", "Visually track G Code as it prints")
		menu2.Append(MENU_VIEW_TERMINAL, "Ter&minal", "View commands set to the printer and their responses")
		menu2.Append(MENU_VIEW_WEBCAM, "&Webcam", "Open a webcam viewing window")
		menu2.Append(MENU_VIEW_FIRMWARE, "&Firmware", "View printer firmware settings")
		menuBar.Append(menu2, "&View")
		
		menu3 = wx.Menu()
		menu3.Append(MENU_CONNECT, "&Connect", "Force a printer connection")
		menu3.Append(MENU_DISCONNECT, "&Disconnect", "Force a printer disconnection")
		menuBar.Append(menu3, "&Connection")
		
		menu4 = wx.Menu()
		menu4.Append(MENU_OCTOLAPSE, "&Configure", "Configure Octolapse")
		menuBar.Append(menu4, "&Octolapse")

		self.SetMenuBar(menuBar)
		self.Bind(wx.EVT_MENU, self.MenuFileList, id=MENU_FILE_LIST)
		self.Bind(wx.EVT_MENU, self.MenuFileUpload, id=MENU_FILE_UPLOAD)
		self.Bind(wx.EVT_MENU, self.MenuFileUpdate, id=MENU_FILE_UPDATE)
		self.Bind(wx.EVT_MENU, self.MenuViewTemps, id=MENU_VIEW_TEMPERATURES)
		self.Bind(wx.EVT_MENU, self.MenuViewGCode, id=MENU_VIEW_GCODE)
		self.Bind(wx.EVT_MENU, self.MenuViewTerminal, id=MENU_VIEW_TERMINAL)
		self.Bind(wx.EVT_MENU, self.MenuViewFirmware, id=MENU_VIEW_FIRMWARE)
		self.Bind(wx.EVT_MENU, self.MenuViewWebcam, id=MENU_VIEW_WEBCAM)
		self.Bind(wx.EVT_MENU, self.MenuConnect, id=MENU_CONNECT)
		self.Bind(wx.EVT_MENU, self.MenuDisconnect, id=MENU_DISCONNECT)
		self.Bind(wx.EVT_MENU, self.MenuOctolapse, id=MENU_OCTOLAPSE)

		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer(10)

		szh = wx.BoxSizer(wx.HORIZONTAL)

		box = wx.StaticBox(self, wx.ID_ANY, " Status ")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)
		t = wx.StaticText(self, wx.ID_ANY, "Status: ", size=(labelWidth, -1), style=stStyle)
		t.SetFont(lbFont)
		hsz.Add(t)
		hsz.AddSpacer(spacerWidth)
		self.stPrinterStatus = wx.StaticText(self, wx.ID_ANY, "%s" % self.printerState, size=(fieldWidth, -1))
		self.stPrinterStatus.SetFont(lFont)
		hsz.Add(self.stPrinterStatus)
		bsizer.Add(hsz)

		bsizer.AddSpacer(5)
		bsizer.Add(wx.StaticLine(self, wx.ID_ANY, style=wx.LI_HORIZONTAL, size=(50, -1)), 1, wx.EXPAND, 1)
		bsizer.AddSpacer(5)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)
		t = wx.StaticText(self, wx.ID_ANY, "File: ", size=(labelWidth, -1), style=stStyle)
		t.SetFont(lbFont)
		hsz.Add(t)
		hsz.AddSpacer(spacerWidth)
		self.stPrinterFile = wx.StaticText(self, wx.ID_ANY, "-", size=(fieldWidth, -1))
		self.stPrinterFile.SetFont(lFont)
		hsz.Add(self.stPrinterFile)
		bsizer.Add(hsz)

		self.stPrinterFilament = {}
		for tool in self.tools:
			hsz = wx.BoxSizer(wx.HORIZONTAL)
			hsz.AddSpacer(10)
			if tool == "tool0":
				t = wx.StaticText(self, wx.ID_ANY, "Filament (Tool0): ", size=(labelWidth, -1), style=stStyle)
			else:
				t = wx.StaticText(self, wx.ID_ANY, "(%s): " % tool.capitalize(), size=(labelWidth, -1), style=stStyle)
			t.SetFont(lbFont)
			hsz.Add(t)
			hsz.AddSpacer(spacerWidth)
			self.stPrinterFilament[tool] = wx.StaticText(self, wx.ID_ANY, "- / -", size=(fieldWidth, -1))
			self.stPrinterFilament[tool].SetFont(lFont)
			hsz.Add(self.stPrinterFilament[tool])
			bsizer.Add(hsz)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)
		t = wx.StaticText(self, wx.ID_ANY, "Est Print Time: ", size=(labelWidth, -1), style=stStyle)
		t.SetFont(lbFont)
		hsz.Add(t)
		hsz.AddSpacer(spacerWidth)
		self.stPrinterEstPrintTime = wx.StaticText(self, wx.ID_ANY, "-", size=(fieldWidth, -1))
		self.stPrinterEstPrintTime.SetFont(lFont)
		hsz.Add(self.stPrinterEstPrintTime)
		bsizer.Add(hsz)

		bsizer.AddSpacer(5)
		bsizer.Add(wx.StaticLine(self, wx.ID_ANY, style=wx.LI_HORIZONTAL, size=(50, -1)), 1, wx.EXPAND, 1)
		bsizer.AddSpacer(5)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)
		t = wx.StaticText(self, wx.ID_ANY, "Printed: ", size=(labelWidth, -1), style=stStyle)
		t.SetFont(lbFont)
		hsz.Add(t)
		hsz.AddSpacer(spacerWidth)
		self.stPrinted = wx.StaticText(self, wx.ID_ANY, "- / -", size=(fieldWidth, -1))
		self.stPrinted.SetFont(lFont)
		hsz.Add(self.stPrinted)
		bsizer.Add(hsz)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)
		t = wx.StaticText(self, wx.ID_ANY, "Completion: ", size=(labelWidth, -1), style=stStyle)
		t.SetFont(lbFont)
		hsz.Add(t)
		hsz.AddSpacer(spacerWidth)
		self.stCompletion = wx.StaticText(self, wx.ID_ANY, "-", size=(fieldWidth, -1))
		self.stCompletion.SetFont(lFont)
		hsz.Add(self.stCompletion)
		bsizer.Add(hsz)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)
		t = wx.StaticText(self, wx.ID_ANY, "Print Time: ", size=(labelWidth, -1), style=stStyle)
		t.SetFont(lbFont)
		hsz.Add(t)
		hsz.AddSpacer(spacerWidth)
		self.stPrintTime = wx.StaticText(self, wx.ID_ANY, "-", size=(fieldWidth, -1))
		self.stPrintTime.SetFont(lFont)
		hsz.Add(self.stPrintTime)
		bsizer.Add(hsz)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)
		t = wx.StaticText(self, wx.ID_ANY, "Print Time Left: ", size=(labelWidth, -1), style=stStyle)
		t.SetFont(lbFont)
		hsz.Add(t)
		hsz.AddSpacer(spacerWidth)
		self.stPrintTimeLeft = wx.StaticText(self, wx.ID_ANY, "-", size=(fieldWidth, -1))
		self.stPrintTimeLeft.SetFont(lFont)
		hsz.Add(self.stPrintTimeLeft)
		bsizer.Add(hsz)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)
		t = wx.StaticText(self, wx.ID_ANY, "Height: ", size=(labelWidth, -1), style=stStyle)
		t.SetFont(lbFont)
		hsz.Add(t)
		hsz.AddSpacer(spacerWidth)
		self.stHeight = wx.StaticText(self, wx.ID_ANY, "- / -", size=(fieldWidth, -1))
		self.stHeight.SetFont(lFont)
		hsz.Add(self.stHeight)
		bsizer.Add(hsz)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)
		t = wx.StaticText(self, wx.ID_ANY, "Layer: ", size=(labelWidth, -1), style=stStyle)
		t.SetFont(lbFont)
		hsz.Add(t)
		hsz.AddSpacer(spacerWidth)
		self.stLayer = wx.StaticText(self, wx.ID_ANY, "- / -", size=(fieldWidth, -1))
		self.stLayer.SetFont(lFont)
		hsz.Add(self.stLayer)
		bsizer.Add(hsz)
		bsizer.AddSpacer(10)

		statsz = wx.BoxSizer(wx.VERTICAL)
		statsz.Add(bsizer)
		statsz.AddSpacer(5)

		box = wx.StaticBox(self, wx.ID_ANY, " Job Control ")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bsizer.AddSpacer(5)

		bhsizer = wx.BoxSizer(wx.HORIZONTAL)

		bhsizer.AddSpacer(10)

		self.bPrint = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPrint, size=BTNDIM, style=wx.NO_BORDER)
		self.bPrint.SetToolTip("Start/Restart printing selected file")
		self.Bind(wx.EVT_BUTTON, self.onBPrint, self.bPrint)
		bhsizer.Add(self.bPrint)

		bhsizer.AddSpacer(30)

		self.bPause = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPause, size=BTNDIM, style=wx.NO_BORDER)
		self.bPause.SetToolTip("Pause/Resume printing")
		self.Bind(wx.EVT_BUTTON, self.onBPause, self.bPause)
		bhsizer.Add(self.bPause)

		bhsizer.AddSpacer(30)

		self.bCancel = wx.BitmapButton(self, wx.ID_ANY, self.images.pngCancel, size=BTNDIM, style=wx.NO_BORDER)
		self.bCancel.SetToolTip("Cancel printing")
		self.Bind(wx.EVT_BUTTON, self.onBCancel, self.bCancel)
		bhsizer.Add(self.bCancel)

		bhsizer.AddSpacer(30)

		self.bPreheat = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPreheat, size=BTNDIM, style=wx.NO_BORDER)
		self.bPreheat.SetToolTip("Preheat based on loaded G Code")
		self.Bind(wx.EVT_BUTTON, self.onBPreheat, self.bPreheat)
		bhsizer.Add(self.bPreheat)

		bhsizer.AddSpacer(10)

		bsizer.Add(bhsizer, 1, wx.ALIGN_CENTER)

		bsizer.AddSpacer(5)
		statsz.Add(bsizer, 1, wx.EXPAND)
		statsz.AddSpacer(5)

		box = wx.StaticBox(self, wx.ID_ANY, " Temperatures ")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(10)
		t = wx.StaticText(self, wx.ID_ANY, "Bed: ", size=(labelWidth, -1), style=stStyle)
		t.SetFont(lbFont)
		hsz.Add(t)
		hsz.AddSpacer(spacerWidth)
		self.stBedTemps = wx.StaticText(self, wx.ID_ANY, "- / -", size=(fieldWidth, -1))
		self.stBedTemps.SetFont(lFont)
		hsz.Add(self.stBedTemps)
		bsizer.Add(hsz)

		self.stToolTemps = {}
		for tool in self.tools:
			hsz = wx.BoxSizer(wx.HORIZONTAL)
			hsz.AddSpacer(10)
			t = wx.StaticText(self, wx.ID_ANY, "%s: " % tool.capitalize(), size=(labelWidth, -1), style=stStyle)
			t.SetFont(lbFont)
			hsz.Add(t)
			hsz.AddSpacer(spacerWidth)
			self.stToolTemps[tool] = wx.StaticText(self, wx.ID_ANY, "- / -", size=(fieldWidth, -1))
			self.stToolTemps[tool].SetFont(lFont)
			hsz.Add(self.stToolTemps[tool])
			bsizer.Add(hsz)

		bsizer.AddSpacer(10)
		statsz.Add(bsizer)

		boxfan = wx.StaticBox(self, wx.ID_ANY, " Fan ")
		fansz = wx.StaticBoxSizer(boxfan, wx.VERTICAL)

		self.fan = Fan(self, self.server)

		fansz.AddSpacer(10)
		fansz.Add(self.fan)
		fansz.AddSpacer(10)

		statsz.AddSpacer(5)
		statsz.Add(fansz)

		boxJog = wx.StaticBox(self, wx.ID_ANY, " Jog ")
		jogsz = wx.StaticBoxSizer(boxJog, wx.VERTICAL)

		h = wx.BoxSizer(wx.HORIZONTAL)
		self.axesXY = ImageMap(self, self.images.pngControl_xy)
		self.axesXY.SetToolTip("Move X/Y axes")
		self.axesXY.setHotSpots(self.onImageClickXY, imageMapXY)
		self.axisZ = ImageMap(self, self.images.pngControl_z)
		self.axisZ.SetToolTip("Move Z axis")
		self.axisZ.setHotSpots(self.onImageClickZ, imageMapZ)

		if os.name == 'posix':
			h.AddSpacer(20)
		h.Add(self.axesXY)
		if os.name == 'posix':
			h.AddSpacer(20)
		h.Add(self.axisZ)

		jogsz.Add(h)

		h = wx.BoxSizer(wx.HORIZONTAL)
		h.AddSpacer(10)

		self.scXYSpeed = wx.SpinCtrl(self, wx.ID_ANY, "",
				size=(120 if os.name == 'posix' else 70, -1), style=wx.ALIGN_RIGHT)
		self.scXYSpeed.SetFont(lbFont)
		self.scXYSpeed.SetRange(10, 1800)
		self.scXYSpeed.SetValue(self.xySpeed)
		self.Bind(wx.EVT_SPINCTRL, self.onScXYSpeed, self.scXYSpeed)

		self.scZSpeed = wx.SpinCtrl(self, wx.ID_ANY, "",
				size=(120 if os.name == 'posix' else 70, -1), style=wx.ALIGN_RIGHT)
		self.scZSpeed.SetFont(lbFont)
		self.scZSpeed.SetRange(10, 600)
		self.scZSpeed.SetValue(self.zSpeed)
		self.Bind(wx.EVT_SPINCTRL, self.onScZSpeed, self.scZSpeed)

		st = wx.StaticText(self, wx.ID_ANY, "X/Y:")
		st.SetFont(lbFont)
		h.Add(st, 0, wx.TOP, 5)
		h.AddSpacer(5)
		h.Add(self.scXYSpeed)
		st = wx.StaticText(self, wx.ID_ANY, " cm/m")
		st.SetFont(lbFont)
		h.Add(st, 0, wx.TOP, 5)

		h.AddSpacer(10)

		st = wx.StaticText(self, wx.ID_ANY, "Z:")
		st.SetFont(lbFont)
		h.Add(st, 0, wx.TOP, 5)
		h.AddSpacer(5)
		h.Add(self.scZSpeed)
		st = wx.StaticText(self, wx.ID_ANY, " cm/m")
		st.SetFont(lbFont)
		h.Add(st, 0, wx.TOP, 5)

		h.AddSpacer(10)

		jogsz.AddSpacer(5)
		jogsz.Add(h)
		jogsz.AddSpacer(5)

		boxFil = wx.StaticBox(self, wx.ID_ANY, " Extrusion ")
		filsz = wx.StaticBoxSizer(boxFil, wx.VERTICAL)

		if self.nExtr > 1:
			self.chTool = wx.Choice(self, wx.ID_ANY, choices=self.tools)
			self.chTool.SetFont(lFont)
			self.chTool.SetSelection(0)
			self.Bind(wx.EVT_CHOICE, self.onChTools, self.chTool)
			filsz.Add(self.chTool, 0, wx.ALIGN_CENTER, 0)
			filsz.AddSpacer(5)

		self.axisE = ImageMap(self, self.images.pngControl_e)
		self.axisE.SetToolTip("Extrude/Retract")
		self.axisE.setHotSpots(self.onImageClickE, imageMapE)
		filsz.Add(self.axisE, 1, wx.ALIGN_CENTER, 0)

		filsz.AddSpacer(10)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(5)
		st = wx.StaticText(self, wx.ID_ANY, "mm:")
		st.SetFont(lbFont)
		hsz.Add(st, 0, wx.TOP, 5)
		hsz.AddSpacer(5)

		self.scEDist = wx.SpinCtrl(self, wx.ID_ANY, "",
				  size=(120 if os.name == 'posix' else 50, -1), style=wx.ALIGN_RIGHT)
		self.scEDist.SetFont(lbFont)
		self.scEDist.SetRange(1, 100)
		self.scEDist.SetValue(self.eLength)
		self.Bind(wx.EVT_SPINCTRL, self.onScEDist, self.scEDist)
		hsz.Add(self.scEDist, 0, wx.ALL, 0)
		hsz.AddSpacer(5)
		filsz.Add(hsz)

		filsz.AddSpacer(10)

		self.cbColdExt = wx.CheckBox(self, wx.ID_ANY, "Allow Cold")  # , style=wx.ALIGN_RIGHT)
		self.cbColdExt.SetValue(False)
		self.cbColdExt.SetToolTip("Allow cold extrusion")
		self.cbColdExt.SetFont(lbFont)
		filsz.Add(self.cbColdExt, 0, wx.ALIGN_CENTER, 0)
		self.Bind(wx.EVT_CHECKBOX, self.onCbColdExt, self.cbColdExt)
		filsz.AddSpacer(5)

		boxhtr = wx.StaticBox(self, wx.ID_ANY, " Heaters ")
		htrsz = wx.StaticBoxSizer(boxhtr, wx.VERTICAL)

		self.bedHeater = Heater(self, self.server, self.server.bed.target, None, "Bed", 0, 120, self.bedPresets)
		htrsz.AddSpacer(5)
		htrsz.Add(self.bedHeater)

		self.toolHeater = {}
		for i in range(self.nExtr):
			h = Heater(self, self.server, self.server.tool.target, i, "Tool%d" % i, 0, 230, self.toolPresets)
			htrsz.AddSpacer(5)
			htrsz.Add(h)
			self.toolHeater[self.tools[i]] = h

		htrsz.AddSpacer(5)

		szh.AddSpacer(10)
		szh.Add(statsz)

		rtsz = wx.BoxSizer(wx.VERTICAL)
		ursz = wx.BoxSizer(wx.HORIZONTAL)
		lrsz = wx.BoxSizer(wx.HORIZONTAL)
		ursz.AddSpacer(5)
		ursz.Add(jogsz)
		ursz.AddSpacer(5)
		ursz.Add(filsz)
		ursz.AddSpacer(5)
		rtsz.Add(ursz)

		mrsz = wx.BoxSizer(wx.HORIZONTAL)
		mrsz.AddSpacer(5)

		rtsz.Add(mrsz)

		lrsz.AddSpacer(5)
		lrsz.Add(htrsz)
		lrsz.AddSpacer(5)
		rtsz.Add(lrsz)

		szh.Add(rtsz)

		szh.AddSpacer(10)
		sz.Add(szh)

		sz.AddSpacer(10)

		sz.Fit(self)
		self.SetSizer(sz)
		self.Fit()

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
		self.Bind(EVT_FIRMWARE, self.evtAllSettings)
		self.Bind(EVT_TERMMSG, self.evtTermMessage)
		self.Bind(EVT_LOGMSG, self.evtLogMessage)
		self.Bind(EVT_ERRMSG, self.evtErrorMessage)
		self.Bind(EVT_GCODE, self.evtUpdateGCDlg)

		self.startTimer()
		rc, json = self.server.state(exclude=["temperature", "sd"])
		if rc < 400:
			try:
				s = json["state"]["text"]
				self.lastReportedPrinterState = s
			except:
				pass

		self.server.subscribe({"job": self.jobUpdate,
							   "message": self.messageUpdate,
							   "log": self.logUpdate,
							   "progress": self.progressUpdate,
							   "state": self.stateUpdate,
							   "plugin": self.pluginUpdate})

	def MenuFileList(self, evt):
		self.fileDlg = FileDlg(self, self.server, self.pname, self.dismissFileDlg)

	def MenuFileUpload(self, evt):
		wildcard = "GCode (*.gcode)|*.gcode;*.GCODE|" \
				   "All files (*.*)|*.*"

		dlg = wx.FileDialog(
			self, message="Choose a GCode file",
			defaultDir=self.settings.getSetting("lastDirectory", dftValue="."),
			defaultFile="",
			wildcard=wildcard,
			style=wx.FD_OPEN)

		rc = dlg.ShowModal()
		if rc == wx.ID_OK:
			path = dlg.GetPath().encode('ascii', 'ignore').decode("utf-8") 
			dpath = os.path.dirname(path)
			pprint.pprint(dpath)
			self.settings.setSetting("lastDirectory", dpath)

		dlg.Destroy()
		if rc != wx.ID_OK:
			return

		bn = os.path.basename(path)
		dlg = UploadDestinationDlg(self, self.pname, self.server, bn)
		rc = dlg.ShowModal()
		if rc == wx.ID_OK:
			fn = dlg.getFn()

		dlg.Destroy()
		if rc == wx.ID_OK:
			gcode = self.loadGCode(path)
			try:
				rc = self.server.gfile.uploadString("".join(gcode), fn, to=5)[0]
			except:
				dlg = wx.MessageDialog(self, "Unable to upload G Code file to printer",
									   "Upload Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
				return

			if rc < 400:
				dlg = wx.MessageDialog(self, "File %s successfully uploaded to %s" % (path, fn),
									   "File Upload", wx.OK | wx.ICON_INFORMATION)
				dlg.ShowModal()
				dlg.Destroy()
			else:
				dlg = wx.MessageDialog(self, "Error %d Uploading file %s" % (rc, path),
									   "Upload Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
				
	def MenuFileUpdate(self, evt):
		pi = self.server.getPlugin("softwareupdate")
		rc, rv = pi.get("check")
		if rc < 400:
			piList = rv["information"]
			updateMessage = []
			octoMessage = ""
			for p in sorted(piList):
				if piList[p]["updateAvailable"]:
					#pprint.pprint(piList[p])
					if p == "octoprint":						
						octoMessage = "%s  %s  =>  %s" % (piList[p]["displayName"], piList[p]["information"]["local"]["value"], piList[p]["information"]["remote"]["value"])
					else:
						updateMessage.append("%s  %s  =>  %s" % (piList[p]["displayName"], piList[p]["information"]["local"]["value"], piList[p]["information"]["remote"]["value"]))
						
			if len(updateMessage) == 0 and octoMessage == "":
				dlg = wx.MessageDialog(self, "Octoprint is up to date", "No Updates Available",
					wx.OK | wx.ICON_INFORMATION)
				dlg.ShowModal()
				dlg.Destroy()
			else:
				ustr = ""
				if octoMessage != "":
					ustr = "\n" + octoMessage + "\n\n\n"
					
				ustr += "\n".join(updateMessage)
				dlg = wx.MessageDialog(self, ustr, "Updates Available",
					wx.OK | wx.ICON_INFORMATION)
				dlg.ShowModal()
				dlg.Destroy()
				
		else:
			print()
			dlg = wx.MessageDialog(self, "Unable to retrieve plugin information.  rc = %d" % rc,
				"Retrieve Updates Error", wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()

	def MenuViewTemps(self, evt):
		if self.tempGraph is None:
			self.tempGraph = TempGraph(self, self.pname, self.settings, self.images, self.tempHistory, self.nextData, self.exitTempDlg)
		self.tempGraph.Show()

	def exitTempDlg(self):
		self.tempGraph.Destroy()
		self.tempGraph = None

	def MenuViewGCode(self, evt):
		if self.selectedFilePath is None:
			self.GCode = GCode("", self.acceleration, self.filamentDiameter, self.nExtr)
		else:
			try:
				rc, gc = self.server.gfile.downloadFileByName(self.selectedFileOrigin, self.selectedFilePath, to=5)
			except:
				dlg = wx.MessageDialog(self, "Unable to retrieve G Code from printer.",
						"Retrieve Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
				return

			if rc < 400:
				self.GCode = GCode(gc, self.acceleration, self.filamentDiameter, self.nExtr)
			else:
				dlg = wx.MessageDialog(self, "Unable to retrieve G Code from printer.  Error = %d" % rc,
						"Retrieve Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
				return

		self.gcdlg = GCodeDlg(self, self.server, self.GCode, self.selectedFilePath, self.pname, self.settings, self.images, self.exitGCDlg)
		self.gcdlg.Show()

	def exitGCDlg(self):
		self.gcdlg.Destroy()
		self.gcdlg = None

	def MenuViewTerminal(self, evt):
		self.termdlg = TerminalDlg(self, self.server, self.pname, self.settings, self.images, self.exitTermDlg)
		self.termdlg.Show()

	def exitTermDlg(self):
		self.termdlg.Destroy()
		self.termdlg = None

	def MenuViewFirmware(self, evt):
		self.startFwCollection(self.flash, self.haveAllSettings)

	def startFwCollection(self, container, callback):
		self.collectingFw = True
		self.collCompleteCB = callback
		FWC.start(container, self.hasZProbe)
		self.server.command("M503")

	def haveAllSettings(self):
		self.fwdlg = FirmwareDlg(self, self.server, self.pname, self.flash, self.exitFwDlg)
		self.fwdlg.Show()

	def exitFwDlg(self):
		self.fwdlg.Destroy()
		self.fwdlg = None
				
	def MenuViewWebcam(self, evt):
		player = self.settings.getSetting("videoPlayer", dftValue="ffplay")
		options = self.settings.getSetting("videoPlayerOptions", self.pname, dftValue=["-vf", "hflip,vflip"])
		uri = self.settings.getSetting("webcamUri", dftValue="webcam/?action=stream")
		cmdList = [player] + options + ["-window_title", "%s webcam" % self.pname, "http://%s/%s" % (self.ipAddr, uri)]
		
		if self.pWebcam is not None:
			self.pWebcam.kill()

		if os.name == 'posix':
			self.pWebcam = subprocess.Popen(cmdList, stderr=subprocess.DEVNULL)
		else:
			si = subprocess.STARTUPINFO()
			si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			si.wShowWindow = subprocess.SW_HIDE
			self.pWebcam = subprocess.Popen(cmdList, stderr=subprocess.DEVNULL, startupinfo=si)
		
	def MenuConnect(self, evt):
		dftPort = self.settings.getSetting("port", self.pname, "/dev/ttyACM0")
		dftBaudrate = self.settings.getSetting("baudrate", self.pname, 115200)
		
		rc, json = self.server.getConnectionInfo()
		if rc >= 400:
			self.server.connect(port=dftPort, baudrate=dftBaudrate)
			return
		
		if not "options" in json:
			self.server.connect(port=dftPort, baudrate=dftBaudrate)
			return
		
		if "baudratePreference" in json["options"]:
			baudrate = json["options"]["baudratePreference"]
		else:
			baudrate = dftBaudrate
			
		if "portPreference" in json["options"]:
			port = json["options"]["portPreference"]
		else:
			port = dftPort
			
		if "ports" not in json["options"]:
			ports = []
		else:
			ports = json["options"]["ports"]
			
		if "baudrates" not in json["options"]:
			baudrates = []
		else:
			baudrates = json["options"]["baudrates"]
		
		dlg = ConnectDlg(self, self.pname, port, ports, baudrate, baudrates)
		rc = dlg.ShowModal()
		if rc == wx.ID_OK:
			baudrate, port = dlg.getResults()
			
		dlg.Destroy()
		if rc != wx.ID_OK:
			return
			
		self.server.connect(port=port, baudrate=baudrate)
		
	def MenuDisconnect(self, evt):
		self.server.disconnect()
		
	def MenuOctolapse(self, evt):
		pi = self.server.getPlugin("octolapse")
		rc, rv = pi.post("loadSettings")
		if rv is None:
			dlg = wx.MessageDialog(self, "Error querying plugin: octolapse",
								   "Plugin Error", wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()
			return 
		
		dlg = OctolapseDlg(self, self.pname, pi, rv)	
		rc = dlg.ShowModal()
		if rc != wx.ID_OK:
			dlg.Destroy()
			return 
		
		failedProfiles = []
		successfulProfiles = []
	
		hasProfileChanged = { "Printer": dlg.hasPrinterProfileChanged,
						"Rendering": dlg.hasRenderingProfileChanged,
						"Snapshot": dlg.hasSnapshotProfileChanged,
						"Stabilization": dlg.hasStabilizationProfileChanged }
		
		for pf in sorted(hasProfileChanged.keys()):
			p = hasProfileChanged[pf]()
			if p is not None:
				rc, rv = pi.post("setCurrentProfile", {"profileType": pf, "guid": p, "client_id": ""})
				if rv is None or not rv["success"]:
					failedProfiles.append(pf)
				else:
					successfulProfiles.append(pf)

		hasShowToggled = {
			"show_extruder_state_changes": dlg.hasShowExtruderStateChanged,
			"show_position_changes": dlg.hasShowPositionChanged,
			"show_position_state_changes": dlg.hasShowPositionStateChanged,
			"show_trigger_state_changes": dlg.hasShowTriggerStateChanged}
		failedToggles = []
		successfulToggles = []					
		for tg in sorted(hasShowToggled.keys()):
			p = hasShowToggled[tg]()
			if p is not None:
				rc, rv = pi.post("toggleInfoPanel", {"panel_type": tg})
				if rv is None or not rv["success"]:
					failedToggles.append("{} ({})".format(tg, p))
				else:
					successfulToggles.append("{} ({})".format(tg, p))
			
		p = dlg.hasEnabledStatusChanged()
		enableResult = None
		if p is not None:
			rc, rv = pi.post("setEnabled", {"is_octolapse_enabled": p})
			if rv is None or not rv["success"]:
				# failed
				if p:
					enableResult = "Unable to ENABLE OctoLapse."
				else:
					enableResult = "Unable to DISABLE OctoLapse."
			else:
				# succeeded
				if p:
					enableResult = "OctoLapse successfully ENABLED."
				else:
					enableResult = "OctoLapse successfully DISABLED."

		message = []			
		if len(failedProfiles) > 0:
			message.append("Failed profile Updates: " + ",".join(failedProfiles))
		if len(successfulProfiles) > 0:
			message.append("Successful profile Updates: " + ",".join(successfulProfiles))
		if len(failedToggles) > 0:
			message.append("Failed toggles:\n  " + "\n  ".join(failedToggles))
		if len(successfulToggles) > 0:
			message.append("Successful toggles:\n  " + "\n  ".join(successfulToggles))
		if enableResult is not None:
			message.append(enableResult)
			
		dlg.Destroy()
		if len(message) > 0:
			dlg = wx.MessageDialog(self, "\n".join(message),
								   "Octolapse Configuration Result", wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()


	def nextData(self):
		return self.currentTemps

	def loadGCode(self, fn):
		if fn is None:
			return None

		try:
			return list(open(fn))
		except:
			dlg = wx.MessageDialog(self, "Error Opening file %s" % fn,
								   "Open Error", wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()
			return None

	def dismissFileDlg(self, cmd):
		self.fileDlg.Destroy()
		self.fileDlg = None

		if not "action" in cmd.keys():
			return

		if not "path" in cmd.keys() or not "origin" in cmd.keys():
			return

		if cmd["action"] == "select":
			if self.printerState == "Printing":
				dlg = wx.MessageDialog(self, "Unable to select a new file while still printing",
									   "Printer busy", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
			else:
				try:
					self.server.gfile.selectFile(cmd["origin"], cmd["path"], prt=False)
				except:
					dlg = wx.MessageDialog(self, "Unable to select a new file to print",
										   "Printer error", wx.OK | wx.ICON_ERROR)
					dlg.ShowModal()
					dlg.Destroy()
					return

				self.selectedFileOrigin = cmd["origin"]
				self.selectedFilePath = cmd["path"]
				self.enablePrintingControls()

		elif cmd["action"] == "delete":
			try:
				self.server.gfile.deleteFile(cmd["origin"], cmd["path"])
			except:
				dlg = wx.MessageDialog(self, "Unknown error during file delete",
									   "Download Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
				return

		elif cmd["action"] == "download" and "url" in cmd.keys():
			try:
				rc, gc = self.server.gfile.downloadFile(cmd["url"], to=5)
			except:
				dlg = wx.MessageDialog(self, "Unknown error during file download",
									   "Download Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
				return

			if rc >= 400:
				dlg = wx.MessageDialog(self, "Error code from file download: %d" % rc,
									   "Download Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
			else:
				self.saveFileAs(gc.split("\n"))


	def saveFileAs(self, gcode):
		wildcard = "GCode (*.gcode)|*.gcode;*.GCODE"

		dlg = wx.FileDialog(
			self, message="Save as ...", defaultDir=self.settings.getSetting("lastDirectory", dftValue="."),
			defaultFile="", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

		val = dlg.ShowModal()

		if val != wx.ID_OK:
			dlg.Destroy()
			return

		path = dlg.GetPath()
		dlg.Destroy()

		dpath = os.path.dirname(path)
		self.settings.setSetting("lastDirectory", dpath)

		ext = os.path.splitext(os.path.basename(path))[1]
		if ext == "":
			path += ".gcode"

		self.saveFile(path, gcode)

	def saveFile(self, path, gcode):
		fp = open(path, 'w')

		for ln in gcode:
			fp.write("%s\n" % ln.rstrip())

		fp.close()

		dlg = wx.MessageDialog(self, "G Code file\n" + path + "\nwritten.",
							   'Save Successful', wx.OK | wx.ICON_INFORMATION)
		dlg.ShowModal()
		dlg.Destroy()

	def enableManualControls(self, flag=True):
		self.enableMovementControls(flag)
		self.enableTemperatureControls(flag)

	def enableMovementControls(self, flag=True):
		self.axesXY.enableControls(flag)
		self.axisZ.enableControls(flag)
		self.axisE.enableControls(flag)
		self.cbColdExt.Enable(flag)
		self.scEDist.Enable(flag)
		self.scXYSpeed.Enable(flag)
		self.scZSpeed.Enable(flag)
		self.movementEnabled = flag

	def enableTemperatureControls(self, flag=True):
		self.bedHeater.enableControls(flag)
		for t in self.tools:
			self.toolHeater[t].enableControls(flag)
		self.temperatureEnabled = flag

	def enablePrintingControls(self):
		# printing controls are Print/Restart, Pause/Resume
		if self.printerState == "Printing":
			self.bPrint.Enable(False)
			self.bPause.Enable(True)
			self.bCancel.Enable(True)
			self.bPreheat.Enable(False)
		elif self.printerState == "Paused" and self.printFileName is not None:
			self.bPrint.Enable(True)
			self.bPause.Enable(True)
			self.bCancel.Enable(True)
			self.bPreheat.Enable(True)
		elif self.printerState == "Operational" and self.printFileName is not None:
			self.bPrint.Enable(True)
			self.bPause.Enable(False)
			self.bCancel.Enable(False)
			self.bPreheat.Enable(True)
		else:
			self.bPrint.Enable(False)
			self.bPause.Enable(False)
			self.bCancel.Enable(False)
			self.bPreheat.Enable(False)

	def onBPrint(self, evt):
		if self.printerState == "Paused":
			self.bPrint.SetBitmap(self.images.pngPrint)
			try:
				self.server.job.restart()
			except:
				dlg = wx.MessageDialog(self, "Unknown error while restarting job",
									   "Restart Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
		else:
			try:
				self.server.job.start()
			except:
				dlg = wx.MessageDialog(self, "Unknown error while starting job",
									   "Start Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()

	def onBPause(self, evt):
		if self.printerState == "Paused":
			self.bPrint.SetBitmap(self.images.pngPrint)
			try:
				self.server.job.resume()
			except:
				dlg = wx.MessageDialog(self, "Unknown error while resuming job",
									   "Resume Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
		else:
			self.bPrint.SetBitmap(self.images.pngRestart)
			try:
				self.server.job.pause()
			except:
				dlg = wx.MessageDialog(self, "Unknown error while pausing job",
									   "Pause Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()

	def onBCancel(self, evt):
		self.bPrint.SetBitmap(self.images.pngPrint)
		try:
			self.server.job.cancel()
		except:
			dlg = wx.MessageDialog(self, "Unknown error while cancelling job",
								   "Cancel Error", wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()

	def onBPreheat(self, evt):
		if self.doPreheat:
			try:
				self.server.job.preheat()
			except:
				dlg = wx.MessageDialog(self, "Unknown error while attempting job preheat",
									   "Preheat Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
				return

			self.bPreheat.SetBitmap(self.images.pngCooldown)
		else:
			self.bedHeater.setHeater(0)
			for h in self.tools:
				self.toolHeater[h].setHeater(0)
			self.bPreheat.SetBitmap(self.images.pngPreheat)

		self.doPreheat = not self.doPreheat

	def setPreheatButton(self, nz):
		if nz != 0:
			self.bPreheat.SetBitmap(self.images.pngCooldown)
			self.doPreheat = False
		else:
			self.bPreheat.SetBitmap(self.images.pngPreheat)
			self.doPreheat = True

	def startTimer(self):
		self.timer.Start(1000)

	def stopTimer(self):
		self.timer.Stop()

	def OnTimer(self, evt):
		if self.msgTimer > 0:
			self.msgTimer -= 1
			if self.msgTimer == 0:
				self.SetStatusText("")

		updateTemps = False
		try:
			rv, json = self.server.state()
		except:
			evt = ErrorEvent(message="Unable to retrieve Bed/Tool state", terminate=True)
			wx.PostEvent(self, evt)
			rv = None
		else:
			if rv == RC_CONNECT_TIMEOUT:
				evt = ErrorEvent(message="Connection timeout retrieving Bed/Tool state", terminate=True)
				wx.PostEvent(self, evt)
				
			elif rv == RC_READ_TIMEOUT:
				self.toRead += 1
				if self.toRead > MAX_READ_TIMEOUTS:
					evt = ErrorEvent(message="Read Timeout retrieving Bed/Tool state", terminate=True)
					wx.PostEvent(self, evt)
			else:
				temps = json["temperature"]
				updateTemps = True	
				self.toRead = 0

		nzct = 0
		if updateTemps:
			self.currentTemps = {}
			if rv < 400:
				try:
					t = "%7.1f / %7.1f" % (temps['bed']['actual'], temps['bed']['target'])
					self.currentTemps['bed'] = {'actual': temps['bed']['actual'], 'target': temps['bed']['target']}
				except:
					t = "- / -"
					self.currentTemps['bed'] = {'actual': 0, 'target': 0}
	
			else:
				t = "- / -"
				self.currentTemps['bed'] = {'actual': 0, 'target': 0}
	
			self.stBedTemps.SetLabel(t)
			t = self.currentTemps['bed']['target']
			self.bedHeater.setTarget(t)
			nzct = 1 if t != 0 else 0

			for tool in self.tools:
				if rv < 400:
					try:
						t = "%7.1f / %7.1f" % (temps[tool]['actual'], temps[tool]['target'])
						self.currentTemps[tool] = {'actual': temps[tool]['actual'], 'target': temps[tool]['target']}
					except:
						t = "- / -"
						self.currentTemps[tool] = {'actual': 0, 'target': 0}
				else:
					t = "- / -"
					self.currentTemps[tool] = {'actual': 0, 'target': 0}
				self.stToolTemps[tool].SetLabel(t)
	
				t = self.currentTemps[tool]['target']
				if t != 0: nzct += 1
				self.toolHeater[tool].setTarget(t)
	
			self.setPreheatButton(nzct)
			self.tempHistory.append(self.currentTemps.copy())
			if len(self.tempHistory) > XCOUNT:
				self.tempHistory = self.tempHistory[-XCOUNT:]

		if self.printerState != self.lastReportedPrinterState:
			self.printerState = self.lastReportedPrinterState
			if self.printerState is None:
				self.stPrinterStatus.SetLabel("-")
			else:
				if self.printerState in ["Printing"]:
					self.enableMovementControls(False)
				else:
					self.enableMovementControls(True)

				self.stPrinterStatus.SetLabel(self.printerState)
				self.enablePrintingControls()

		if self.printFileName != self.lastReportedFileName:
			self.printFileName = self.lastReportedFileName
			if self.printFileName is None:
				self.stPrinterFile.SetLabel("-")
				self.GCode = None
				try:
					self.gcdlg.Destroy()
				except:
					pass
				self.gcdlg = None
			else:
				self.stPrinterFile.SetLabel(self.printFileName)
				if self.gcdlg is not None:
					evt = GCodeEvent()
					wx.PostEvent(self, evt)

			self.enablePrintingControls()

		for t in self.tools:
			if self.filamentData[t] != self.reportedFilamentData[t]:
				self.filamentData[t] = self.reportedFilamentData[t]
				if self.filamentData[t] is None:
					self.stPrinterFilament[t].SetLabel("- / -")
				else:
					self.stPrinterFilament[t].SetLabel(self.filamentData[t])

		if self.estimatedPrintTime != self.lastReportedEstPrintTime:
			self.estimatedPrintTime = self.lastReportedEstPrintTime
			if self.estimatedPrintTime is None:
				self.stPrinterEstPrintTime.SetLabel("-")
			else:
				self.stPrinterEstPrintTime.SetLabel(formatElapsed(self.estimatedPrintTime))

		if self.completion != self.lastReportedCompletion:
			self.completion = self.lastReportedCompletion
			if self.completion is None:
				self.stCompletion.SetLabel("-")
			else:
				self.stCompletion.SetLabel("%7.2f%%" % self.completion)

		if self.printTime != self.lastReportedPrintTime:
			self.printTime = self.lastReportedPrintTime
			if self.printTime is None:
				self.stPrintTime.SetLabel("-")
			else:
				self.stPrintTime.SetLabel(formatElapsed(self.printTime))

		if self.printTimeLeft != self.lastReportedPrintTimeLeft or self.printTimeLeftOrigin != self.lastReportedPrintTimeLeftOrigin:
			self.printTimeLeft = self.lastReportedPrintTimeLeft
			self.printTimeLeftOrigin = self.lastReportedPrintTimeLeftOrigin
			if self.printTimeLeft is None:
				self.stPrintTimeLeft.SetLabel("-")
			elif self.printTimeLeftOrigin is None:
				self.stPrintTimeLeft.SetLabel(formatElapsed(self.printTimeLeft))
			else:
				self.stPrintTimeLeft.SetLabel("%s (%s)" % (formatElapsed(self.printTimeLeft), self.printTimeLeftOrigin))

		if self.fileSize is None:
			self.stPrinted.SetLabel("- / -")
		else:
			if self.filePos != self.lastReportedFilePos:
				self.filePos = self.lastReportedFilePos
				if self.filePos is None:
					self.stPrinted.SetLabel("- / -")
				else:
					self.stPrinted.SetLabel("%s / %s" % (approximateValue(self.filePos), self.approximateFileSize))

		if not self.gcdlg is None and self.printerState == "Printing":
			self.gcdlg.setPrintPosition(self.filePos)

		if self.layerInfo != self.lastReportedLayerInfo:
			self.layerInfo = self.lastReportedLayerInfo
			if self.layerInfo is None:
				self.stLayer.SetLabel("- / -")
			else:
				self.stLayer.SetLabel(self.layerInfo)

		if self.heightInfo != self.lastReportedHeightInfo:
			self.heightInfo = self.lastReportedHeightInfo
			if self.heightInfo is None:
				self.stHeight.SetLabel("- / -")
			else:
				self.stHeight.SetLabel(self.heightInfo)

	def jobUpdate(self, json):
		try:
			self.lastReportedFileName = json['file']['name']
			self.selectedFileOrigin = json['file']['origin']
			self.selectedFilePath = json['file']['name']
		except:
			self.lastReportedFileName = "-"
			self.selectedFileOrigin = None
			self.selectedFilePath = None

		if 'filament' in json.keys():
			fd = json['filament']
			for t in self.tools:
				if fd is not None and t in fd.keys():
					self.reportedFilamentData[t] = "%.2fm / %.2fcm3" % (fd[t]["length"] / 1000.0, fd[t]["volume"])
				else:
					self.reportedFilamentData[t] = None

		try:
			self.lastReportedEstPrintTime = int(json['estimatedPrintTime'])
		except:
			self.lastReportedEstPrintTime = None

		try:
			x = json['file']['size']
			if self.fileSize is None or x != self.fileSize:
				self.fileSize = x
				self.approximateFileSize = approximateValue(self.fileSize)
		except:
			self.fileSize = None
			self.approximateFileSize = " -"

	def messageUpdate(self, msg):
		if msg.startswith("ok "):
			return

		if msg.startswith("echo:"):
			msg = msg[5:]

		msg = msg.strip()
		if len(msg) == 0:
			return

		if msg.startswith("T:"):
			return

		if msg.startswith("X:"):
			return

		evt = LogEvent(message=msg)
		wx.PostEvent(self, evt)

	def evtLogMessage(self, evt):
		self.logMessage(evt.message)

	def evtErrorMessage(self, evt):
		self.logMessage(evt.message)
		try:
			if evt.terminate:
				self.killDialog()
		except:
			pass

	def evtUpdateGCDlg(self, evt):		
		downloadGCode = True
		try:
			rc, gc = self.server.gfile.downloadFileByName(self.selectedFileOrigin, self.selectedFilePath, to=5)
		except:
			self.logMessage("Unable to download G Code File")
			self.GCode = None
			try:
				self.gcdlg.Destroy()
			except:
				pass
			self.gcdlg = None
			downloadGCode = False

		if downloadGCode:
			if rc < 400:
				self.GCode = GCode(gc, self.acceleration, self.filamentDiameter, self.nExtr)
				self.gcdlg.reloadGCode(self.GCode, self.printFileName)
			else:
				self.logMessage("Unable to download G Code File")
				self.GCode = None
				try:
					self.gcdlg.Destroy()
				except:
					pass
				self.gcdlg = None
		
	def logMessage(self, msg, sec=10):
		self.msgTimer = sec
		self.SetStatusText(msg)

	def logUpdate(self, logs):
		pfx = "Recv: echo:  "
		for l in logs:
			evt = TerminalEvent(message=l)
			wx.PostEvent(self, evt)
			if l.startswith(pfx) and self.collectingFw:
				FWC.checkFwCommand(l[len(pfx):])
				if FWC.collectionComplete():
					self.collectingFw = False
					evt = FirmwareEvent(completed=True)
					wx.PostEvent(self, evt)

	def evtAllSettings(self, evt):
		cb = self.collCompleteCB
		self.collCompleteCB = None
		cb()

	def evtTermMessage(self, evt):
		if self.termdlg is not None:
			self.termdlg.logLine(evt.message)

	def progressUpdate(self, json):
		try:
			self.lastReportedCompletion = json["completion"]
		except:
			self.lastReportedCompletion = None

		try:
			self.lastReportedPrintTime = json["printTime"]
		except:
			self.lastReportedPrintTime = None

		try:
			self.lastReportedPrintTimeLeft = json["printTimeLeft"]
		except:
			self.lastReportedPrintTimeLeft = None

		try:
			self.lastReportedPrintTimeLeftOrigin = json["printTimeLeftOrigin"]
		except:
			self.lastReportedPrintTimeLeftOrigin = None

		try:
			self.lastReportedFilePos = json['filepos']
		except:
			self.lastReportedFilePos = None

	def stateUpdate(self, json):
		if "text" in json.keys():
			self.lastReportedPrinterState = json["text"]

	def pluginUpdate(self, json):
		if 'plugin' not in json.keys():
			return

		if json['plugin'] == 'DisplayLayerProgress':
			try:
				self.lastReportedLayerInfo = json['data']['stateMessage']
			except:
				self.lastReportedLayerInfo = None

			try:
				self.lastReportedHeightInfo = json['data']['heightMessage']
			except:
				self.lastReportedHeightInfo = None
		else:
			pass
			#print ("plugin: %s" % json['plugin'])
			#pprint.pprint(json)

	def onImageClickXY(self, command):
		try:
			if command == "HX":
				self.server.printHead.home([True, False, False])
			elif command == "HY":
				self.server.printHead.home([False, True, False])
			elif command == "HZ":
				self.server.printHead.home([False, False, True])
			elif command == "HA":
				self.server.printHead.home([True, True, True])
			elif command == "Y+1":
				self.server.printHead.jog([0, 0.1, 0], False, self.xySpeed)
			elif command == "Y+2":
				self.server.printHead.jog([0, 1, 0], False, self.xySpeed)
			elif command == "Y+3":
				self.server.printHead.jog([0, 10, 0], False, self.xySpeed)
			elif command == "Y+4":
				self.server.printHead.jog([0, 100, 0], False, self.xySpeed)
			elif command == "Y-1":
				self.server.printHead.jog([0, -0.1, 0], False, self.xySpeed)
			elif command == "Y-2":
				self.server.printHead.jog([0, -1, 0], False, self.xySpeed)
			elif command == "Y-3":
				self.server.printHead.jog([0, -10, 0], False, self.xySpeed)
			elif command == "Y-4":
				self.server.printHead.jog([0, -100, 0], False, self.xySpeed)
			elif command == "X+1":
				self.server.printHead.jog([0.1, 0, 0], False, self.xySpeed)
			elif command == "X+2":
				self.server.printHead.jog([1, 0, 0], False, self.xySpeed)
			elif command == "X+3":
				self.server.printHead.jog([10, 0, 0], False, self.xySpeed)
			elif command == "X+4":
				self.server.printHead.jog([100, 0, 0], False, self.xySpeed)
			elif command == "X-1":
				self.server.printHead.jog([-0.1, 0, 0], False, self.xySpeed)
			elif command == "X-2":
				self.server.printHead.jog([-1, 0, 0], False, self.xySpeed)
			elif command == "X-3":
				self.server.printHead.jog([-10, 0, 0], False, self.xySpeed)
			elif command == "X-4":
				self.server.printHead.jog([-100, 0, 0], False, self.xySpeed)

		except:
			dlg = wx.MessageDialog(self, "Error moving X/Y axes",
								   "Job Error", wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()

	def onImageClickZ(self, command):
		try:
			if command == "Z+1":
				self.server.printHead.jog([0, 0, 0.1], False, self.zSpeed)
			elif command == "Z+2":
				self.server.printHead.jog([0, 0, 1], False, self.zSpeed)
			elif command == "Z+3":
				self.server.printHead.jog([0, 0, 10], False, self.zSpeed)
			elif command == "Z+4":
				self.server.printHead.jog([0, 0, 100], False, self.zSpeed)
			elif command == "Z-1":
				self.server.printHead.jog([0, 0, -0.1], False, self.zSpeed)
			elif command == "Z-2":
				self.server.printHead.jog([0, 0, -1], False, self.zSpeed)
			elif command == "Z-3":
				self.server.printHead.jog([0, 0, -10], False, self.zSpeed)
			elif command == "Z-4":
				self.server.printHead.jog([0, 0, -100], False, self.zSpeed)
		except:
			dlg = wx.MessageDialog(self, "Error moving Z axis",
								   "Job Error", wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()

	def onImageClickE(self, command):
		try:
			if command == "Retr":
				self.server.tool.retract(self.eLength)
			elif command == "Extr":
				self.server.tool.extrude(self.eLength)
			else:
				self.logMessage("Command not handled: (%s)" % command)
		except:
			dlg = wx.MessageDialog(self, "Error during extrude/retract",
								   "Extrude Error", wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()

	def onScEDist(self, evt):
		dist = self.scEDist.GetValue()
		if dist != self.eLength:
			self.eLength = dist
			self.settings.setSetting("eLength", str(dist), self.pname)

	def onScXYSpeed(self, evt):
		spd = self.scXYSpeed.GetValue()
		if spd != self.xySpeed:
			self.xySpeed = spd
			self.settings.setSetting("xySpeed", str(spd), self.pname)

	def onScZSpeed(self, evt):
		spd = self.scZSpeed.GetValue()
		if spd != self.zSpeed:
			self.zSpeed = spd
			self.settings.setSetting("zSpeed", str(spd), self.pname)

	def onChTools(self, evt):
		s = evt.GetSelection()
		if s == wx.NOT_FOUND:
			return

		if s != self.currentTool:
			self.currentTool = s
			self.server.tool.select(s)

	def onClose(self, evt):
		self.killDialog()

	def killDialog(self):
		self.sever()
		self.parent.connectionSevered(self.pname)

	def onCbColdExt(self, evt):
		if self.cbColdExt.GetValue():
			self.logMessage("Cold Extrusion Enabled", -1)
			try:
				self.server.command("M302 S0")
			except:
				dlg = wx.MessageDialog(self, "Unable to set for cold extrude",
									   "Printer Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
		else:
			if self.msgTimer <= 0:
				self.SetStatusText("")
				self.msgTimer = 0
			try:
				self.server.command("M302 S170")
			except:
				dlg = wx.MessageDialog(self, "Unable to clear for cold extrude",
									   "Printer Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()

	def sever(self):
		try:
			self.server.unsubscribe()
		except:
			pass

		try:
			self.stopTimer()
		except:
			pass

		try:
			self.fileDlg.Destroy()
		except:
			pass

		try:
			self.tempGraph.close()
			self.tempGraph.Destroy()
		except:
			pass

		try:
			self.gcdlg.Destroy()
		except:
			pass

		try:
			self.termdlg.Destroy()
		except:
			pass

		try:
			self.fwdlg.Destroy()
		except:
			pass
		
		if self.pWebcam is not None:
			try:
				self.pWebcam.kill()
			except:
				pass
