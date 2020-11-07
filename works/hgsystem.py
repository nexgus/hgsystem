from datetime import date
from datetime import datetime

###################################################################################################
VER_MAJOR = 0
VER_MINOR = 1
VER_PATCH = 1
VER_STRING = f"{VER_MAJOR}.{VER_MINOR}.{VER_PATCH}"

YearTaiwan = 0
YearCommon = 1
YearNone = 9996

###################################################################################################
def toROCYear(year):
    """Convert input year to ROC year."""
    y = year - 1911
    if y <= 0: y -= 1
    return y

###################################################################################################
def toPythonDatetime(s):
    """Convert ROC date string to a Python datetime.datetime instance."""
    x = s.split("/")
    if x.count("/") == 1:
        y = YearNone
        m = int(x[0])
        d = int(x[1])
    else:
        y = toCommonYear(int(x[0]))
        m = int(x[1])
        d = int(x[2])
    if m == 0 or d == 0: return None
    return datetime(y, m, d)

###################################################################################################
def toCommonYear(year):
    """Convert input year to Common Year (西元)."""
    if year == 0: return YearNone
    if year > 0: return year + 1911
    if year < 0: return year + 1912

###################################################################################################
def toROCDateString(dt):
    """Convert a Pythn datetime object to ROC date string."""
    if dt is None: return "0/00/00"
    if dt.year == YearNone:
        return f"{dt.month:02d}/{dt.day:02d}"
    else:
        return f"{toROCYear(dt.year)}/{dt.month:02d}/{dt.day:02d}"

###################################################################################################
class EditMode(object):
    none = 0
    append = 1
    modify = 2
    inhibit = 3
    editing = {inhibit: False, none: False, append: True, modify: True}
    color = {
        none:    'black',
        append:  'red',
        modify:  'red',
        inhibit: 'black',
        True:    'red',
        False:   'black'
    }

    @staticmethod
    def inRange(mode):
        if mode in (EditMode.none, EditMode.append, EditMode.modify, EditMode.inhibit):
            return True
        else:
            return False

    @staticmethod
    def stylesheetQLineEdit(mode):
        return 'QLineEdit {{color: {}; background: white;}}'.format(EditMode.color[mode])

###################################################################################################
def taiwanDateStringToPythonDate(dateString):
    year, month, day = dateString.split('/')
    return date(int(year)+1911, int(month), int(day))

###################################################################################################
def pythonDateToTaiwainDateString(dt):
    year  = dt.year - 1911
    month = dt.month
    day   = dt.day
    if year < 1: year = year - 1
    return '{}/{:02d}/{:02d}'.format(year, month, day)
