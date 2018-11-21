"""
Created on May 4, 2018

@author: Jeff
"""
import os
import wx

LOGLIMIT = 300

from macrolist import MacroList


class TerminalDlg(wx.Frame):
    def __init__(self, parent, server, pname, settings, images, cbexit):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Terminal Display for %s" % pname)
        self.SetBackgroundColour("white")
        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.parent = parent
        self.server = server
        self.pname = pname
        self.settings = settings
        self.images = images
        self.exitDlg = cbexit

        self.paused = False
        self.suppressTempRpt = False
        self.suppressTempProbe = False

        self.macroList = MacroList(pname)
        self.orderedMacroList = self.macroList.getOrderedList()

        sz = wx.BoxSizer(wx.VERTICAL)
        sz.AddSpacer(10)

        hsz = wx.BoxSizer(wx.HORIZONTAL)
        hsz.AddSpacer(10)

        szLeft = wx.BoxSizer(wx.VERTICAL)

        box = wx.StaticBox(self, wx.ID_ANY, " Log ")
        szLog = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.tcLog = wx.TextCtrl(self, wx.ID_ANY, "", size=(500, 400), style=wx.TE_MULTILINE+wx.TE_READONLY)
        szLog.Add(self.tcLog, 1, wx.ALL, 5)
        szLogCtrl = wx.BoxSizer(wx.HORIZONTAL)

        self.bClear = wx.BitmapButton(self, wx.ID_ANY, self.images.pngClearlog, size=(48,48))
        self.bClear.SetToolTip("Clear the log")
        self.Bind(wx.EVT_BUTTON, self.onBClear, self.bClear)
        szLogCtrl.Add(self.bClear, 0, wx.ALL, 5)

        self.bSave = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSavelog, size=(48,48))
        self.bSave.SetToolTip("Save the log to a file")
        self.Bind(wx.EVT_BUTTON, self.onBSave, self.bSave)
        szLogCtrl.Add(self.bSave, 0, wx.ALL, 5)

        szLogCtrl.AddSpacer(50)

        szFilters = wx.BoxSizer(wx.VERTICAL)
        szFilters.AddSpacer(4)

        self.cbPause = wx.CheckBox(self, wx.ID_ANY, "Pause logging")
        szFilters.Add(self.cbPause)
        self.cbPause.SetValue(self.paused)
        self.Bind(wx.EVT_CHECKBOX, self.onCbPause, self.cbPause)

        self.cbSuppressTempRpt = wx.CheckBox(self, wx.ID_ANY, "Suppress temperature reports")
        szFilters.Add(self.cbSuppressTempRpt, 0, wx.TOP, 4)
        self.cbSuppressTempRpt.SetValue(self.suppressTempRpt)
        self.Bind(wx.EVT_CHECKBOX, self.onCbSuppressTempRpt, self.cbSuppressTempRpt)

        self.cbSuppressTempProbe = wx.CheckBox(self, wx.ID_ANY, "Suppress temperature probes")
        szFilters.Add(self.cbSuppressTempProbe, 0, wx.TOP, 4)
        self.cbSuppressTempProbe.SetValue(self.suppressTempProbe)
        self.Bind(wx.EVT_CHECKBOX, self.onCbSuppressTempProbe, self.cbSuppressTempProbe)

        szLogCtrl.Add(szFilters)
        szLog.Add(szLogCtrl, 0, wx.ALL|wx.EXPAND, 5)

        szLeft.Add(szLog)

        box = wx.StaticBox(self, wx.ID_ANY, " Manual Entry ")
        szMan = wx.StaticBoxSizer(box, wx.HORIZONTAL)

        szMan.AddSpacer(5)

        szV = wx.BoxSizer(wx.VERTICAL)

        self.tcMan = wx.TextCtrl(self, wx.ID_ANY, "", size=(250, -1), style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.onBSend, self.tcMan)
        szV.Add(self.tcMan)
        self.cbForceUpper = wx.CheckBox(self, wx.ID_ANY, "Force upper case")
        self.cbForceUpper.SetValue(True)
        szV.Add(self.cbForceUpper, 0, wx.ALIGN_CENTER)

        szMan.Add(szV, 0, wx.TOP, 10)

        szMan.AddSpacer(5)

        self.bSend = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSend, size=(48,48))
        self.bSend.SetToolTip("Send the command to the printer")
        self.Bind(wx.EVT_BUTTON, self.onBSend, self.bSend)
        szMan.Add(self.bSend, 0, wx.ALL, 5)

        self.bErase = wx.BitmapButton(self, wx.ID_ANY, self.images.pngClearlog, size=(48,48))
        self.bErase.SetToolTip("Clear the manual entry field")
        self.Bind(wx.EVT_BUTTON, self.onBErase, self.bErase)
        szMan.Add(self.bErase, 0, wx.ALL, 5)

        szLeft.Add(szMan, 0, wx.EXPAND)

        hsz.Add(szLeft)
        hsz.AddSpacer(10)

        if len(self.orderedMacroList) > 0:
            box = wx.StaticBox(self, wx.ID_ANY, " Macros ")
            szMacro = wx.StaticBoxSizer(box, wx.VERTICAL)

            self.macroMap = {}
            for m in self.orderedMacroList:
                mName = m.getName()
                b = wx.Button(self, wx.ID_ANY, mName, size=(120, -1))
                self.Bind(wx.EVT_BUTTON, self.onBMacro, b)
                szMacro.Add(b, 0, wx.ALL, 5)
                self.macroMap[mName] = m

            hsz.Add(szMacro, 0, wx.EXPAND)
            hsz.AddSpacer(10)

        sz.Add(hsz)
        sz.AddSpacer(10)

        self.SetSizer(sz)
        self.Fit()

    def logLine(self, l):
        if self.paused:
            return
        if self.suppressTempRpt and l.startswith("Recv:  T:"):
            return
        if self.suppressTempProbe:
            if l.startswith("Recv: ok T:"):
                return
            if l.startswith("Send: M105"):
                return

        self.tcLog.AppendText(l+"\n")
        t = self.tcLog.GetValue().split("\n")

        if len(t) > LOGLIMIT:
            t = t[-LOGLIMIT:]
            self.tcLog.SetValue("\n".join(t))
            self.tcLog.SetInsertionPointEnd()

    def logLines(self, ls):
        for l in ls:
            self.logLine(l)

    def onCbPause(self, evt):
        self.paused = self.cbPause.GetValue()

    def onBClear(self, evt):
        self.tcLog.Clear()

    def onBErase(self, evt):
        self.tcMan.Clear()

    def onBSend(self, evt):
        cmd = self.tcMan.GetValue()
        if self.cbForceUpper.IsChecked():
            cmd = cmd.upper()
        self.parent.logMessage("Sending command (%s)" % cmd)
        try:
            self.server.command(cmd)
        except:
            self.exitDlg()

    def onCbSuppressTempRpt(self, evt):
        self.suppressTempRpt = self.cbSuppressTempRpt.GetValue()

    def onCbSuppressTempProbe(self, evt):
        self.suppressTempProbe = self.cbSuppressTempProbe.GetValue()

    def onBSave(self, evt):
        wildcard = "Log File |*.log;*.LOG"
        dlg = wx.FileDialog(
            self, message="Save as ...",
            defaultDir=self.settings.getSetting("lastLogDirectory", dftValue="."),
            defaultFile="", wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)

        val = dlg.ShowModal()

        if val == wx.ID_OK:
            path = dlg.GetPath().encode('ascii', 'ignore').decode("utf-8") 
            dpath = os.path.dirname(path)
            self.settings.setSetting("lastLogDirectory", dpath)

            if self.tcLog.SaveFile(path):
                self.parent.logMessage("Log successfully saved to %s" % path)
            else:
                self.parent.logMessage("Save of log to %s failed" % path)

        dlg.Destroy()
        pass

    def onBMacro(self, evt):
        mName = evt.GetEventObject().GetLabel()
        if not mName in self.macroMap.keys():
            return

        self.parent.logMessage("Executing macro (%s)" % mName)
        mcl = self.macroMap[mName].getCommands()
        for mc in mcl:
            self.server.command(mc)

    def onClose(self, evt):
        self.exitDlg()
