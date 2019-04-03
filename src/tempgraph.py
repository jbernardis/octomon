import wx
import os
import matplotlib

matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
import numpy
import pylab
from settings import XCOUNT

defaultActualColors = {
    "bed": (255, 0, 0),
    "tool0": (0, 255, 0),
    "tool1": (0, 0, 255)}

defaultTargetColors = {
    "bed": (0, 255, 255),
    "tool0": (255, 0, 255),
    "tool1": (255, 255, 0)}

class TempGraph(wx.Frame):
    def __init__(self, parent, pName, settings, images, history, cbNext, cbExit):
        wx.Frame.__init__(self, parent, -1, "%s Temperature Monitor" % pName)

        self.Bind(wx.EVT_CLOSE, self.on_exit)

        self.pName = pName
        self.settings = settings
        self.images = images
        self.history = history
        self.nextData = cbNext
        self.exitDlg = cbExit

        self.lbFont = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.lbFontL = wx.Font(16, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.lFont = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        di = self.history[0]
        self.heaters = sorted(di.keys())
        self.actualColors = {}
        self.targetColors = {}
        for k in self.heaters:
            self.actualColors[k] = settings.getSetting("tempcolor.%s.actual" % k, pName, defaultActualColors[k])
            self.targetColors[k] = settings.getSetting("tempcolor.%s.target" % k, pName, defaultTargetColors[k])

        self.actual = {}
        self.pendingActual = {}
        self.showActual = {}
        self.target = {}
        self.pendingTarget = {}
        self.showTarget = {}

        for k in self.heaters:
            self.actual[k] = []
            self.pendingActual[k] = []
            self.showActual[k] = True

            self.target[k] = []
            self.pendingTarget[k] = []
            self.showTarget[k] = True

        for di in self.history:
            for k in self.heaters:
                self.actual[k].append(di[k]["actual"])
                self.target[k].append(di[k]["target"])


        self.paused = False

        self.create_main_panel()

        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        self.redraw_timer.Start(1000)

    def create_main_panel(self):
        self.panel = wx.Panel(self)

        self.init_plot()
        self.canvas = FigCanvas(self.panel, -1, self.fig)

        self.bPause = wx.BitmapButton(self.panel, -1, self.images.pngPause,
                size=(48, 48) if os.name == 'posix' else (32, 32), style=wx.NO_BORDER)
        self.bPause.SetToolTip("Pause/Resume dynamic graph")
        self.Bind(wx.EVT_BUTTON, self.on_bPause, self.bPause)

        self.cb_grid = wx.CheckBox(self.panel, wx.ID_ANY, "Show Grid")
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)
        self.cb_grid.SetValue(True)

        self.cbActuals = {}
        self.cbTargets = {}
        self.teCurrentActual = {}
        self.teCurrentTarget = {}
        self.bPaletteActual = {}
        self.bPaletteTarget = {}
        for k in self.heaters:
            a = wx.CheckBox(self.panel, wx.ID_ANY, "", name=k)
            a.SetToolTip("Hide/show %s actual graph" % k)
            self.Bind(wx.EVT_CHECKBOX, self.on_cb_actual, a)
            a.SetValue(True)
            self.cbActuals[k] = a

            t = wx.CheckBox(self.panel, wx.ID_ANY, "", name=k)
            t.SetToolTip("Hide/show %s target graph" % k)
            self.Bind(wx.EVT_CHECKBOX, self.on_cb_target, t)
            t.SetValue(True)
            self.cbTargets[k] = t

            b = wx.BitmapButton(self.panel, wx.ID_ANY, self.images.pngPalette,
                    size=(32, 32) if os.name == 'posix' else (16, 16), style=wx.NO_BORDER, name=k)
            b.SetToolTip("Change color for %s actual graph" % k)
            self.Bind(wx.EVT_BUTTON, self.on_b_actual, b)
            self.bPaletteActual[k] = b

            b = wx.BitmapButton(self.panel, wx.ID_ANY, self.images.pngPalette,
                    size=(32, 32) if os.name == 'posix' else (16, 16), style=wx.NO_BORDER, name=k)
            b.SetToolTip("Change color for %s target graph" % k)
            self.Bind(wx.EVT_BUTTON, self.on_b_target, b)
            self.bPaletteTarget[k] = b

            te = wx.TextCtrl(self.panel, wx.ID_ANY, "",
                             size=(84 if os.name == 'posix' else 50, -1), style=wx.TE_READONLY)
            te.SetFont(self.lbFont)
            te.SetForegroundColour(wx.Colour(self.actualColors[k]))
            self.teCurrentActual[k] = te

            te = wx.TextCtrl(self.panel, wx.ID_ANY, "",
                             size=(84 if os.name == 'posix' else 50, -1), style=wx.TE_READONLY)
            te.SetFont(self.lbFont)
            te.SetForegroundColour(wx.Colour(self.targetColors[k]))
            self.teCurrentTarget[k] = te

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.bPause, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        hbox1.AddSpacer(20)
        hbox1.Add(self.cb_grid, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

        canvasBox = wx.BoxSizer(wx.VERTICAL)
        canvasBox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)
        canvasBox.Add(hbox1, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        canvasBox.AddSpacer(20)

        currentBox = wx.BoxSizer(wx.VERTICAL)
        currentBox.AddSpacer(10)
        for k in self.heaters:
            boxHtr = wx.StaticBox(self.panel, wx.ID_ANY, " %s " % k)
            boxHtr.SetFont(self.lbFont)
            szHtr = wx.StaticBoxSizer(boxHtr, wx.VERTICAL)
            szHtr.AddSpacer(5)

            h = wx.BoxSizer(wx.HORIZONTAL)
            t = wx.StaticText(self.panel, wx.ID_ANY, "Actual:", size=(60, -1))
            t.SetFont(self.lbFont)
            h.Add(t, 1, wx.TOP, 4)
            h.AddSpacer(5)
            h.Add(self.teCurrentActual[k])
            h.AddSpacer(10)
            h.Add(self.cbActuals[k], 0, wx.TOP, 6)
            h.AddSpacer(5)
            h.Add(self.bPaletteActual[k], 0, wx.TOP, 0 if os.name == 'posix' else 6)

            szHtr.Add(h, 1, wx.LEFT + wx.RIGHT, 20)

            szHtr.AddSpacer(5)

            h = wx.BoxSizer(wx.HORIZONTAL)
            t = wx.StaticText(self.panel, wx.ID_ANY, "Target:", size=(60, -1))
            t.SetFont(self.lbFont)
            h.Add(t, 1, wx.TOP, 4)
            h.AddSpacer(5)
            h.Add(self.teCurrentTarget[k])
            h.AddSpacer(10)
            h.Add(self.cbTargets[k], 0, wx.TOP, 6)
            h.AddSpacer(5)
            h.Add(self.bPaletteTarget[k], 0, wx.TOP, 0 if os.name == 'posix' else 6)

            szHtr.Add(h, 1, wx.LEFT + wx.RIGHT, 20)

            szHtr.AddSpacer(5)

            currentBox.Add(szHtr)
            currentBox.AddSpacer(10)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(canvasBox)
        hbox.Add(currentBox)
        hbox.AddSpacer(20)

        self.panel.SetSizer(hbox)
        hbox.Fit(self)

    def init_plot(self):
        self.dpi = 100
        self.fig = Figure((6.0, 3.0), dpi=self.dpi)

        self.axes = self.fig.add_subplot(111)
        self.axes.set_title("%s Temperature" % self.pName, size=12)
        self.axes.set_xbound(lower=-XCOUNT, upper=0)
        self.axes.set_ybound(lower=0, upper=250)
        self.axes.set_xticks(range(-XCOUNT, 1, 60))
        self.axes.set_xticklabels(["%d:00" % int(x / 60) for x in range(-600, 1, 60)])

        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)

        self.plot_actual = {}
        self.plot_target = {}
        for k in self.heaters:
            self.plot_actual[k] = self.axes.plot(
                [0], # * XCOUNT,
                linewidth=1,
                color=[x/255.0 for x in self.actualColors[k]]
            )[0]
            self.plot_target[k] = self.axes.plot(
                [0], # * XCOUNT,
                linewidth=1,
                linestyle="-.",
                color=[x/255.0 for x in self.targetColors[k]]
            )[0]

    def draw_plot(self):
        self.axes.set_xbound(lower=-XCOUNT, upper=0)
        self.axes.set_ybound(lower=0, upper=250)
        if self.cb_grid.IsChecked():
            self.axes.grid(True, color='gray')
        else:
            self.axes.grid(False)

        l = len(self.actual[list(self.actual.keys())[0]])
        if l > XCOUNT:
            l = XCOUNT
            for k in self.heaters:
                self.actual[k] = self.actual[k][-XCOUNT:]
                self.target[k] = self.target[k][-XCOUNT:]

        xdata = numpy.arange(-l + 1, 1)
        for k in self.heaters:
            if self.showActual[k]:
                self.plot_actual[k].set_xdata(xdata)
                self.plot_actual[k].set_ydata(numpy.array(self.actual[k]))
            else:
                self.plot_actual[k].set_xdata(None)
                self.plot_actual[k].set_ydata(None)

            if self.showTarget[k]:
                self.plot_target[k].set_xdata(numpy.array([-XCOUNT+1, 0]))
                self.plot_target[k].set_ydata(numpy.array([self.target[k][-1], self.target[k][-1]]))
            else:
                self.plot_target[k].set_xdata(None)
                self.plot_target[k].set_ydata(None)

        self.canvas.draw()

    def on_bPause(self, _):
        self.paused = not self.paused
        png = self.images.pngResume if self.paused else self.images.pngPause
        self.bPause.SetBitmap(png)

    def on_cb_grid(self, _):
        self.draw_plot()

    def on_cb_actual(self, evt):
        o = evt.GetEventObject()
        t = o.GetName()
        self.showActual[t] = o.GetValue()
        self.draw_plot()

    def on_cb_target(self, evt):
        o = evt.GetEventObject()
        t = o.GetName()
        self.showTarget[t] = o.GetValue()
        self.draw_plot()

    def on_b_actual(self, evt):
        o = evt.GetEventObject()
        t = o.GetName()
        newColor = self.chooseColor(self.actualColors[t])
        if newColor is not None:
            self.teCurrentActual[t].SetForegroundColour(newColor)
            self.teCurrentActual[t].Refresh()
            self.settings.setSetting("tempcolor.%s.actual" % t, str(newColor), self.pName)
            self.actualColors[t] = newColor
            self.plot_actual[t].set_color([x/255.0 for x in newColor])

    def on_b_target(self, evt):
        o = evt.GetEventObject()
        t = o.GetName()
        newColor = self.chooseColor(self.targetColors[t])
        if newColor is not None:
            self.teCurrentTarget[t].SetForegroundColour(newColor)
            self.teCurrentTarget[t].Refresh()
            self.settings.setSetting("tempcolor.%s.target" % t, str(newColor), self.pName)
            self.targetColors[t] = newColor
            self.plot_target[t].set_color([x/255.0 for x in newColor])

    def chooseColor(self, ccolor):
        dlg = wx.ColourDialog(self)
        cd = dlg.GetColourData()
        cd.SetChooseFull(True)
        cd.SetColour(ccolor)

        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            color = data.GetColour().Get()
            return color[0:3]
        else:
            return None

    def on_redraw_timer(self, _):
        di = self.nextData()
        for k in self.heaters:
            self.teCurrentActual[k].SetValue("%.1f" % di[k]["actual"])
            self.teCurrentTarget[k].SetValue("%.1f" % di[k]["target"])

        if self.paused:
            for k in self.heaters:
                self.pendingActual[k].append(di[k]["actual"])
                if len(self.pendingActual[k]) > XCOUNT:
                    self.pendingActual[k] = self.pendingActual[-XCOUNT:]
                self.pendingTarget[k].append(di[k]["target"])
                if len(self.pendingTarget[k]) > XCOUNT:
                    self.pendingTarget[k] = self.pendingTarget[-XCOUNT:]
        else:
            for k in self.heaters:
                self.actual[k].extend(self.pendingActual[k])
                self.pendingActual[k] = []
                self.actual[k].append(di[k]["actual"])
                self.target[k].extend(self.pendingTarget[k])
                self.pendingTarget[k] = []
                self.target[k].append(di[k]["target"])

        self.draw_plot()

    def close(self):
        self.redraw_timer.Stop()

    def on_exit(self, _):
        self.redraw_timer.Stop()
        self.exitDlg()
