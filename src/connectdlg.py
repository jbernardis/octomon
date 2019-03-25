"""
Created on May 4, 2018

@author: Jeff
"""
import wx

BTNDIM = (48, 48)

class ConnectDlg(wx.Dialog):
	def __init__(self, parent, pname, port, ports, baudrate, baudrates):
		wx.Dialog.__init__(self, None, wx.ID_ANY, "%s Connection" % pname)
		self.SetBackgroundColour("white")
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.parent = parent
		self.images = parent.images

		self.port = None
		self.baudrate = None

		sz = wx.BoxSizer(wx.HORIZONTAL)
		sz.AddSpacer(10)

		vsz = wx.BoxSizer(wx.VERTICAL)
		vsz.AddSpacer(10)

		bsz = wx.BoxSizer(wx.HORIZONTAL)
		
		if port in ports:
			self.lPorts = ports
		else:
			self.lPorts = ports + [ port ]
			
		if baudrate in baudrates:
			self.lBaudrates = baudrates
		else:
			self.lBaudrates = baudrates + [ baudrate ]

		box = wx.StaticBox(self, wx.ID_ANY, " Port ")
		bsizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
			
		self.chPorts = wx.Choice(self, wx.ID_ANY, choices=self.lPorts, size=(160, -1)) 
		bsizer.Add(self.chPorts)
		vsz.Add(bsizer)
		vsz.AddSpacer(5)
		v = self.lPorts.index(port)
		self.chPorts.SetSelection(v)
		
		vsz.AddSpacer(5)

		box = wx.StaticBox(self, wx.ID_ANY, " Baud Rate ")
		bsizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
		
		self.chBaudrates = wx.Choice(self, wx.ID_ANY, choices=["%d" % x for x in self.lBaudrates], size=(160, -1)) 
		bsizer.Add(self.chBaudrates)
		vsz.Add(bsizer)
		v = self.lBaudrates.index(baudrate)
		self.chBaudrates.SetSelection(v)
		
		vsz.AddSpacer(10)
		
		b = wx.BitmapButton(self, wx.ID_ANY, self.images.pngConnect, size=BTNDIM)
		b.SetToolTip("Connect to Printer")
		self.Bind(wx.EVT_BUTTON, self.onBConnect, b)
		bsz.Add(b)
		bsz.AddSpacer(10)
		
		b = wx.BitmapButton(self, wx.ID_ANY, self.images.pngCancel, size=BTNDIM)
		b.SetToolTip("Cancel Connection")
		self.Bind(wx.EVT_BUTTON, self.onBCancel, b)
		bsz.Add(b)
		bsz.AddSpacer(10)
		
		vsz.Add(bsz, 0, wx.ALIGN_CENTER_HORIZONTAL)
		vsz.AddSpacer(10)

		sz.Add(vsz)
		sz.AddSpacer(10)

		self.SetSizer(sz)
		self.Fit()
		
	def getResults(self):
		return self.baudrate, self.port
		
	def onBConnect(self, _):
		v = self.chPorts.GetSelection()
		self.port = self.lPorts[v]
		v = self.chBaudrates.GetSelection()
		self.baudrate = self.lBaudrates[v]
		self.EndModal(wx.ID_OK)
		
	def onBCancel(self, _):
		self.EndModal(wx.ID_CANCEL)

	def onClose(self, _):
		self.EndModal(wx.ID_CANCEL)
