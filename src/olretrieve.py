"""
Created on May 14, 2018

@author: Jeff
"""

import os
import wx
import paramiko

class OLRetrieveDlg(wx.Frame):
	def __init__(self, parent, pname, cb):
		wx.Frame.__init__(self, None, wx.ID_ANY, "OptoLapse Files: %s" % pname)
		self.SetBackgroundColour("white")

		self.selectedItem = None

		self.parent = parent
		self.images = self.parent.images
		self.settings = self.parent.settings
		self.pname = pname
		self.cb = cb

		dnsname = self.settings.getSetting("dnsname", section=pname)

		self.ssh = paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		self.ssh.connect(dnsname + ".local", 22, "pi", "raspberry")
		self.sftp = self.ssh.open_sftp()
		self.sftp.sshclient = self.ssh

		self.remoteDir = "/home/pi/.octoprint/timelapse"
		self.fileList = [x for x in self.sftp.listdir(self.remoteDir) if x.lower().endswith(".mp4")]

		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.listBox = wx.ListBox(self, wx.ID_ANY, choices=[], style=wx.LB_SORT + wx.LB_SINGLE, size=(300, 200))

		self.bDelete = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDelete, size=(48, 48))
		self.bDelete.SetToolTip("Delete file")
		self.Bind(wx.EVT_BUTTON, self.onBDelete, self.bDelete)

		self.bDownload = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDownload, size=(48, 48))
		self.bDownload.SetToolTip("Download file")
		self.Bind(wx.EVT_BUTTON, self.onBDownload, self.bDownload)
		self.setListBox()

		hsz = wx.BoxSizer(wx.HORIZONTAL)
		sz = wx.BoxSizer(wx.VERTICAL)
		sz.AddSpacer(10)
		sz.Add(self.listBox)
		sz.AddSpacer(10)
		
		bsz = wx.BoxSizer(wx.HORIZONTAL)
		bsz.AddSpacer(10)
		bsz.Add(self.bDownload)
		bsz.AddSpacer(10)
		bsz.Add(self.bDelete)
		bsz.AddSpacer(10)
		sz.Add(bsz, 1, wx.ALIGN_CENTER)
		sz.AddSpacer(10)

		hsz.AddSpacer(10)
		hsz.Add(sz)
		hsz.AddSpacer(10)

		self.SetSizer(hsz)
		self.Layout()
		self.Fit()

		self.Show()

	def setListBox(self):
		self.fileList = [x for x in self.sftp.listdir(self.remoteDir) if x.lower().endswith(".mp4")]
		self.listBox.Set(self.fileList)
		if len(self.fileList) > 0:
			self.listBox.SetSelection(0)
			self.bDelete.Enable(True)
			self.bDownload.Enable(True)
		else:
			self.bDelete.Enable(False)
			self.bDownload.Enable(False)


	def getSelectedFile(self):
		n = self.listBox.GetSelection()
		if n == wx.NOT_FOUND:
			return None
		return self.listBox.GetString(n)

	def onBDelete(self, _):
		f = self.getSelectedFile()
		if f is None:
			return
		path = "/".join([self.remoteDir, f])
		self.sftp.remove(path)

		dlg = wx.MessageDialog(self, "File \"{}\" deleted".format(f),
							   'File Deleted', wx.OK | wx.ICON_INFORMATION)
		dlg.ShowModal()
		dlg.Destroy()

		self.setListBox()

	def onBDownload(self, _):
		f = self.getSelectedFile()
		if f is None:
			return

		wildcard = "MP4 (*.MP4)|*.mp4;*.MP4"

		dlg = wx.FileDialog(
			self, message="Save as ...", defaultDir=self.settings.getSetting("octoLapseDirectory", dftValue="."),
			defaultFile=f, wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

		val = dlg.ShowModal()

		if val != wx.ID_OK:
			dlg.Destroy()
			return

		path = dlg.GetPath()
		dlg.Destroy()

		dpath = os.path.dirname(path)
		self.settings.setSetting("octoLapseDirectory", dpath)

		ext = os.path.splitext(os.path.basename(path))[1]
		if ext == "":
			path += ".mp4"

		rpath = "/".join([self.remoteDir, f])
		self.sftp.get(rpath, path)

		dlg = wx.MessageDialog(self, "File \"{}\"\ndownloaded to \"{}\"".format(f, path),
							   'Download Complete', wx.OK | wx.ICON_INFORMATION)
		dlg.ShowModal()
		dlg.Destroy()

	def onClose(self, _):
		self.ssh.close()
		self.cb()
