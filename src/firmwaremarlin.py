import os
import wx
import wx.lib.newevent
import configparser

from fwsettings import FwSettings

wildcard = "Firmware Files (*.fw)|*.fw|All Files (*.*)|*.*"


grpinfo = {'m92' : ['Steps per Unit - M92', 4, ['x', 'y', 'z', 'e'], ['X Steps', 'Y Steps', 'Z Steps', 'E Steps']],
		'm201' : ['Max Acceleration (mm/s2) - M201', 4, ['x', 'y', 'z', 'e'], ['X Maximum Acceleration', 'Y Maximum Acceleration', 'Z Maximum Acceleration', 'E Maximum Acceleration']],
		'm203' : ['Max Feed Rates (mm/s) - M203', 4, ['x', 'y', 'z', 'e'], ['X Maximum Feed Rate', 'Y Maximum Feed Rate', 'Z Maximum Feed Rate', 'E Maximum Feed Rate']],
		'm204' : ['Acceleration - M204', 3, ['p', 'r', 't'], ['Maximum Print Acceleration', 'Maximum Retraction Acceleration', 'Maximum Travel Acceleration']],
		'm205' : ['Advanced - M205', 6, ['s', 't', 'b', 'x', 'z', 'e'], ['Minimum Feed Rate', 'Minimum Travel', 'Minimum Segment Time', 'Maximum XY Jerk', 'Maximum Z Jerk', 'Maximum E Jerk']],
		'm301' : ['PID - M301', 3, ['p', 'i', 'd'], ['Proportional Value', 'Integral Value', 'Derivative Value']]}

grporder = ['m92', 'm201', 'm203', 'm204', 'm205', 'm301']

zprobeinfo = {'m851': ['Z Probe Offset - M851', 1, ['z'], ['Z Offset from extruder']]}
zprobeorder = ['m851']

def getFirmwareProfile(fn, container):
	cfg = configparser.ConfigParser()

	if not cfg.read(fn):
		return False, "Firmware profile settings file %s does not exist." % fn

	section = "Firmware"
	if not cfg.has_section(section):
		return False, "Firmware profile file %s does not have %s section." % (fn, section)

	for g in grporder:
		for i in grpinfo[g][2]:
			k = "%s_%s" % (g, i)
			if not cfg.has_option(section, k):
				v = None
			else:
				v = str(cfg.get(section, k))

			container.setValue(k, v)
			
	if container.hasZProbe:
		for g in zprobeorder:
			for i in zprobeinfo[g][2]:
				k = "%s_%s" % (g, i)
				if not cfg.has_option(section, k):
					v = None
				else:
					v = str(cfg.get(section, k))

				container.setValue(k, v)
   	
	return True, "Firmware profile file %s successfully read" % fn


def putFirmwareProfile(fn, container):
	cfg = configparser.ConfigParser()

	section = "Firmware"
	cfg.add_section(section)
	for g in grporder:
		for i in grpinfo[g][2]:
			k = "%s_%s" % (g, i)
			v = container.getValue(k)
			if v is not None:
				cfg.set(section, k, str(v))
			else:
				try:
					cfg.remove_option(section, k)
				except:
					pass
	if container.hasZProbe:
		for g in zprobeorder:
			for i in zprobeinfo[g][2]:
				k = "%s_%s" % (g, i)
				v = container.getValue(k)
				if v is not None:
					cfg.set(section, k, str(v))
				else:
					try:
						cfg.remove_option(section, k)
					except:
						pass

	try:
		with open(fn, "w") as configfile:
			cfg.write(configfile)
	except:
		return False, "Error saving firmware profile to %s" % fn

	return True, "Firmware profile successfully saved to %s" % fn


class TextBox(wx.Window):
	def __init__(self, parent, text, size=wx.DefaultSize):
		wx.Window.__init__(self, parent, -1,
							 #style=wx.RAISED_BORDER
							 #style=wx.SUNKEN_BORDER
							 style=wx.SIMPLE_BORDER
							 )
		self.text = str(text)
		if size != wx.DefaultSize:
			self.bestsize = size
		else:
			self.bestsize = (250,25)
		self.SetSize(self.GetBestSize())

		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_SIZE, self.OnSize)

	def setText(self, text):
		self.text = "" if text is None else str(text)
		self.Refresh()

	def getText(self):
		return self.text

	def OnPaint(self, evt):
		sz = self.GetSize()
		dc = wx.PaintDC(self)
		w,h = dc.GetTextExtent(self.text)
		dc.Clear()
		dc.DrawText(self.text, (sz.width-w)/2, (sz.height-h)/2)

	def OnSize(self, evt):
		self.Refresh()

	def DoGetBestSize(self):
		return self.bestsize


BSIZE = (140, 40)


class FirmwareDlg(wx.Frame):
	def __init__(self, parent, server, pname, flash, cbexit):
		wx.Frame.__init__(self, None, wx.ID_ANY, "%s Firmware Parameters" % pname,
						  pos=wx.DefaultPosition, size=(950, 780)) #, style=wx.DEFAULT_FRAME_STYLE)
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.server = server
		self.eeprom = FwSettings(self.parent.hasZProbe)
		self.flash = flash
		self.working = FwSettings(self.parent.hasZProbe)
		self.printerName = pname
		self.exitDlg = cbexit
		self.settings = self.parent.settings

		self.eepromFileName = "eeprom.%s.marlin" % pname
		rc, msg = getFirmwareProfile(self.eepromFileName, self.eeprom)
		self.parent.logMessage(msg)

		self.sizer = wx.GridBagSizer()

		row = 1
		btnBase = 5000
		grpBase = 6000
		self.itemMap = {}
		self.buttonMap = {}
		self.groupMap = {}

		font = wx.Font (12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

		t = wx.StaticText(self, wx.ID_ANY, "FLASH")
		t.SetFont(font)
		self.sizer.Add(t, pos=(0, 6), flag=wx.ALIGN_CENTER)

		t = wx.StaticText(self, wx.ID_ANY, "EEPROM")
		t.SetFont(font)
		self.sizer.Add(t, pos=(0, 7), flag=wx.ALIGN_CENTER)

		t = wx.StaticText(self, wx.ID_ANY, "  ", size=(20, -1))
		self.sizer.Add(t, pos=(0, 8), flag=wx.ALIGN_CENTER)
		grps = grporder
		if self.parent.hasZProbe:
			grps = grporder + zprobeorder

		for g in grps:
			try:
				item = grpinfo[g]
			except:
				item = zprobeinfo[g]
				
			t = TextBox(self, item[0])
			self.sizer.Add(t, pos=(row, 1), span=(item[1], 1), flag=wx.EXPAND)
			for i in range(item[1]):
				itemKey = g + '_' + item[2][i]

				t = TextBox(self, item[2][i] + ':', size=(20, 25))
				self.sizer.Add(t, pos=(row+i, 2), flag=wx.EXPAND)

				tv = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_CENTER, size=(140, 25))
				tv.SetFont(font)
				tv.SetToolTip(item[3][i])
				self.sizer.Add(tv, pos=(row+i, 3), flag=wx.EXPAND)

				b = wx.Button(self, btnBase+row+i, "-->")
				self.buttonMap[btnBase+row+i] = itemKey
				self.Bind(wx.EVT_BUTTON, self.onItemCopy, b)
				self.sizer.Add(b, pos=(row+i, 4), flag=wx.EXPAND)

				v = self.flash.getValue(itemKey)
				if v is None: v = ""
				tf = TextBox(self, v, size=(100, 25))
				self.sizer.Add(tf, pos=(row+i, 6), flag=wx.EXPAND)

				v = self.eeprom.getValue(itemKey)
				if v is None: v = ""
				te = TextBox(self, v, size=(100, 25))
				self.sizer.Add(te, pos=(row+i, 7), flag=wx.EXPAND)

				self.itemMap[itemKey] = [tv, tf, te]

			b = wx.Button(self, grpBase, "-->")
			self.groupMap[grpBase] = g
			self.Bind(wx.EVT_BUTTON, self.onGroupCopy, b)
			self.sizer.Add(b, pos=(row, 5), span=(item[1], 1), flag=wx.EXPAND)
			grpBase += 1

			row += item[1]

		btnSizer = wx.BoxSizer(wx.VERTICAL)

		btnSizer.AddSpacer(40)

		self.buttons = []
		btn = wx.Button(self, wx.ID_ANY, "Load Profile", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onLoadProf, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)

		btn = wx.Button(self, wx.ID_ANY, "Save Profile", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onSaveProf, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)

		btnSizer.AddSpacer(100)

		btn = wx.Button(self, wx.ID_ANY, "All -> FLASH", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onCopyAllToFlash, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)

		btn = wx.Button(self, wx.ID_ANY, "FLASH -> EEPROM", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onCopyFlashToEEProm, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)

		btn = wx.Button(self, wx.ID_ANY, "EEPROM -> FLASH", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onCopyEEPromToFlash, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)

		btn = wx.Button(self, wx.ID_ANY, "Flash -> Working", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onCopyFlashToWork, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)

		btnSizer.AddSpacer(80)

		btn = wx.Button(self, wx.ID_ANY, "Close", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onClose, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)

		self.sizer.Add(btnSizer, pos=(0,0), span=(row+2,1))

		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.SetSizer(self.sizer)
		self.SetAutoLayout(True)
		self.Fit()

	def enableButtons(self, flag):
		for b in self.buttons:
			b.Enable(flag)

	def onItemCopy(self, event):
		wid = event.GetId()
		if wid not in self.buttonMap.keys():
			return

		ik = self.buttonMap[wid]
		wVal = self.itemMap[ik][0]
		val = wVal.GetValue().strip()

		if val != "":
			cmd = "%s%s" % (ik.upper().replace('_', ' '), val)
			self.server.command(cmd)

			wFlash = self.itemMap[ik][1]
			wFlash.setText(val)
			self.flash.setValue(ik, val)

	def onGroupCopy(self, event):
		wid = event.GetId()
		if wid not in self.groupMap.keys():
			return

		gk = self.groupMap[wid]
		self.sendGroupToFlash(gk)

	def sendGroupToFlash(self, gk):
		cmd = gk.upper()
		nterms = 0
		try:
			item = grpinfo[gk]
		except:
			item = zprobeinfo[gk]
		for gi in item[2]:
			ik = gk + '_' + gi

			wVal = self.itemMap[ik][0]
			val = wVal.GetValue().strip()

			if val != "":
				nterms += 1
				cmd += " %s%s" % (gi.upper(), val)
				wFlash = self.itemMap[ik][1]
				wFlash.setText(val)
				self.flash.setValue(ik, val)

		if nterms != 0:
			self.server.command(cmd)

	def onCopyAllToFlash(self, evt):
		for g in grporder:
			self.sendGroupToFlash(g)
		if self.parent.hasZProbe:
			for g in zprobeorder:
				self.sendGroupToFlash(g)

	def onCopyFlashToEEProm(self, evt):
		self.server.command("M500")
		for i in self.itemMap.keys():
			v = self.itemMap[i][1].getText()
			self.itemMap[i][2].setText(v)
			self.eeprom.setValue(i, v)

		rc, msg = putFirmwareProfile(self.eepromFileName, self.eeprom)
		self.parent.logMessage(msg)

	def onCopyEEPromToFlash(self, evt):
		self.enableButtons(False)
		self.server.command("M501")
		self.parent.startFwCollection(self.eeprom, self.resumeAfterFwCollection)

	def resumeAfterFwCollection(self):
		for i in self.itemMap.keys():
			v = self.eeprom.getValue(i)
			self.itemMap[i][2].setText(v)
			self.itemMap[i][1].setText(v)
			self.flash.setValue(i, v)

		rc, msg = putFirmwareProfile(self.eepromFileName, self.eeprom)
		self.parent.logMessage(msg)
		self.enableButtons(True)

	def onCopyFlashToWork(self, evt):
		for i in self.itemMap.keys():
			v = self.itemMap[i][1].getText()
			self.itemMap[i][0].SetValue(v)
			self.working.setValue(i, v)

	def onLoadProf(self, event):
		dlg = wx.FileDialog(
			self, message="Choose a firmware file",
			defaultDir=self.settings.getSetting("lastFwDirectory", dftValue="."),
			defaultFile="",
			wildcard=wildcard,
			style=wx.FD_OPEN | wx.FD_CHANGE_DIR
			)

		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath().encode('ascii', 'ignore').decode("utf-8") 
			dpath = os.path.dirname(path)
			self.settings.setSetting("lastFwDirectory", dpath)

			rc, msg = getFirmwareProfile(path, self.working)
			if rc:
				for k in self.itemMap.keys():
					wVal = self.itemMap[k][0]
					val = self.working.getValue(k)
					if val is None: val = ""
					wVal.SetValue(val)
			self.parent.logMessage(msg)

		dlg.Destroy()

	def onSaveProf(self, event):
		dlg = wx.FileDialog(
			self, message="Save firmware profile as...",
			defaultDir=self.settings.getSetting("lastFwDirectory", dftValue="."),
			defaultFile="",
			wildcard=wildcard,
			style=wx.FD_SAVE | wx.FD_CHANGE_DIR | wx.FD_OVERWRITE_PROMPT
			)

		v = dlg.ShowModal()
		if v != wx.ID_OK:
			dlg.Destroy()
			return

		path = dlg.GetPath().encode('ascii', 'ignore').decode("utf-8") 
		dlg.Destroy()
		dpath = os.path.dirname(path)
		self.settings.setSetting("lastFwDirectory", dpath)

		ext = os.path.splitext(os.path.basename(path))[1]
		if ext == "":
			path += ".fw"

		rc, msg = putFirmwareProfile(path, self.working)
		self.parent.logMessage(msg)

	def onClose(self, event):
		self.exitDlg()





