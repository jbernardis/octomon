"""
Created on May 14, 2018

@author: Jeff
"""

import os
import wx
import wx.dataview
import time
from utils import approximateValue

class node:
	def __init__(self, path, origin, parent, leaf, downloadUrl, sz, dt):
		self.path = path
		self.origin = origin
		self.parent = parent
		self.leaf = leaf
		self.downloadUrl = downloadUrl
		self.size = sz
		self.date = dt
		self.itemId = None
		
	def setItemId(self, itemid):
		self.itemId = itemid
		
	def getItemId(self):
		return self.itemId

	def toString(self):
		return "%s %s %s %s %s %s %s" % (str(self.path), str(self.parent), str(self.origin), str(self.leaf), str(self.downloadUrl), str(self.size), str(self.date))


def mapHasPath(path, nl):
	for n in nl:
		if path == n.path:
			return True
	return False

treesize = (600, 200) if os.name == 'posix' else (450, 200)
treecol0 = 300        if os.name == 'posix' else 226
treecol1 = 100        if os.name == 'posix' else 80
treecol2 = 180        if os.name == 'posix' else 120

class FileDlg(wx.Frame):
	def __init__(self, parent, server, pname, cb):
		wx.Frame.__init__(self, None, wx.ID_ANY, "File List: %s" % pname)
		self.SetBackgroundColour("white")

		self.selectedItem = None

		self.parent = parent
		self.images = self.parent.images
		self.settings = self.parent.settings
		self.server = server
		self.cb = cb
		self.pname = pname
		self.item = None

		self.sortColumn = 0
		self.sortDescending = False
		self.dirList = {}

		self.Bind(wx.EVT_CLOSE, self.onClose)
		
		self.includeSd = self.settings.getSetting("filesd", dftValue=False)
		
		self.fmap = self.getFileMap()

		self.tree = wx.dataview.TreeListCtrl(self, wx.ID_ANY, size=treesize, style=wx.TR_HAS_BUTTONS)

		isz = (16, 16)
		il = wx.ImageList(isz[0], isz[1])
		self.fldridx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz))
		self.fldropenidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN, wx.ART_OTHER, isz))
		self.fileidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
		self.selectedidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_OTHER, isz))

		self.tree.SetImageList(il)
		self.il = il

		self.tree.AppendColumn("<file>")
		self.tree.AppendColumn("<size>")
		self.tree.AppendColumn("<date>")

		self.root = self.tree.InsertItem(self.tree.GetRootItem(), wx.dataview.TLI_FIRST, self.pname)

		self.tree.SetItemData(self.root, node("<root>", None, None, False, None, 0, 0))
		self.tree.SetItemImage(self.root, closed=self.fldridx, opened=self.fldropenidx)
		
		self.populateTree()

		self.tree.Expand(self.root)
		self.tree.Bind(wx.dataview.EVT_TREELIST_SELECTION_CHANGED, self.onTreeSelection)
		self.tree.Bind(wx.dataview.EVT_TREELIST_ITEM_ACTIVATED, self.onDoubleClick)

		self.bSelect = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPrinter, size=(48, 48))
		self.bSelect.SetToolTip("Select file for printing")
		self.Bind(wx.EVT_BUTTON, self.onBSelect, self.bSelect)
		self.bSelect.SetDefault()
		self.bSelect.Enable(False)

		self.cbDelete = wx.CheckBox(self, wx.ID_ANY, "Delete")
		self.cbDelete.SetToolTip("Enable Delete button")
		self.Bind(wx.EVT_CHECKBOX, self.onCbDelete, self.cbDelete)
		self.cbDelete.SetValue(False)
		self.cbDelete.Enable(False)

		self.bDelete = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDelete, size=(48, 48))
		self.bDelete.SetToolTip("Delete file")
		self.Bind(wx.EVT_BUTTON, self.onBDelete, self.bDelete)
		self.bDelete.Enable(False)

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
			self.DoExpandAll()
		
		self.cbIncludeSd = wx.CheckBox(self, wx.ID_ANY, "Include SD Files")
		self.cbIncludeSd.SetToolTip("Include files from SD card (if present)")
		self.cbIncludeSd.SetValue(self.includeSd)
		self.Bind(wx.EVT_CHECKBOX, self.onCbIncludeSd, self.cbIncludeSd)

		self.rbFile = wx.RadioButton(self, wx.ID_ANY, " File name", style=wx.RB_GROUP)
		self.rbSize = wx.RadioButton(self, wx.ID_ANY, " Size")
		self.rbDate = wx.RadioButton(self, wx.ID_ANY, " Date")
		self.rbFile.SetValue(True)
		self.Bind(wx.EVT_RADIOBUTTON, self.onRbFile, self.rbFile)
		self.Bind(wx.EVT_RADIOBUTTON, self.onRbSize, self.rbSize)
		self.Bind(wx.EVT_RADIOBUTTON, self.onRbDate, self.rbDate)

		self.cbSortDescending = wx.CheckBox(self, wx.ID_ANY, "Sort Descending")
		self.cbSortDescending.SetValue(False)
		self.Bind(wx.EVT_CHECKBOX, self.onCbSortDescending, self.cbSortDescending)

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		sz = wx.BoxSizer(wx.VERTICAL)
		sz.Add(self.tree)
		sz.AddSpacer(20)
		
		osz = wx.BoxSizer(wx.HORIZONTAL)
		oszv = wx.BoxSizer(wx.VERTICAL)
		oszv.AddSpacer(20)
		oszv.Add(self.cbExpandAll)
		oszv.AddSpacer(10)
		oszv.Add(self.cbIncludeSd)
		osz.Add(oszv)

		osz.AddSpacer(40)

		box = wx.StaticBox(self, wx.ID_ANY, " Sort ")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		bsizer.AddSpacer(5)
		bsizer.Add(self.rbFile, 1, wx.ALL, 5)
		bsizer.Add(self.rbSize, 1, wx.ALL, 5)
		bsizer.Add(self.rbDate, 1, wx.ALL, 5)
		bsizer.AddSpacer(10)
		bsizer.Add(self.cbSortDescending)
		bsizer.AddSpacer(10)

		osz.Add(bsizer)

		sz.Add(osz, 1, wx.ALIGN_CENTER, 0)
		sz.AddSpacer(10)
		
		bsz = wx.BoxSizer(wx.HORIZONTAL)
		bsz.Add(self.bSelect)
		bsz.AddSpacer(10)
		bsz.Add(self.bDownload)
		bsz.AddSpacer(10)
		bsz.Add(self.cbDelete, 0, wx.ALIGN_CENTER_VERTICAL, 0)
		bsz.AddSpacer(3)
		bsz.Add(self.bDelete)
		bsz.AddSpacer(10)
		bsz.Add(self.bRefresh)
		sz.Add(bsz, 0, wx.ALIGN_CENTER, 0)
		sz.AddSpacer(10)

		hsz.AddSpacer(10)
		hsz.Add(sz)
		hsz.AddSpacer(10)

		self.SetSizer(hsz)
		self.Layout()
		self.Fit()

		self.Show()
		self.tree.SetColumnWidth(0, treecol0)
		self.tree.SetColumnWidth(1, treecol1)
		self.tree.SetColumnWidth(2, treecol2)


	def onRbFile(self, evt):
		self.sortColumn = 0
		self.rebuildTree()

	def onRbSize(self, evt):
		self.sortColumn = 1
		self.rebuildTree()

	def onRbDate(self, evt):
		self.sortColumn = 2
		self.rebuildTree()

	def onCbSortDescending(self, evt):
		self.sortDescending = self.cbSortDescending.GetValue()
		self.rebuildTree()

	def DoExpandAll(self):
		self.tree.Expand(self.root)
		for o in self.dirList.keys():
			for d in self.dirList[o]:
				self.tree.Expand(d)


	def DoCollapseAll(self):
		for o in self.dirList.keys():
			for d in self.dirList[o]:
				self.tree.Collapse(d)
		self.tree.Collapse(self.root)


	def getFileMap(self):
		fl = self.server.gfile.listFiles(local=True, sd=self.includeSd, recursive=True)
		try:
			fl = self.server.gfile.listFiles(local=True, sd=self.includeSd, recursive=True)
		except:
			dlg = wx.MessageDialog(self.parent, "Unable to get file listing from printer",
								   "Printer Error", wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()
			return {}

		if fl is None:
			dlg = wx.MessageDialog(self.parent, "Unable to get file listing from printer",
								   "Printer Error", wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()
			return {}

		fmap = {}
		for origin, ofl in fl.items():
			fmap[origin] = []
			for fn, dnurl, fsz, fdt in ofl:
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
						fmap[origin].append(node(path, origin, parent, path == fn, dnurl, fsz, fdt))
		return fmap

	def getSortKey(self, f):
		if self.sortColumn == 0:
			return f.path
		elif self.sortColumn == 1:
			return f.size
		elif self.sortColumn == 2:
			return f.date
		else:
			return f.path
		
	def populateTree(self):
		self.dirList = {}
		for origin in sorted(self.fmap.keys()):
			if origin == "sdcard" and not self.includeSd:
				continue
			
			nodeMap = {}
			dirs = []
			dirmap = {}
			for fl in self.fmap[origin]:
				fdir, fbn = os.path.split(fl.path)
				if fdir not in dirs:
					dirs.append(fdir)
					dirmap[fdir] = []

				dirmap[fdir].append(fl)

			for fdir in sorted(dirs):
				if fdir == "":
					originNode = self.tree.AppendItem(self.root, origin)
					nodeMap[origin] = originNode
					self.tree.SetItemData(originNode, node("<%s>" % origin, None, None, False, None, 0, 0))
					self.tree.SetItemImage(originNode, closed=self.fldridx, opened=self.fldropenidx)
				else:
					parentString = os.path.split(fdir)[0]
					if parentString == '':
						parentString = origin
					parentNode = nodeMap[parentString]
					nextNode = self.tree.AppendItem(parentNode, fdir)
					nodeMap[fdir] = nextNode

					self.tree.SetItemData(nextNode, node("<%s>" % fdir, None, None, False, None, 0, 0))
					self.tree.SetItemText(nextNode, 0, os.path.basename(fdir))
					self.tree.SetItemText(nextNode, 1, "")
					self.tree.SetItemText(nextNode, 2, "")
					self.tree.SetItemImage(nextNode, closed=self.fldridx, opened=self.fldropenidx)

			for fdir in sorted(dirs, reverse=self.sortDescending):
				for fl in sorted(dirmap[fdir], key=self.getSortKey, reverse=self.sortDescending):
					if not fl.leaf:
						continue

					parentNode = nodeMap[fl.parent]
					nextNode = self.tree.AppendItem(parentNode, fl.path)
					nodeMap[fl.path] = nextNode

					fl.setItemId(nextNode)
					self.tree.SetItemData(nextNode, fl)
					self.tree.SetItemText(nextNode, 0, os.path.basename(fl.path))

					if fl.size == 0:
						fsz = ""
					else:
						fsz = approximateValue(fl.size)
					if fl.date == 0:
						fdt = ""
					else:
						fdt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(fl.date))

					self.tree.SetItemText(nextNode, 1, fsz)
					self.tree.SetItemText(nextNode, 2, fdt)
					self.tree.SetItemImage(nextNode, closed=wx.NO_IMAGE, opened=wx.NO_IMAGE)
			dl = [nodeMap[x] for x in dirs if x != ""]
			self.dirList[origin] = [nodeMap[origin]] + dl


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

	def onBSelect(self, _):
		self.selectFile()
		
	def selectFile(self):
		if self.selectedItem:
			self.cb({"action": "select",
					 "origin": self.selectedItem.origin,
					 "path": self.selectedItem.path})

	def onCbDelete(self, _):
		if self.cbDelete.GetValue():
			self.bDelete.Enable(True)
		else:
			self.bDelete.Enable(False)

	def onBDelete(self, _):
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
				self.tree.SetItemImage(self.item, opened=wx.NO_IMAGE, closed=wx.NO_IMAGE)
				self.tree.DeleteItem(self.item)

				for origin in list(self.fmap.keys()):
					for fx in range(len(self.fmap[origin])):
						fl = self.fmap[origin][fx]
						if self.item == fl.getItemId():
							del self.fmap[origin][fx]
							break
						
				self.item = None
				self.selectedItem = None
				#self.tree.ClearFocusedItem()
				self.enableControls(False, False)

	def onBDownload(self, _):
		if self.selectedItem:
			self.cb({"action": "download",
					 "origin": self.selectedItem.origin,
					 "path": self.selectedItem.path,
					 "url": self.selectedItem.downloadUrl})
			
	def onBRefresh(self, _):
		self.fmap = self.getFileMap()

		self.rebuildTree()

	def rebuildTree(self):
		self.tree.DeleteAllItems()
		self.root = self.tree.InsertItem(self.tree.GetRootItem(), wx.dataview.TLI_FIRST, self.pname)
		self.tree.SetItemData(self.root, None)
		self.tree.SetItemImage(self.root, closed=self.fldridx, opened=self.fldropenidx)
		self.populateTree()
		self.item = None
		self.selectedItem = None
		self.enableControls(False, False)
		if self.expandAll:
			self.DoExpandAll()
		else:
			self.DoCollapseAll()
			self.tree.Expand(self.root)

	def onCbExpandAll(self, _):
		self.expandAll = self.cbExpandAll.GetValue()
		self.settings.setSetting("fileexpandall", str(self.expandAll))
		if self.expandAll:
			self.DoExpandAll()
		else:
			self.DoCollapseAll()
			self.tree.Expand(self.root)
			
	def onCbIncludeSd(self, _):
		self.includeSd = self.cbIncludeSd.GetValue()
		self.settings.setSetting("filesd", str(self.includeSd))
		self.fmap = self.getFileMap()

		self.rebuildTree()

	def onTreeSelection(self, evt):
		oldItem = self.item
		self.item = evt.GetItem()
		if not self.item:
			self.enableControls(False, False)
			return

		itemData = self.tree.GetItemData(self.item)
		isAFile = not (itemData is None or not itemData.leaf)
		isDownloadable = not (itemData is None or not itemData.downloadUrl)
		self.enableControls(isAFile, isDownloadable)

		if isAFile:
			if oldItem:
				self.tree.SetItemImage(oldItem, opened=wx.NO_IMAGE, closed=wx.NO_IMAGE)
			self.tree.SetItemImage(self.item, opened=self.selectedidx, closed=self.selectedidx)
			self.selectedItem = itemData
		else:
			self.selectedItem = None
			
	def onDoubleClick(self, _):
		self.selectFile()

	def onClose(self, _):
		self.cb({})
