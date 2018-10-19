"""
Created on May 4, 2018

@author: Jeff
"""
import wx
import os

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

        self.printPosition = 0
        self.followPrint = True

        self.lx = 0

        lbFont = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.gcf = GcFrame(self, self.pname, self.gcode, self.settings)
        self.stHeight = wx.StaticText(self, wx.ID_ANY, "Height: 0.00")
        self.stHeight.SetFont(lbFont)
        self.slLayer = wx.Slider(self, wx.ID_ANY, 1, 1, 10, style=wx.SL_VERTICAL+wx.SL_LABELS+wx.SL_INVERSE)
        self.Bind(wx.EVT_SLIDER, self.onSlLayer, self.slLayer)
        self.bUp =  wx.BitmapButton(self, wx.ID_ANY, self.images.pngUp, size=BTNDIM, style=wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self.onBUp, self.bUp)
        self.bDown =  wx.BitmapButton(self, wx.ID_ANY, self.images.pngDown, size=BTNDIM, style=wx.NO_BORDER)
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

        szgc = wx.BoxSizer(wx.HORIZONTAL)
        szgc.AddSpacer(15)
        szgc.Add(szgcf)
        if os.name == 'posix':
            szgc.AddSpacer(10)
        szgc.Add(sznavgc, 1, wx.GROW)
        szgc.AddSpacer(15)

        szopt1 = wx.BoxSizer(wx.VERTICAL)
        szopt1.Add(self.cbSync)
        szopt1.Add(self.cbPrintedOnly)

        szopt2 = wx.BoxSizer(wx.VERTICAL)
        szopt2.Add(self.cbShowPrev)
        szopt2.Add(self.cbShowMoves)

        szopt3 = wx.BoxSizer(wx.VERTICAL)
        szopt3.Add(self.cbShowRetr)
        szopt3.Add(self.cbShowRevRetr)

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
        sz.Add(szoptions, 1, wx.GROW)
        sz.AddSpacer(10)

        self.showHeight()

        self.SetSizer(sz)
        self.Fit()

    def formatTitle(self, pname, filenm):
        if filenm is None:
            return "%s - GCode Monitor - (no file loaded)" % pname
        else:
            return "%s - GCode monitor - %s" % (pname, filenm)

    def reloadGCode(self, gcode, filenm):
        self.filenm = filenm
        self.SetTitle(self.formatTitle(self.pname, filenm))
        self.gcode = gcode

        self.setSliderRange()

        # send new gcode to gcf
        self.gcf.loadGCode(gcode)

    def setSliderRange(self):
        n = self.gcode.layerCount()
        self.slLayer.SetRange(1, 10 if n == 0 else n)
        self.slLayer.SetValue(1)
        self.slLayer.Enable(n != 0)
        self.bUp.Enable(n != 0)
        self.bDown.Enable(n != 0)

    def setPrintPosition(self, pos):
        if pos is None:
            return
        self.printPosition = 0 if pos is None else pos
        self.gcf.setPrintPosition(self.printPosition)

        if not self.followPrint:
            return

        pLayer = self.gcode.findLayerByOffset(self.printPosition)
        cLayer = self.gcf.getCurrentLayerNum()

        if cLayer != pLayer:
            self.gcf.setLayer(pLayer)
            self.slLayer.SetValue(pLayer+1)
            self.showHeight()

    def showHeight(self):
        l = self.gcf.getCurrentLayer()
        if l is None:
            lbl = "Height: ???"
        else:
            lbl = "Height: %.2f" % l.getHeight()
        self.stHeight.SetLabel(lbl)

    def onSlLayer(self, evt):
        self.followPrintOff()
        v = self.slLayer.GetValue()-1
        self.gcf.setLayer(v)
        self.showHeight()

    def onBUp(self, evt):
        v = self.slLayer.GetValue()
        if v < self.gcode.layerCount():
            self.followPrintOff()
            v += 1
            self.slLayer.SetValue(v)
            self.gcf.setLayer(v-1)
            self.showHeight()

    def onBDown(self, evt):
        v = self.slLayer.GetValue()
        if v > 1:
            self.followPrintOff()
            v -= 1
            self.slLayer.SetValue(v)
            self.gcf.setLayer(v-1)
            self.showHeight()

    def followPrintOff(self):
        if self.followPrint:
            self.cbSync.SetValue(False)
            self.followPrint = False
            self.gcf.setFollowPrint(False)

    def onCbSync(self, evt):
        self.followPrint = self.cbSync.GetValue()
        self.gcf.setFollowPrint(self.followPrint)

    def onCbShowPrintedOnly(self, evt):
        v = self.cbPrintedOnly.GetValue()
        self.settings.setSetting("showprintedonly", str(v), self.pname)
        self.gcf.setShowPrintedOnly(v)

    def onCbShowPrev(self, evt):
        v = self.cbShowPrev.GetValue()
        self.settings.setSetting("showprevious", str(v), self.pname)
        self.gcf.setShowPrevious(v)

    def onCbShowMoves(self, evt):
        v = self.cbShowMoves.GetValue()
        self.settings.setSetting("showmoves", str(v), self.pname)
        self.gcf.setShowMoves(v)

    def onCbShowRetr(self, evt):
        v = self.cbShowRetr.GetValue()
        self.settings.setSetting("showretractions", str(v), self.pname)
        self.gcf.setShowRetractions(v)

    def onCbShowRevRetr(self, evt):
        v = self.cbShowRevRetr.GetValue()
        self.settings.setSetting("showrevretractions", str(v), self.pname)
        self.gcf.setShowRevRetractions(v)

    def onClose(self, evt):
        self.exitDlg()
