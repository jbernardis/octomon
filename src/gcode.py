import re

gcRegex = re.compile("[-]?\d+[.]?\d*")

MOVE_MOVE = 'm'
MOVE_PRINT = 'p'
MOVE_EXTRUDE = 'e'
MOVE_RETRACT = 'r'


class GCMove:
    def __init__(self, x, y, e, f, mtype, offset):
        # print ("Movement type {:d} to coordinate {:f},{:f}, offset = {:d}".format(mtype, x, y, offset))
        self.x = x
        self.y = y
        self.e = e
        self.f = f
        self.mtype = mtype
        self.offset = offset

    def getMoveType(self):
        return self.mtype

    def getOffset(self):
        return self.offset


class GCLayer:
    def __init__(self, ht):
        # print ("new layer at height {:f}".format(ht))
        self.height = ht;
        self.moves = []
        self.minOffset = None
        self.maxOffset = None
        self.printMoves = 0
        self.moveMoves = 0
        self.extrudeMoves = 0

    def getMoves(self):
        return self.moves

    def addMove(self, move):
        self.moves.append(move)
        mo = move.getOffset()
        if self.minOffset is None or mo < self.minOffset: self.minOffset = mo
        if self.maxOffset is None or mo > self.maxOffset: self.maxOffset = mo
        mt = move.getMoveType()
        if mt == MOVE_PRINT:
            self.printMoves += 1
        elif mt == MOVE_MOVE:
            self.moveMoves += 1
        elif mt == MOVE_EXTRUDE:
            self.extrudeMoves += 1

    def getHeight(self):
        return self.height

    def getMoveCounts(self):
        return len(self.moves), self.printMoves, self.moveMoves, self.extrudeMoves

    def getOffsets(self):
        return self.minOffset, self.maxOffset

    def setMinOffset(self, mino):
        self.minOffset = mino


class GCode:
    def __init__(self, gc):
        self.gcode = gc.split("\n")

        self.relativeExtrude = False
        self.relativeMove = False
        self.hasMovement = False
        self.hasFilament = False

        self.layer = GCLayer(0.0)
        self.layers = []
        self.layers.append(self.layer)

        self.lastX = self.paramX = 0.0
        self.lastY = self.paramY = 0.0
        self.lastZ = self.paramZ = 0.0
        self.lastE = self.paramE = 0.0
        self.lastF = self.paramF = 1000.0

        offset = 0
        ln = 0
        for gl in self.gcode:
            offset += len(gl) + 1

            ln += 1
            self.parseGLine(gl, offset)
            if self.hasMovement:
                if self.paramZ != self.lastZ:
                    self.layer = GCLayer(self.paramZ)
                    self.layers.append(self.layer)

                if self.paramE == self.lastE:
                    moveType = MOVE_MOVE
                else:
                    moveType = MOVE_PRINT
                self.layer.addMove(GCMove(self.paramX, self.paramY, self.paramE, self.paramF, moveType, offset))
            elif self.hasFilament:
                if self.paramE > self.lastE:
                    moveType = MOVE_EXTRUDE
                else:
                    moveType = MOVE_RETRACT
                self.layer.addMove(GCMove(self.paramX, self.paramY, self.paramE, self.paramF, moveType, offset))

            self.lastX = self.paramX
            self.lastY = self.paramY
            self.lastZ = self.paramZ
            self.lastE = self.paramE
            self.lastF = self.paramF

        self.compress()

    def getLayer(self, lx):
        if lx < 0 or lx >= len(self.layers):
            return None

        return self.layers[lx]

    def findLayerByOffset(self, offset):
        lx = 0
        if len(self.layers) == 0:
            return 0

        for l in self.layers:
            minOff, maxOff = l.getOffsets()
            if minOff <= offset <= maxOff:
                return lx
            lx += 1

        if offset >= self.layers[-1].getOffsets()[1]:
            return lx-1

        return 0

    def layerCount(self):
        return len(self.layers)

    def compress(self):
        nl = []
        lastMaxOffset = None
        for l in self.layers:
            printMoves = l.getMoveCounts()[1]

            if printMoves != 0:
                if lastMaxOffset is not None:
                    l.setMinOffset(lastMaxOffset+1)
                lastMaxOffset = l.getOffsets()[1]
                nl.append(l)

        self.layers = nl

    def parseGLine(self, gl, offset):
        self.hasMovement = False
        self.hasFilament = False
        if ";" in gl:
            gl = gl.split(";")[0]
        if gl.strip() == "":
            return

        p = re.split("\\s+", gl, 1) + [""]

        cmd = p[0].strip().upper()
        if cmd in ["G1", "G2"]:
            if "X" in p[1]:
                self.hasMovement = True
            if "Y" in p[1]:
                self.hasMovement = True
            if "Z" in p[1]:
                self.hasMovement = True
            if "E" in p[1]:
                self.hasFilament = True

            self.paramX = self._get_float(p[1], "X", self.lastX, self.relativeMove)
            self.paramY = self._get_float(p[1], "Y", self.lastY, self.relativeMove)
            self.paramZ = self._get_float(p[1], "Z", self.lastZ, self.relativeMove)
            self.paramE = self._get_float(p[1], "E", self.lastE, self.relativeExtrude)
            self.paramF = self._get_float(p[1], "F", self.lastF)

        elif cmd == "G92":
            self.paramX = self._get_float(p[1], "X", self.lastX)
            self.paramY = self._get_float(p[1], "Y", self.lastY)
            self.paramZ = self._get_float(p[1], "Z", self.lastZ)
            self.paramE = self._get_float(p[1], "E", self.lastE)
            self.paramF = self._get_float(p[1], "F", self.lastF)

        elif cmd == "G28":
            self.hasMovement = True
            if not ("X" in p[1] or "Y" in p[1] or "Z" in p[1]):
                self.paramX = self.paramY = self.paramZ = 0.0
            else:
                self.paramX = 0.0 if "X" in p[1] else self.lastX
                self.paramY = 0.0 if "Y" in p[1] else self.lastY
                self.paramZ = 0.0 if "Z" in p[1] else self.lastZ
            self.paramE = self.lastE
            self.paramF = self.lastF

        elif cmd == "G90":
            self.relativeMove = False

        elif cmd == "G91":
            self.relativeMove = True

        elif cmd == "M82":
            self.relativeExtrude = False

        elif cmd == "M83":
            self.relativeExtrude = True

        else:
            pass
            # print ("Not processing command (%s) at offset %d" % (cmd, offset))

    def _get_float(self, paramStr, which, last, relativeValue=False):
        try:
            v = float(gcRegex.findall(paramStr.split(which)[1])[0])
            if relativeValue:
                return v+last
            else:
                return v
        except:
            return last
