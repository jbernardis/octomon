
import re

class M92(object):
# Recv (Steps per unit:)
# Recv (M92 X44.44 Y44.44 Z400.00 E833.30)
	def __init__(self):
		self.x = None
		self.y = None
		self.z = None
		self.e = None
		self.hasValues = False

	def __repr__(self):
		return "M92 X(%f) Y(%f) Z(%f) E(%f)" % (self.x, self.y, self.z, self.e)
		
	def clearHasValues(self):
		self.hasValues = False
	
	def setStepsPerUnit(self, x, y, z, e):
		self.x = x
		self.y = y
		self.z = z 
		self.e = e 
		self.hasValues = True

class M201(object):
# Recv (Maximum Acceleration (mm/s2):)
# Recv (M201 X3500 Y3500 Z100 E2000)
	def __init__(self):
		self.x = None
		self.y = None
		self.z = None
		self.e = None
		self.hasValues = False

	def __repr__(self):
		return "M201 X(%f) Y(%f) Z(%f) E(%f)" % (self.x, self.y, self.z, self.e)
		
	def clearHasValues(self):
		self.hasValues = False
	
	def setMaxAccel(self, x, y, z, e):
		self.x = x
		self.y = y
		self.z = z 
		self.e = e 
		self.hasValues = True

class M203(object):
# Recv (Maximum feedrates (mm/s):)
# Recv (M203 X500.00 Y500.00 Z5.00 E25.00)
	def __init__(self):
		self.x = None
		self.y = None
		self.z = None
		self.e = None
		self.hasValues = False

	def __repr__(self):
		return "M203 X(%f) Y(%f) Z(%f) E(%f)" % (self.x, self.y, self.z, self.e)
		
	def clearHasValues(self):
		self.hasValues = False
	
	def setMaxFeedRates(self, x, y, z, e):
		self.x = x
		self.y = y
		self.z = z 
		self.e = e 
		self.hasValues = True
		
class M204(object):
# Recv (Accelerations: P=printing, R=retract and T=travel)
# Recv (M204 P1000.00 R2000.00 T3000.00)
	def __init__(self):
		self.p = None
		self.r = None
		self.t = None
		self.hasValues = False
		
	def __repr__(self):
		return "M204 P(%f) R(%f) T(%f)" % (self.p, self.r, self.t)
		
	def clearHasValues(self):
		self.hasValues = False
	
	def setAcceleration(self, p, r, t):
		self.p = p
		self.r = r
		self.t = t
		self.hasValues = True

class M205(object):
#  Recv (Advanced variables: S=Min feedrate (mm/s), T=Min travel feedrate (mm/s), B=minimum segment time (ms), X=maximum XY jerk (mm/s),  Z=maximum Z jerk (mm/s),  E=maximum E jerk (mm/s))
# Recv (M205 S0.00 T0.00 B20000 X10.00 Z0.40 E5.00)
	def __init__(self):
		self.s = None
		self.t = None
		self.b = None
		self.x = None
		self.z = None
		self.e = None
		self.hasValues = False
		
	def __repr__(self):
		return "M205 S(%f) T(%f) B(%f) X(%f) Z(%f) E(%f)" % (self.s, self.t, self.b, self.x, self.z, self.e)
		
	def clearHasValues(self):
		self.hasValues = False
	
	def setValues(self, s, t, b, x, z, e):
		self.s = s
		self.t = t
		self.b = b
		self.x = x
		self.z = z
		self.e = e
		self.hasValues = True

class M301(object):
# Recv (PID settings:)
# Recv (M301 P18.97 I1.23 D73.04 C100.00 L20)
	def __init__(self):
		self.p = None
		self.i = None
		self.d = None
		self.c = None
		self.l = None
		self.hasValues = False
		
	def __repr__(self):
		return "M301 P(%f) I(%f) D(%f) C(%f) L(%f)" % (self.p, self.i, self.d, self.c, self.l)
		
	def clearHasValues(self):
		self.hasValues = False
	
	def setPID(self, p, i, d, c, l):
		self.p = p
		self.i = i
		self.d = d
		self.c = c
		self.l = l
		self.hasValues = True

gcRegex = re.compile("[-]?\d+[.]?\d*")

def get_float(paramStr, which):
	try:
		v = float(gcRegex.findall(paramStr.split(which)[1])[0])
		return v
	except ValueError:
		return None

class EEProm(object):
	def __init__(self):
		self.cb = None
		self.m92 = M92()
		self.m201 = M201()
		self.m203 = M203()
		self.m204 = M204()
		self.m205 = M205()
		self.m301 = M301()
		
	def __repr__(self):
		return ("EEProm:\n" + str(self.m92) + "\n" +
			str(self.m201) + "\n" +
			str(self.m203) + "\n" +
			str(self.m204) + "\n" +
			str(self.m205) + "\n" +
			str(self.m301))
		
	def setCallbackTrigger(self, cb):
		self.cb = cb
		self.m92.clearHasValues()
		self.m203.clearHasValues()
		self.m201.clearHasValues()
		self.m204.clearHasValues()
		self.m205.clearHasValues()
		self.m301.clearHasValues()
		
	def checkCallBack(self):
		if self.hasAllValues() and self.cb is not None:
			callback = self.cb
			self.cb = None
			callback()

	def hasAllValues(self):
		return self.m92.hasValues and self.m203.hasValues and self.m201.hasValues and self.m204.hasValues and self.m205.hasValues and self.m301.hasValues
		
	def parseM92(self, gl):
		x = get_float(gl, "X")
		y = get_float(gl, "Y")
		z = get_float(gl, "Z")
		e = get_float(gl, "E")
		self.m92.setStepsPerUnit(x, y, z, e)
		self.checkCallBack()
		
	def parseM203(self, gl):
		x = get_float(gl, "X")
		y = get_float(gl, "Y")
		z = get_float(gl, "Z")
		e = get_float(gl, "E")
		self.m203.setMaxFeedRates(x, y, z, e)
		self.checkCallBack()
		
	def parseM201(self, gl):
		x = get_float(gl, "X")
		y = get_float(gl, "Y")
		z = get_float(gl, "Z")
		e = get_float(gl, "E")
		self.m201.setMaxAccel(x, y, z, e)
		self.checkCallBack()
		
	def parseM204(self, gl):
		p = get_float(gl, "P")
		r = get_float(gl, "R")
		t = get_float(gl, "T")
		self.m204.setAcceleration(p, r, t)
		self.checkCallBack()
		
	def parseM205(self, gl):
		s = get_float(gl, "S")
		t = get_float(gl, "T")
		b = get_float(gl, "B")
		x = get_float(gl, "X")
		z = get_float(gl, "Z")
		e = get_float(gl, "E")
		self.m205.setValues(s, t, b, x, z, e)
		self.checkCallBack()
		
	def parseM301(self, gl):
		p = get_float(gl, "P")
		i = get_float(gl, "I")
		d = get_float(gl, "D")
		c = get_float(gl, "C")
		l = get_float(gl, "L")
		self.m301.setPID(p, i, d, c, l)
		try:
			self.checkCallBack()
		except Exception as e:
			print ("exception (%s)" % str(e))
		



# Recv (Home offset (mm):)
# Recv (M206 X0.00 Y0.00 Z0.00)
# Recv (Mesh bed leveling:)
# Recv (M420 S0 X3 Y3)
# Recv (M421 X10.00 Y10.00 Z0.00)
# Recv (M421 X100.00 Y10.00 Z0.00)
# Recv (M421 X190.00 Y10.00 Z0.00)
# Recv (M421 X10.00 Y100.00 Z0.00)
# Recv (M421 X100.00 Y100.00 Z0.00)
# Recv (M421 X190.00 Y100.00 Z0.00)
# Recv (M421 X10.00 Y190.00 Z0.00)
# Recv (M421 X100.00 Y190.00 Z0.00)
# Recv (M421 X190.00 Y190.00 Z0.00)
# Recv (Material heatup parameters:)
# Recv (M145 S0 H180 B60 F0)
# Recv (M145 S1 H230 B110 F0)
# Recv (Filament settings: Disabled)
# Recv (M200 D3.00)
# Recv (M200 D0)
		
