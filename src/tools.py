secpday = 60 * 60 * 24
secphour = 60 * 60


def formatElapsed(secs):
    ndays = int(secs / secpday)
    secday = secs % secpday

    nhour = int(secday / secphour)
    sechour = secday % secphour

    nmin = int(sechour / 60)
    nsec = sechour % 60

    if ndays == 0:
        if nhour == 0:
            return "%d:%02d" % (nmin, nsec)
        else:
            return "%d:%02d:%02d" % (nhour, nmin, nsec)
    else:
        return "%d-%d:%02d:%02d" % (ndays, nhour, nmin, nsec)


def approximateValue(n):
    if n <= 10240:
        return "%d" % n

    if n <= (1048576):
        return "{:,.2f}".format(n / 1024.0) + " K"

    return '{:,.2f}'.format(n / (1048576.0)) + " M"
