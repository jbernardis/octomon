"""
Created on May 4, 2018

@author: Jeff
"""
import wx

BTNDIM = (48, 48)
IPSIZE = (240, -1)

class OctolapseDlg(wx.Dialog):
	def __init__(self, parent, pname, piserver, picfg):
		try:
			v = " (" + picfg["version"] + ")"
		except IndexError:
			v = ""
		wx.Dialog.__init__(self, None, wx.ID_ANY, "%s OctoLapse %s Configuration" % (pname, v))
		self.SetBackgroundColour("white")
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.images = parent.images
		self.server = piserver
		self.config = picfg

		self.origEnabled = picfg["is_octolapse_enabled"]	

		sz = wx.BoxSizer(wx.HORIZONTAL)
		sz.AddSpacer(10)

		vsz = wx.BoxSizer(wx.VERTICAL)
		vsz.AddSpacer(20)
		
		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(320)
		
		self.cbEnabled = wx.CheckBox(self, wx.ID_ANY, " OctoLapse Enabled")
		self.cbEnabled.SetValue(self.origEnabled)
		hsz.Add(self.cbEnabled)
		vsz.Add(hsz)
		vsz.AddSpacer(20)
		
		box = wx.StaticBox(self, wx.ID_ANY, " Printer ")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		
		self.printerNameList = [p["name"] for p in picfg["printers"]]
		self.printerDescList = [p["description"] for p in picfg["printers"]]
		self.printerGUIDList = [p["guid"] for p in picfg["printers"]]
		
		self.origPrinterGuid = picfg["current_printer_profile_guid"]
		self.currentPrinterGuid = self.origPrinterGuid
		try:
			v = self.printerGUIDList.index(self.currentPrinterGuid)
			descr = self.printerDescList[v]
		except IndexError:
			v = 0
			descr = ""
		
		self.chPrinters = wx.Choice(self, wx.ID_ANY, choices=self.printerNameList, size=(500, -1)) 
		bsizer.Add(self.chPrinters)
		self.chPrinters.SetSelection(v)
		self.Bind(wx.EVT_CHOICE, self.onChPrinters, self.chPrinters)
		
		bsizer.AddSpacer(5)
		
		self.stPrinters = wx.StaticText(self, wx.ID_ANY, descr, size=(500, 1))
		bsizer.Add(self.stPrinters)
		bsizer.AddSpacer(5)
		
		vsz.Add(bsizer)
		vsz.AddSpacer(10)
		
		box = wx.StaticBox(self, wx.ID_ANY, " Rendering ")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		
		self.renderingNameList = [p["name"] for p in picfg["renderings"]]
		self.renderingDescList = [p["description"] for p in picfg["renderings"]]
		self.renderingGUIDList = [p["guid"] for p in picfg["renderings"]]
		
		self.origRenderingGuid = picfg["current_rendering_profile_guid"]
		self.currentRenderingGuid = self.origRenderingGuid
		try:
			v = self.renderingGUIDList.index(self.currentRenderingGuid)
			descr = self.renderingDescList[v]
		except IndexError:
			v = 0
			descr = ""

		self.chRenderings = wx.Choice(self, wx.ID_ANY, choices=self.renderingNameList, size=(500, -1)) 
		bsizer.Add(self.chRenderings)
		self.chRenderings.SetSelection(v)
		self.Bind(wx.EVT_CHOICE, self.onChRenderings, self.chRenderings)
		
		bsizer.AddSpacer(5)
		
		self.stRenderings = wx.StaticText(self, wx.ID_ANY, descr, size=(500, -1))
		bsizer.Add(self.stRenderings)
		bsizer.AddSpacer(5)
		
		vsz.Add(bsizer)
		vsz.AddSpacer(10)
		
		box = wx.StaticBox(self, wx.ID_ANY, " Snapshots ")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		
		self.snapshotsNameList = [p["name"] for p in picfg["snapshots"]]
		self.snapshotsDescList = [p["description"] for p in picfg["snapshots"]]
		self.snapshotsGUIDList = [p["guid"] for p in picfg["snapshots"]]
		
		self.origSnapshotGuid = picfg["current_snapshot_profile_guid"]
		self.currentSnapshotGuid = self.origSnapshotGuid
		try:
			v = self.snapshotsGUIDList.index(self.currentSnapshotGuid)
			descr = self.snapshotsDescList[v]
		except IndexError:
			v = 0
			descr = ""
		
		self.chSnapshots = wx.Choice(self, wx.ID_ANY, choices=self.snapshotsNameList, size=(500, -1)) 
		bsizer.Add(self.chSnapshots)
		self.chSnapshots.SetSelection(v)
		self.Bind(wx.EVT_CHOICE, self.onChSnapshots, self.chSnapshots)
		
		bsizer.AddSpacer(5)
		
		self.stSnapshots = wx.StaticText(self, wx.ID_ANY, descr, size=(500, -1))
		bsizer.Add(self.stSnapshots)
		bsizer.AddSpacer(5)
		
		vsz.Add(bsizer)
		vsz.AddSpacer(10)
		
		box = wx.StaticBox(self, wx.ID_ANY, " Stabilizations ")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		
		self.stabilizationsNameList = [p["name"] for p in picfg["stabilizations"]]
		self.stabilizationsDescList = [p["description"] for p in picfg["stabilizations"]]
		self.stabilizationsGUIDList = [p["guid"] for p in picfg["stabilizations"]]
		
		self.origStabilizationGuid = picfg["current_stabilization_profile_guid"]
		self.currentStabilizationGuid = self.origStabilizationGuid
		try:
			v = self.stabilizationsGUIDList.index(self.currentStabilizationGuid)
			descr = self.stabilizationsDescList[v]
		except IndexError:
			v = 0
			descr = ""
		
		self.chStabilizations = wx.Choice(self, wx.ID_ANY, choices=self.stabilizationsNameList, size=(500, -1)) 
		bsizer.Add(self.chStabilizations)
		self.chStabilizations.SetSelection(v)
		self.Bind(wx.EVT_CHOICE, self.onChStabilizations, self.chStabilizations)
		
		bsizer.AddSpacer(5)
		
		self.stStabilizations = wx.StaticText(self, wx.ID_ANY, descr, size=(500, -1))
		bsizer.Add(self.stStabilizations)
		bsizer.AddSpacer(5)
		
		vsz.Add(bsizer)
		
		self.origShowExtruderStateChanges = picfg["show_extruder_state_changes"]
		self.cbShowExtruderStateChanges = wx.CheckBox(self, wx.ID_ANY, " Show Extruder state changes", size=IPSIZE)
		self.cbShowExtruderStateChanges.SetValue(self.origShowExtruderStateChanges)
		
		self.origShowPositionChanges = picfg["show_position_changes"]
		self.cbShowPositionChanges = wx.CheckBox(self, wx.ID_ANY, " Show Position changes", size=IPSIZE)
		self.cbShowPositionChanges.SetValue(self.origShowPositionChanges)

		self.origShowPositionStateChanges = picfg["show_position_state_changes"]
		self.cbShowPositionStateChanges = wx.CheckBox(self, wx.ID_ANY, " Show Position state changes", size=IPSIZE)
		self.cbShowPositionStateChanges.SetValue(self.origShowPositionStateChanges)
		
		self.origShowTriggerStateChanges = picfg["show_trigger_state_changes"]
		self.cbShowTriggerStateChanges = wx.CheckBox(self, wx.ID_ANY, " Show Trigger state changes", size=IPSIZE)
		self.cbShowTriggerStateChanges.SetValue(self.origShowTriggerStateChanges)

		box = wx.StaticBox(self, wx.ID_ANY, " Information Panel ")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		
		bsizer.AddSpacer(5)
		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(20)
		hsz.Add(self.cbShowExtruderStateChanges)
		hsz.Add(self.cbShowPositionChanges)
		bsizer.Add(hsz)
		
		bsizer.AddSpacer(5)
		hsz = wx.BoxSizer(wx.HORIZONTAL)
		hsz.AddSpacer(20)
		hsz.Add(self.cbShowPositionStateChanges)
		hsz.Add(self.cbShowTriggerStateChanges)
		bsizer.Add(hsz)
		
		bsizer.AddSpacer(5)
		vsz.AddSpacer(10)
		vsz.Add(bsizer, 1, wx.EXPAND)

		bsz = wx.BoxSizer(wx.HORIZONTAL)
		bsz.AddSpacer(10)

		b = wx.BitmapButton(self, wx.ID_ANY, self.images.pngOk, size=BTNDIM)
		b.SetToolTip("Exit Dialog")
		self.Bind(wx.EVT_BUTTON, self.onBOK, b)
		bsz.Add(b)
		bsz.AddSpacer(10)
		
		b = wx.BitmapButton(self, wx.ID_ANY, self.images.pngCancel, size=BTNDIM)
		b.SetToolTip("Cancel")
		self.Bind(wx.EVT_BUTTON, self.onClose, b)
		bsz.Add(b)
		bsz.AddSpacer(10)
		
		vsz.AddSpacer(10)
		vsz.Add(bsz, 0, wx.ALIGN_CENTER_HORIZONTAL)
		vsz.AddSpacer(10)

		sz.Add(vsz)
		sz.AddSpacer(10)

		self.SetSizer(sz)
		self.Fit()

	def onChPrinters(self, _):
		v = self.chPrinters.GetSelection()
		if v == wx.NOT_FOUND:
			return 
		
		self.stPrinters.SetLabel(self.printerDescList[v])
		self.currentPrinterGuid = self.printerGUIDList[v]

	def onChRenderings(self, _):
		v = self.chRenderings.GetSelection()
		if v == wx.NOT_FOUND:
			return 
		
		self.stRenderings.SetLabel(self.renderingDescList[v])
		self.currentRenderingGuid = self.renderingGUIDList[v]

	def onChSnapshots(self, _):
		v = self.chSnapshots.GetSelection()
		if v == wx.NOT_FOUND:
			return 
		
		self.stSnapshots.SetLabel(self.snapshotsDescList[v])
		self.currentSnapshotGuid = self.snapshotsGUIDList[v]

	def onChStabilizations(self, _):
		v = self.chStabilizations.GetSelection()
		if v == wx.NOT_FOUND:
			return 
		
		self.stStabilizations.SetLabel(self.stabilizationsDescList[v])
		self.currentStabilizationGuid = self.stabilizationsGUIDList[v]
		
	def onBOK(self, _):
		self.EndModal(wx.ID_OK)

	def onClose(self, _):
		if self.hasAnythingChanged():
			dlg = wx.MessageDialog(self, "Changes will be lost.  Exit anyway?",
										   "Lose Changes?", wx.OK | wx.CANCEL | wx.ICON_WARNING)
			rc = dlg.ShowModal()
			dlg.Destroy()
			if rc != wx.ID_OK:
				return

		self.EndModal(wx.ID_CANCEL)
		
	def hasAnythingChanged(self):
		if self.hasEnabledStatusChanged():
			return True
		if self.hasPrinterProfileChanged():
			return True
		if self.hasRenderingProfileChanged():
			return True
		if self.hasSnapshotProfileChanged():
			return True
		if self.hasStabilizationProfileChanged():
			return True
		
		return False
		
	def hasEnabledStatusChanged(self):
		cur = self.cbEnabled.GetValue()
		if self.origEnabled == cur:
			return None
		else:
			return cur
		
	def hasPrinterProfileChanged(self):
		if self.origPrinterGuid == self.currentPrinterGuid:
			return None
		else:
			return self.currentPrinterGuid
		
	def hasRenderingProfileChanged(self):
		if self.origRenderingGuid == self.currentRenderingGuid:
			return None
		else:
			return self.currentRenderingGuid
		
	def hasSnapshotProfileChanged(self):
		if self.origSnapshotGuid == self.currentSnapshotGuid:
			return None
		else:
			return self.currentSnapshotGuid
		
	def hasStabilizationProfileChanged(self):
		if self.origStabilizationGuid == self.currentStabilizationGuid:
			return None
		else:
			return self.currentStabilizationGuid		
		
	def hasShowExtruderStateChanged(self):
		cur = self.cbShowExtruderStateChanges.GetValue()
		if self.origShowExtruderStateChanges == cur:
			return None
		else:
			return cur
		
	def hasShowPositionChanged(self):
		cur = self.cbShowPositionChanges.GetValue()
		if self.origShowPositionChanges == cur:
			return None
		else:
			return cur
		
	def hasShowPositionStateChanged(self):
		cur = self.cbShowPositionStateChanges.GetValue()
		if self.origShowPositionStateChanges == cur:
			return None
		else:
			return cur
		
	def hasShowTriggerStateChanged(self):
		cur = self.cbShowTriggerStateChanges.GetValue()
		if self.origShowTriggerStateChanges == cur:
			return None
		else:
			return cur

