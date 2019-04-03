import wx

BUTTONDIM = (48, 48)


class UploadDestinationDlg(wx.Dialog):
    def __init__(self, parent, pname, ps, dname):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Upload to %s" % pname)

        self.parent = parent
        self.ps = ps
        self.pname = pname

        self.fn = dname

        sizer = wx.BoxSizer(wx.VERTICAL)
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)

        fl = ps.gfile.listFiles()
        if fl is None:
            wx.CallAfter(self.notConnected)
            return

        flist = [x[0] for x in fl['local']]
        self.ch = wx.Choice(self, wx.ID_ANY, choices=["<none>"] + sorted(flist), size=(300, -1))
        self.ch.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.onChoice, self.ch)

        self.entry = wx.TextCtrl(self, wx.ID_ANY, "%s" % self.fn, size=(300, -1))

        sizer.AddSpacer(20)
        sizer.Add(wx.StaticText(self, wx.ID_ANY, "Choose an existing file:"),
                  0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.LEFT, 10)
        sizer.Add(self.ch, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL | wx.LEFT | wx.RIGHT, 10)
        sizer.AddSpacer(20)
        sizer.Add(wx.StaticText(self, wx.ID_ANY, "Or enter a new name:"),
                  0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.LEFT, 10)
        sizer.Add(self.entry, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL | wx.LEFT | wx.RIGHT, 10)
        sizer.AddSpacer(20)

        btn = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngOk, size=BUTTONDIM)
        btn.SetToolTip("Upload")
        btnsizer.Add(btn)
        self.Bind(wx.EVT_BUTTON, self.onOk, btn)

        btnsizer.AddSpacer(30)

        btn = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngCancel, size=BUTTONDIM)
        btn.SetToolTip("Cancel Upload")
        btnsizer.Add(btn)
        self.Bind(wx.EVT_BUTTON, self.onCancel, btn)

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        sizer.AddSpacer(20)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def notConnected(self):
        dlg = wx.MessageDialog(self, "Unable to connect to %s" % self.pname,
                               "Unable to connect", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

        self.EndModal(wx.ID_CANCEL)

    def getFn(self):
        fn = self.entry.GetValue()
        if not fn.endswith(".gcode"):
            fn += ".gcode"

        return fn

    def onChoice(self, _):
        idx = self.ch.GetSelection()
        if idx == wx.NOT_FOUND or idx == 0:
            self.entry.SetValue(self.fn)
        else:
            self.entry.SetValue(self.ch.GetString(idx))

    def onOk(self, _):
        self.EndModal(wx.ID_OK)

    def onCancel(self, _):
        self.EndModal(wx.ID_CANCEL)
