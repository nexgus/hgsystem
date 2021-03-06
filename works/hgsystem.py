import logging
import os

from datetime import date
from datetime import datetime
from PySide2.QtGui import QFont # pylint: disable=no-name-in-module

###################################################################################################
VER_MAJOR = 0
VER_MINOR = 5
VER_PATCH = 1
VER_EXTRA = ""
VER_STRING = f"{VER_MAJOR}.{VER_MINOR}.{VER_PATCH}{VER_EXTRA}"

"""History
0.3.0:
    1) Add a tool for extract BC data from original database.
    2) Add an update tool in main menu.
0.3.1:
    Set update message box title.
0.3.2:
    Change font of the update and about message boxes.
0.3.3:
    Add logging.
0.4.0:
    Add history search function.
0.4.1:
    Maximize GUI.
0.5.0:
    Add backup/restore function.
0.5.1:
    Fix cannnot edit worksheet.
0.5.2:
    Set icon of the windows.
0.5.3:
    Set menu icons.
"""

###################################################################################################
fonts = {
    "新細明體": "PMingLiU",
    "細明體": "MingLiU",
    "標楷體": "DFKai-SB",
    "宋體": "SimSun",
    "新宋體": "NSimSun",
    "仿宋": "FangSong",
    "楷體": "KaiTi",
    "微軟正黑體": "Microsoft JhengHei",
    "微軟雅黑體": "Microsoft YaHei",
}
FONT = QFont(fonts["微軟雅黑體"], 12, 50) 

YearTaiwan = 0
YearCommon = 1
YearNone = 9996

###################################################################################################
logger = logging.getLogger("hgsystem")
logger.setLevel(logging.DEBUG)

_logdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(_logdir, exist_ok=True)
_logfile = os.path.join(_logdir, f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.log")
#_logfmt = logging.Formatter("%(asctime)s [%(filename)s:%(lineno)d] %(levelname)s - %(message)s")
_logfmt = logging.Formatter("[%(asctime)s] %(levelname)-5.5s - %(message)s")

_fileHandler = logging.FileHandler(_logfile, encoding="utf-8")
_fileHandler.setLevel(logging.DEBUG)
_fileHandler.setFormatter(_logfmt)
logger.addHandler(_fileHandler)
logger.info("Start hgsystem.")

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
