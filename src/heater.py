"""
Created on May 11, 2018

@author: Jeff
"""

import wx
import os


class Heater(wx.Window):
    def __init__(self, parent, server, setter, hIndex, name, minTemp, maxTemp, presets):
        self.parent = parent
        self.images = parent.images
        self.settings = parent.settings
        self.server = server
        self.setter = setter
        self.hIndex = hIndex
        self.heaterOn = False
        self.lastSetValue = -1
        if self.hIndex is not None:
            self.shIndex = "%d" % self.hIndex

        lbFont = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        lFont = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.name = name
        self.minTemp = minTemp
        self.maxTemp = maxTemp
        self.presets = presets
        wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.NO_BORDER)

        szHeater = wx.BoxSizer(wx.HORIZONTAL)
        szHeater.AddSpacer(10)

        l = wx.StaticText(self, wx.ID_ANY, self.name, size=(50, -1))
        l.SetFont(lbFont)
        szHeater.Add(l, 0, wx.TOP, 13 if os.name == 'posix' else 5)
        szHeater.AddSpacer(5)

        self.sc = wx.SpinCtrl(self, wx.ID_ANY, "", size=(120 if os.name == 'posix' else 70, -1), style=wx.ALIGN_RIGHT)
        self.sc.SetFont(lbFont)
        self.sc.SetRange(self.minTemp, self.maxTemp)
        self.sc.SetValue(self.minTemp)

        szHeater.Add(self.sc, 0, wx.TOP, 8 if os.name == 'posix' else 0)

        self.bPower = wx.BitmapButton(self, wx.ID_ANY, self.images.pngHeatoff,
                                      size=(48, 48) if os.name == 'posix' else (32, 32), style=wx.NO_BORDER)
        self.bPower.SetToolTip("Turn heater on/off")
        self.Bind(wx.EVT_BUTTON, self.onBPower, self.bPower)

        szHeater.AddSpacer(5)
        szHeater.Add(self.bPower)

        self.chPresets = wx.Choice(self, wx.ID_ANY, choices=[x[0] for x in self.presets])
        self.chPresets.SetFont(lFont)
        self.chPresets.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.onPreset, self.chPresets)

        szHeater.AddSpacer(5)
        szHeater.Add(self.chPresets, 0, wx.TOP, 8 if os.name == 'posix' else 0)

        szHeater.AddSpacer(10)
        self.SetSizer(szHeater)
        self.Layout()

    def enableControls(self, flag):
        self.sc.Enable(flag)
        self.bPower.Enable(flag)
        self.chPresets.Enable(flag)

    def onPreset(self, evt):
        s = evt.GetSelection()
        if s == wx.NOT_FOUND:
            return

        t = self.presets[s][1]
        self.sc.SetValue(t)
        self.setHeater(t)

    def setTarget(self, target):
        if target == 0 and self.heaterOn:
            self.heaterOn = False
            self.bPower.SetBitmap(self.images.pngHeatoff)
            # self.sc.SetValue(target)
        elif target != 0 and target != self.lastSetValue:
            self.heaterOn = True
            self.bPower.SetBitmap(self.images.pngHeaton)
            # self.sc.SetValue(target)

    def onBPower(self, evt):
        nv = self.sc.GetValue()
        self.setHeater(nv)

    def setHeater(self, nv):
        try:
            if self.hIndex is None:
                self.setter(nv)
            else:
                self.setter({self.shIndex: nv})
        except:
            self.parent.askToSever("Unable to set heater power")
            return

        self.setTarget(nv)
        self.lastSetValue = nv
