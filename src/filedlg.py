"""
Created on May 14, 2018

@author: Jeff
"""

import wx

class node:
	def __init__(self, path, origin, parent, leaf, downloadUrl):
		self.path = path
		self.origin = origin
		self.parent = parent
		self.leaf = leaf
		self.downloadUrl = downloadUrl
		self.itemId = None
		
	def setItemId(self, itemid):
		self.itemId = itemid
		
	def getItemId(self):
		return self.itemId


def mapHasPath(path, nl):
	for n in nl:
		if path == n.path:
			return True
	return False


class FileDlg(wx.Frame):
	def __init__(self, parent, server, pname, cb):
		wx.Frame.__init__(self, None, wx.ID_ANY, "File List: %s" % pname)
		self.SetBackgroundColour("white")

		self.selectedItem = None

		self.parent = parent
		self.images = self.parent.images
		self.settings = self.parent.settings
		self.server = self.parent.server
		self.cb = cb

		self.Bind(wx.EVT_CLOSE, self.onClose)
		
		self.includeSd = self.settings.getSetting("filesd", dftValue=False)
		
		self.fmap = self.getFileMap()

		self.tree = wx.TreeCtrl(self, wx.ID_ANY, size=(300, 200), style=wx.TR_HAS_BUTTONS)

		isz = (16, 16)
		il = wx.ImageList(isz[0], isz[1])
		self.fldridx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz))
		self.fldropenidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN, wx.ART_OTHER, isz))
		self.fileidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
		self.selectedidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_OTHER, isz))

		self.tree.SetImageList(il)
		self.il = il

		self.root = self.tree.AddRoot(pname)
		self.tree.SetItemData(self.root, None)
		self.tree.SetItemImage(self.root, self.fldridx, wx.TreeItemIcon_Normal)
		self.tree.SetItemImage(self.root, self.fldropenidx, wx.TreeItemIcon_Expanded)
		
		self.populateTree()
		

		self.tree.Expand(self.root)
		self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onTreeSelection, self.tree)

		self.bSelect = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSelect, size=(48, 48))
		self.bSelect.SetToolTip("Select file for printing")
		self.Bind(wx.EVT_BUTTON, self.onBSelect, self.bSelect)

		self.cbDelete = wx.CheckBox(self, wx.ID_ANY, "Delete")
		self.cbDelete.SetToolTip("Enable Delete button")
		self.Bind(wx.EVT_CHECKBOX, self.onCbDelete, self.cbDelete)
		self.cbDelete.SetValue(False)

		self.bDelete = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDelete, size=(48, 48))
		self.bDelete.SetToolTip("Delete file")
		self.Bind(wx.EVT_BUTTON, self.onBDelete, self.bDelete)

		self.bDownload = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDownload, size=(48, 48))
		self.bDownload.SetToolTip("Download file")
		self.Bind(wx.EVT_BUTTON, self.onBDownload, self.bDownload)

		self.bRefresh = wx.BitmapButton(self, wx.ID_ANY, self.images.pngRefresh, size=(48, 48))
		self.bRefresh.SetToolTip("Refresh file list")
		self.Bind(wx.EVT_BUTTON, self.onBRefresh, self.bRefresh)
		
		self.expandAll = self.settings.getSetting("fileexpandall", dftValue=True)
		self.cbExpandAll = wx.CheckBox(self, wx.ID_ANY, "Expand all")
		self.cbExpandAll.SetToolTip("Expand all branches of the tree")
		self.cbExpandAll.SetValue(self.expandAll)
		self.Bind(wx.EVT_CHECKBOX, self.onCbExpandAll, self.cbExpandAll)
		if self.expandAll:
			self.tree.ExpandAll()
		
		self.cbIncludeSd = wx.CheckBox(self, wx.ID_ANY, "Include SD Files")
		self.cbIncludeSd.SetToolTip("Include files from SD card (if present)")
		self.cbIncludeSd.SetValue(self.includeSd)
		self.Bind(wx.EVT_CHECKBOX, self.onCbIncludeSd, self.cbIncludeSd)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		sz = wx.BoxSizer(wx.VERTICAL)
		sz.Add(self.tree)
		sz.AddSpacer(5)
		
		osz = wx.BoxSizer(wx.HORIZONTAL)
		osz.Add(self.cbExpandAll)
		osz.AddSpacer(10)
		osz.Add(self.cbIncludeSd)
		sz.Add(osz, 1, wx.ALIGN_CENTER_HORIZONTAL, 0)
		
		bsz = wx.BoxSizer(wx.HORIZONTAL)
		bsz.Add(self.bSelect)
		bsz.AddSpacer(10)
		bsz.Add(self.bDownload)
		bsz.AddSpacer(10)
		bsz.Add(self.cbDelete, 1, wx.ALIGN_CENTER_VERTICAL, 0)
		bsz.AddSpacer(3)
		bsz.Add(self.bDelete)
		bsz.AddSpacer(10)
		bsz.Add(self.bRefresh)
		sz.Add(bsz, 1, wx.ALIGN_CENTER, 0)
		sz.AddSpacer(10)

		hsz.AddSpacer(10)
		hsz.Add(sz)
		hsz.AddSpacer(10)

		self.SetSizer(hsz)
		self.Layout()
		self.Fit()

		self.Show()

	def getFileMap(self):
		try:
			fl = self.server.gfile.listFiles(local=True, sd=self.includeSd, recursive=True)
		except:
			dlg = wx.MessageDialog(self.parent, "Unable to get file listing from printer",
								   "Printer Error", wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()
			return {}

		fmap = {}
		for origin, ofl in fl.items():
			fmap[origin] = []
			for fn, dnurl in ofl:
				pl = fn.split("/")
				path = None
				for p in pl:
					if path is None:
						parent = origin
						path = p
					else:
						parent = path
						path = path + "/" + p
					if not mapHasPath(path, fmap[origin]):
						fmap[origin].append(node(path, origin, parent, path == fn, dnurl))
		return fmap
		
	def populateTree(self):
		for origin in sorted(self.fmap.keys()):
			if origin == "sdcard" and not self.includeSd:
				continue
			
			nodeMap = {}
			originNode = self.tree.AppendItem(self.root, origin)
			nodeMap[origin] = originNode
			self.tree.SetItemData(originNode, None)
			self.tree.SetItemImage(originNode, self.fldridx, wx.TreeItemIcon_Normal)
			self.tree.SetItemImage(originNode, self.fldropenidx, wx.TreeItemIcon_Expanded)

			for fl in sorted(self.fmap[origin], key=lambda x: x.path):
				parentNode = nodeMap[fl.parent]
				nextNode = self.tree.AppendItem(parentNode, fl.path)
				nodeMap[fl.path] = nextNode
				fl.setItemId(nextNode)
				self.tree.SetItemData(nextNode, fl)
				if fl.leaf:
					self.tree.SetItemImage(nextNode, self.fileidx, wx.TreeItemIcon_Normal)
					self.tree.SetItemImage(nextNode, self.fileidx, wx.TreeItemIcon_Expanded)
					self.tree.SetItemImage(nextNode, self.selectedidx, wx.TreeItemIcon_Selected)
					self.tree.SetItemImage(nextNode, self.selectedidx, wx.TreeItemIcon_SelectedExpanded)
				else:
					self.tree.SetItemImage(nextNode, self.fldridx, wx.TreeItemIcon_Normal)
					self.tree.SetItemImage(nextNode, self.fldropenidx, wx.TreeItemIcon_Expanded)


	def enableControls(self, isAFile, isDownloadable):
		if isAFile:
			self.bSelect.Enable(True)
			self.bDelete.Enable(False)
			self.cbDelete.Enable(True)
			self.cbDelete.SetValue(False)
			self.bDownload.Enable(isDownloadable)
		else:
			self.bSelect.Enable(False)
			self.bDelete.Enable(False)
			self.cbDelete.Enable(False)
			self.bDownload.Enable(False)

	def onBSelect(self, evt):
		if self.selectedItem:
			self.cb({"action": "select",
					 "origin": self.selectedItem.origin,
					 "path": self.selectedItem.path})

	def onCbDelete(self, evt):
		if self.cbDelete.GetValue():
			self.bDelete.Enable(True)
		else:
			self.bDelete.Enable(False)

	def onBDelete(self, evt):
		if self.selectedItem:
			try:
				rc = self.server.gfile.deleteFile(self.selectedItem.origin, self.selectedItem.path)
			except:
				dlg = wx.MessageDialog(self, "Unknown error during file delete",
									   "Delete Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
				return
			if rc >= 400:
				dlg = wx.MessageDialog(self, "Error %d during file delete" % rc,
								   "Delete Error", wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
				return
			
			if self.item:
				self.tree.Delete(self.item)

				for origin in list(self.fmap.keys()):
					for fx in range(len(self.fmap[origin])):
						fl = self.fmap[origin][fx]
						if self.item == fl.getItemId():
							del self.fmap[origin][fx]
							break
						
				self.item = None
				self.selectedItem = None
				self.tree.ClearFocusedItem()
				self.enableControls(False, False)

	def onBDownload(self, evt):
		if self.selectedItem:
			self.cb({"action": "download",
					 "origin": self.selectedItem.origin,
					 "path": self.selectedItem.path,
					 "url": self.selectedItem.downloadUrl})
			
	def onBRefresh(self, evt):
		self.tree.DeleteChildren(self.root)
		self.getFileMap()
		self.populateTree()
		self.item = None
		self.selectedItem = None
		self.tree.ClearFocusedItem()
		self.enableControls(False, False)
		if self.expandAll:
			self.tree.ExpandAll()
		else:
			self.tree.CollapseAll()
			self.tree.Expand(self.root)
			
	def onCbExpandAll(self, evt):
		self.expandAll = self.cbExpandAll.GetValue()
		self.settings.setSetting("fileexpandall", str(self.expandAll))
		if self.expandAll:
			self.tree.ExpandAll()
		else:
			self.tree.CollapseAll()
			self.tree.Expand(self.root)
			
	def onCbIncludeSd(self, evt):
		self.includeSd = self.cbIncludeSd.GetValue()
		self.settings.setSetting("filesd", str(self.includeSd))
		
		self.tree.DeleteChildren(self.root)
		
		self.fmap = self.getFileMap()
		self.populateTree()
		self.item = None
		self.selectedItem = None
		self.tree.ClearFocusedItem()
		self.enableControls(False, False)
		if self.expandAll:
			self.tree.ExpandAll()

	def onTreeSelection(self, evt):
		self.item = evt.GetItem()
		if not self.item:
			self.enableControls(False, False)
			return

		itemData = self.tree.GetItemData(self.item)
		isAFile = not (itemData is None or not itemData.leaf)
		isDownloadable = not (itemData is None or not itemData.downloadUrl)
		self.enableControls(isAFile, isDownloadable)

		if isAFile:
			self.selectedItem = itemData
		else:
			self.selectedItem = None

	def onClose(self, evt):
		self.cb({})
