secpday = 60 * 60 * 24
secphour = 60 * 60


def formatElapsed(secs):
	sign = ""
	if secs < 0:
		secs = -secs
		sign = "-"
		
	ndays = int(secs / secpday)
	secday = secs % secpday

	nhour = int(secday / secphour)
	sechour = secday % secphour

	nmin = int(sechour / 60)
	nsec = sechour % 60

	if ndays == 0:
		if nhour == 0:
			return "%s%d:%02d" % (sign, nmin, nsec)
		else:
			return "%s%d:%02d:%02d" % (sign, nhour, nmin, nsec)
	else:
		return "%s%d-%d:%02d:%02d" % (sign, ndays, nhour, nmin, nsec)


def approximateValue(n):
	if n <= 10240:
		return "%d" % n

	if n <= (1048576):
		return "{:,.2f}".format(n / 1024.0) + " K"

	return '{:,.2f}'.format(n / (1048576.0)) + " M"
