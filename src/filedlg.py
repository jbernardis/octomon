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


def mapHasPath(path, nl):
    for n in nl:
        if path == n.path:
            return True
    return False


class FileDlg(wx.Frame):
    def __init__(self, parent, server, pname, fl, cb):
        wx.Frame.__init__(self, None, wx.ID_ANY, "File List: %s" % pname)
        self.SetBackgroundColour("white")

        self.selectedItem = None

        self.parent = parent
        self.images = self.parent.images
        self.cb = cb

        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.fmap = {}
        for origin, ofl in fl.items():
            self.fmap[origin] = []
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
                    if not mapHasPath(path, self.fmap[origin]):
                        self.fmap[origin].append(node(path, origin, parent, path == fn, dnurl))

        self.tree = wx.TreeCtrl(self, wx.ID_ANY, size=(300, 200), style=wx.TR_HAS_BUTTONS)

        isz = (16, 16)
        il = wx.ImageList(isz[0], isz[1])
        fldridx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz))
        fldropenidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN, wx.ART_OTHER, isz))
        fileidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
        selectedidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_OTHER, isz))

        self.tree.SetImageList(il)
        self.il = il

        self.root = self.tree.AddRoot(pname)
        self.tree.SetItemData(self.root, None)
        self.tree.SetItemImage(self.root, fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, fldropenidx, wx.TreeItemIcon_Expanded)

        for origin in sorted(self.fmap.keys()):
            nodeMap = {}
            originNode = self.tree.AppendItem(self.root, origin)
            nodeMap[origin] = originNode
            self.tree.SetItemData(originNode, None)
            self.tree.SetItemImage(originNode, fldridx, wx.TreeItemIcon_Normal)
            self.tree.SetItemImage(originNode, fldropenidx, wx.TreeItemIcon_Expanded)

            for fl in sorted(self.fmap[origin], key=lambda x: x.path):
                parentNode = nodeMap[fl.parent]
                nextNode = self.tree.AppendItem(parentNode, fl.path)
                nodeMap[fl.path] = nextNode
                self.tree.SetItemData(nextNode, fl)
                if fl.leaf:
                    self.tree.SetItemImage(nextNode, fileidx, wx.TreeItemIcon_Normal)
                    self.tree.SetItemImage(nextNode, fileidx, wx.TreeItemIcon_Expanded)
                    self.tree.SetItemImage(nextNode, selectedidx, wx.TreeItemIcon_Selected)
                    self.tree.SetItemImage(nextNode, selectedidx, wx.TreeItemIcon_SelectedExpanded)
                else:
                    self.tree.SetItemImage(nextNode, fldridx, wx.TreeItemIcon_Normal)
                    self.tree.SetItemImage(nextNode, fldropenidx, wx.TreeItemIcon_Expanded)

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

        hsz = wx.BoxSizer(wx.HORIZONTAL)
        sz = wx.BoxSizer(wx.VERTICAL)
        sz.Add(self.tree)
        sz.AddSpacer(5)
        bsz = wx.BoxSizer(wx.HORIZONTAL)
        bsz.Add(self.bSelect)
        bsz.AddSpacer(20)
        bsz.Add(self.bDownload)
        bsz.AddSpacer(20)
        bsz.Add(self.bDelete)
        bsz.AddSpacer(3)
        bsz.Add(self.cbDelete, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        sz.Add(bsz, 1, wx.ALIGN_CENTER, 0)
        sz.AddSpacer(5)

        hsz.AddSpacer(10)
        hsz.Add(sz)
        hsz.AddSpacer(10)

        self.SetSizer(hsz)
        self.Layout()
        self.Fit()

        self.Show()

    def enableControls(self, isAFile, isDownloadable):
        if isAFile:
            self.bSelect.Enable(True)
            self.bDelete.Enable(False)
            self.cbDelete.Enable(True)
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
            self.cb({"action": "delete",
                     "origin": self.selectedItem.origin,
                     "path": self.selectedItem.path})

    def onBDownload(self, evt):
        if self.selectedItem:
            self.cb({"action": "download",
                     "origin": self.selectedItem.origin,
                     "path": self.selectedItem.path,
                     "url": self.selectedItem.downloadUrl})

    def onTreeSelection(self, evt):
        self.item = evt.GetItem()
        if not self.item:
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
