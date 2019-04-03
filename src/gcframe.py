import wx, math

from gcode import MOVE_MOVE, MOVE_PRINT, MOVE_EXTRUDE, MOVE_RETRACT

MAXZOOM = 10
ZOOMDELTA = 0.1


def triangulate(p1, p2):
	dx = p2[0] - p1[0]
	dy = p2[1] - p1[1]
	d = math.sqrt(dx*dx + dy*dy)
	return d


dk_Gray = wx.Colour(224, 224, 224)
lt_Gray = wx.Colour(128, 128, 128)
black = wx.Colour(0, 0, 0)


class GcFrame (wx.Window):
	def __init__(self, parent, pname, gcode, settings):
		self.parent = parent
		self.pname = pname
		self.settings = settings

		self.printPosition = 0

		self.scale = self.settings.getSetting("scale", self.pname, 3)
		self.zoom = 1
		self.offsety = 0
		self.offsetx = 0
		self.startPos = (0, 0)
		self.startOffset = (0, 0)
		self.buildarea = self.settings.getSetting("buildarea", self.pname, [200, 200])
		self.gcode = None
		self.currentlx = None
		self.shiftX = 0
		self.shiftY = 0
		self.buffer = None
		self.penMap = {}
		self.bkgPenMap = {}

		self.followprint = True

		self.penInvisible = wx.Pen(wx.Colour(0, 0, 0), 1, style=wx.PENSTYLE_TRANSPARENT)
		self.pensInvisible = [self.penInvisible, self.penInvisible]

		self.movePens = [wx.Pen(wx.Colour(128, 128, 128), 1), wx.Pen(wx.Colour(0, 0, 0), 2)]
		self.printPens = [wx.Pen(wx.Colour(255, 0, 0), 1), wx.Pen(wx.Colour(37, 61, 180), 2)]
		self.retractionPens = [wx.Pen(wx.Colour(255, 0, 0), 8), wx.Pen(wx.Colour(45, 222, 222), 8)]
		self.revRetractionPens = [wx.Pen(wx.Colour(255, 0, 0), 8), wx.Pen(wx.Colour(196, 28, 173), 8)]

		self.backgroundPen = wx.Pen(wx.Colour(128, 128, 128), 1)

		self.showmoves = self.settings.getSetting("showmoves", self.pname, False)
		self.showprevious = self.settings.getSetting("showprevious", self.pname, False)
		self.showretractions = self.settings.getSetting("showretractions", self.pname, False)
		self.showrevretractions = self.settings.getSetting("showrevretractions", self.pname, False)
		self.showprintedonly = self.settings.getSetting("showprintedonly", self.pname, False)

		self.setPenMap()

		sz = [(x+1) * self.scale for x in self.buildarea]

		wx.Window.__init__(self,parent,size=sz)
		self.Show()

		self.initBuffer()
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
		self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
		self.Bind(wx.EVT_MOTION, self.onMotion)
		self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel, self)

		if gcode is None:
			self.loadGCode(gcode)

	def setPenMap(self):
		self.penMap = { MOVE_PRINT: self.printPens,
						MOVE_MOVE: self.movePens if self.showmoves else self.pensInvisible,
						MOVE_EXTRUDE: self.revRetractionPens if self.showrevretractions else self.pensInvisible,
						MOVE_RETRACT: self.retractionPens if self.showretractions else self.pensInvisible }

		self.bkgPenMap = { MOVE_PRINT: self.backgroundPen,
							MOVE_MOVE: self.backgroundPen if self.showmoves else self.penInvisible,
							MOVE_EXTRUDE: self.backgroundPen if self.showrevretractions else self.penInvisible,
							MOVE_RETRACT: self.backgroundPen if self.showretractions else self.penInvisible }

	def onSize(self, _):
		self.initBuffer()

	def setFollowPrint(self, flag=True):
		self.followprint = flag
		self.redrawCurrentLayer()

	def setShowPrintedOnly(self, flag=True):
		self.showprintedonly = flag
		self.redrawCurrentLayer()

	def setShowMoves(self, flag=True):
		self.showmoves = flag
		self.setPenMap()
		self.redrawCurrentLayer()

	def setShowPrevious(self, flag=True):
		self.showprevious = flag
		self.setPenMap()
		self.redrawCurrentLayer()

	def setShowRetractions(self, flag=True):
		self.showretractions = flag
		self.setPenMap()
		self.redrawCurrentLayer()

	def setShowRevRetractions(self, flag=True):
		self.showrevretractions = flag
		self.setPenMap()
		self.redrawCurrentLayer()

	def setPrintPosition(self, pos):
		self.printPosition = pos
		self.redrawCurrentLayer()

	def onPaint(self, _):
		dc = wx.BufferedPaintDC(self, self.buffer)  # @UnusedVariable

	def onLeftDown(self, evt):
		self.startPos = evt.GetPosition()
		self.startOffset = (self.offsetx, self.offsety)
		self.CaptureMouse()
		self.SetFocus()

	def onLeftUp(self, _):
		if self.HasCapture():
			self.ReleaseMouse()

	def onMotion(self, evt):
		if evt.Dragging() and evt.LeftIsDown():
			x, y = evt.GetPosition()
			dx = x - self.startPos[0]
			dy = y - self.startPos[1]
			self.offsetx = self.startOffset[0] - dx/(2*self.zoom)
			if self.offsetx < 0:
				self.offsetx = 0
			if self.offsetx > (self.buildarea[0]-self.buildarea[0]/self.zoom):
				self.offsetx = self.buildarea[0]-self.buildarea[0]/self.zoom

			self.offsety = self.startOffset[1] - dy/(2*self.zoom)
			if self.offsety < 0:
				self.offsety = 0
			if self.offsety > (self.buildarea[1]-self.buildarea[1]/self.zoom):
				self.offsety = self.buildarea[1]-self.buildarea[1]/self.zoom

			self.redrawCurrentLayer()

		evt.Skip()

	def onMouseWheel(self, evt):
		if evt.GetWheelRotation() < 0:
			self.zoomIn()
		else:
			self.zoomOut()

	def zoomIn(self):
		if self.zoom < MAXZOOM:
			zoom = self.zoom + ZOOMDELTA
			self.setZoom(zoom)

	def zoomOut(self):
		if self.zoom > 1:
			zoom = self.zoom - ZOOMDELTA
			self.setZoom(zoom)

	def loadGCode(self, gcode, layer=0, zoom=1):
		self.gcode = gcode

		if gcode is None:
			self.currentlx = None
		else:
			self.currentlx = layer
		self.shiftX = 0
		self.shiftY = 0
		if not zoom is None:
			self.zoom = zoom
			if zoom == 1:
				self.offsetx = 0
				self.offsety = 0

		self.printPosition = 0
		self.redrawCurrentLayer()

	def initBuffer(self):
		w, h = self.GetClientSize()
		self.buffer = wx.Bitmap(w, h)
		self.redrawCurrentLayer()

	def setLayer(self, lyr):
		if self.gcode is None:
			return
		if lyr < 0 or lyr >= self.gcode.layerCount():
			return
		if lyr == self.currentlx:
			return

		self.currentlx = lyr
		self.redrawCurrentLayer()

	def getCurrentLayerNum(self):
		return self.currentlx

	def getCurrentLayer(self):
		if self.currentlx is None:
			return None

		return self.gcode.getLayer(self.currentlx)

	def getZoom(self):
		return self.zoom

	def setZoom(self, zoom):
		if zoom > self.zoom:
			oldzoom = self.zoom
			self.zoom = zoom
			cx = self.offsetx + self.buildarea[0]/oldzoom/2.0
			cy = self.offsety + self.buildarea[1]/oldzoom/2.0
			self.offsetx = cx - self.buildarea[0]/self.zoom/2.0
			self.offsety = cy - self.buildarea[1]/self.zoom/2.0
		else:
			oldzoom = self.zoom
			self.zoom = zoom
			cx = self.offsetx + self.buildarea[0]/oldzoom/2.0
			cy = self.offsety + self.buildarea[1]/oldzoom/2.0
			self.offsetx = cx - self.buildarea[0]/self.zoom/2.0
			self.offsety = cy - self.buildarea[1]/self.zoom/2.0
			if self.offsetx < 0:
				self.offsetx = 0
			if self.offsetx > (self.buildarea[0]-self.buildarea[0]/self.zoom):
				self.offsetx = self.buildarea[0]-self.buildarea[0]/self.zoom

			if self.offsety < 0:
				self.offsety = 0
			if self.offsety > (self.buildarea[1]-self.buildarea[1]/self.zoom):
				self.offsety = self.buildarea[1]-self.buildarea[1]/self.zoom

		self.redrawCurrentLayer()

	def setShift(self, sx, sy):
		self.shiftX = sx
		self.shiftY = sy
		self.redrawCurrentLayer()

	def redrawCurrentLayer(self):
		dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)

		self.drawGraph(dc, self.currentlx)

		del dc
		self.Refresh()
		self.Update()

	def drawGraph(self, dc, lyr):
		dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
		dc.Clear()

		self.drawGrid(dc)
		self.drawLayer(dc, lyr)

	def drawGrid(self, dc):
		yleft = (0 - self.offsety)*self.zoom*self.scale
		if yleft < 0: yleft = 0

		yright = (self.buildarea[1] - self.offsety)*self.zoom*self.scale
		if yright > self.buildarea[1]*self.scale: yright = self.buildarea[1]*self.scale

		for x in range(0, self.buildarea[0]+1, 10):
			if x == 0 or x == self.buildarea[0]:
				dc.SetPen(wx.Pen(black, 1))
			elif x%50 == 0:
				dc.SetPen(wx.Pen(lt_Gray, 1))
			else:
				dc.SetPen(wx.Pen(dk_Gray, 1))
			x = (x - self.offsetx)*self.zoom*self.scale
			if 0 <= x <= self.buildarea[0]*self.scale:
				dc.DrawLine(x, yleft, x, yright)

		xtop = (0 - self.offsetx)*self.zoom*self.scale
		if xtop <1: xtop = 1

		xbottom = (self.buildarea[0] - self.offsetx)*self.zoom*self.scale
		if xbottom > self.buildarea[0]*self.scale: xbottom = self.buildarea[0]*self.scale

		for y in range(0, self.buildarea[1]+1, 10):
			if y == 0 or y == self.buildarea[1]:
				dc.SetPen(wx.Pen(black, 1))
			if y%50 == 0:
				dc.SetPen(wx.Pen(lt_Gray, 1))
			else:
				dc.SetPen(wx.Pen(dk_Gray, 1))
			y = (y - self.offsety)*self.zoom*self.scale
			if 0 <= y <= self.buildarea[1]*self.scale:
				dc.DrawLine(xtop, y, xbottom, y)

	def drawLayer(self, dc, lx):
		if lx is None:
			return

		pl = self.currentlx-1
		if pl>=0 and self.showprevious:
			self.drawOneLayer(dc, pl, background=True)

		self.drawOneLayer(dc, lx)

	def drawOneLayer(self, dc, lx, background=False):
		if lx is None:
			return

		layer = self.gcode.getLayer(lx)
		if layer is None:
			return

		pts = [ self.transform(m.x, m.y) for m in layer.getMoves() ]
		mtype = [m.mtype for m in layer.getMoves() ]
		offsets = [m.offset for m in layer.getMoves() ]

		if len(pts) == 0:
			return

		if len(pts) == 1:
			pts = [[pts[0][0], pts[0][1]], [pts[0][0], pts[0][1]]]
			mt = mtype[0]
			mtype = [mt, mt]
			of = offsets[0]
			offsets = [of, of]

		lines = [[pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1]] for i in range(len(pts)-1)]
		pens = [self.getPen(mtype[i+1], offsets[i+1], background) for i in range(len(mtype)-1)]

		dc.DrawLineList(lines, pens)

	def getPen(self, mtype, offset, background):
		if background:
			return self.bkgPenMap[mtype]

		if self.printPosition < offset:
			if self.followprint and self.showprintedonly:
				return self.penInvisible
			else:
				return self.penMap[mtype][0]
		else:
			return self.penMap[mtype][1]

	def transform(self, ptx, pty):
		x = (ptx - self.offsetx + self.shiftX)*self.zoom*self.scale
		y = (self.buildarea[1]-pty - self.offsety - self.shiftY)*self.zoom*self.scale
		return x, y
