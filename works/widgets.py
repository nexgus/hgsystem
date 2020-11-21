# pylint: disable=no-name-in-module
import hgsystem as hg

from datetime import datetime
from PySide2.QtCore import Qt
from PySide2.QtCore import QDate
from PySide2.QtCore import QEvent
from PySide2.QtCore import Signal
from PySide2.QtGui import QBrush
from PySide2.QtGui import QColor
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QComboBox
from PySide2.QtWidgets import QDialog
from PySide2.QtWidgets import QHBoxLayout
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QLineEdit
from PySide2.QtWidgets import QSpinBox
from PySide2.QtWidgets import QWidget

##############################################################################################################
class TaiwanEra(object):
    def __init__(self, year=0, month=0, day=0):
        """Create a Taiwan Year instance.

        Args:
            year (int, optional): Year of Taiwan Era. Defaults to 0.
            month (int, optional): Month of Taiwan Era. Defaults to 0.
            day (int, optional): Day of Taiwan Era. Defaults to 0.
        """
        # Use QDate since it can store 0/0/0 or 0/12/31
        self.date = QDate(self.toCommonEra(year), month, day)

    def __str__(self):
        """The method when print() is called."""
        if self.month + self.day == 0:
            return f"{self.year}/{self.month}/{self.day}"
        elif self.year == 0:
            return f"{self.month}/{self.day}"
        else:
            return f"{self.year}/{self.month}/{self.day}"

    def __repr__(self):
        """The method when the variable is called."""
        if self.month + self.day == 0:
            return f"{self.year} 年 {self.month} 月 {self.day} 日"
        elif self.year == 0:
            return f"{self.month} 月 {self.day} 日"
        elif self.year > 0:
            return f"民國 {self.year} 年 {self.month} 月 {self.day} 日"
        elif self.year < 0:
            return f"民前 {-self.year} 年 {self.month} 月 {self.day} 日"

    @staticmethod
    def toCommonEra(year):
        """Convert Taiwan Year to Common Era.

        Args:
            year (int): Taiwan year.

        Returns:
            int: Year of Common Era.
        """
        if year == 0:
            ce = 0
        elif year < 0:
            ce = year + 1912
        else:
            ce = year + 1911
        return ce

    @staticmethod
    def toTaiwanEra(year):
        """Convert Common Era to Taiwan Year.

        Args:
            year (int): Year of Common Era.

        Returns:
            int: Year of Taiwan Year.
        """
        if year == 0:
            tw = 0
        else:
            tw = year - 1911
            if tw <= 0: tw -= 1
        return tw

    @property
    def year(self):
        return self.toTaiwanEra(self.date.year())

    @property
    def month(self):
        return self.date.month()

    @property
    def day(self):
        return self.date.day()

    def toPython(self):
        try:
            ret = datetime(self.toCommonEra(self.year), self.month, self.day)
        except Exception:
            ret = None
        return ret

    def toString(self):
        return self.__str__()

##############################################################################################################
class MyDateWidget(QWidget):
    DaysPerMonth = [31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def __init__(self, year=0, month=0, day=0):
        super(MyDateWidget, self).__init__()

        font = QFont("Helvetica", 10, QFont.Bold)
        self.setFont(font)

        txtYearType = QLabel('民國')
        txtYear = QLabel('年')
        txtMonth = QLabel('月')
        txtDay = QLabel('日')

        self.edtYear = MySpinBox()
        self.edtYear.setMinimum(TaiwanEra.toTaiwanEra(1))
        self.edtYear.setMaximum(TaiwanEra.toTaiwanEra(9999))
        self.edtYear.setValue(year)
        self.edtYear.setAlignment(Qt.AlignRight)
        self.edtYear.setMinimumWidth(50)

        self.edtMonth = QComboBox()
        self.edtMonth.setMinimumWidth(50)
        self.edtMonth.setEditable(True)
        for x in range(13):
            self.edtMonth.addItem(str(x))
        self.edtMonth.setCurrentIndex(month)

        self.edtDay = QComboBox()
        self.edtDay.setMinimumWidth(50)
        self.edtDay.setEditable(True)
    
        days = self.DaysPerMonth[month]
        if days == 28:  # It must be Feb.
            if year==0 or QDate.isLeapYear(TaiwanEra.toCommonEra(year)):
                days = 29
        for x in range(days+1):
            self.edtDay.addItem(str(x))
        self.edtDay.setCurrentIndex(day)

        layout = QHBoxLayout()
        layout.addWidget(txtYearType)
        layout.addWidget(self.edtYear)
        layout.addWidget(txtYear)
        layout.addWidget(self.edtMonth)
        layout.addWidget(txtMonth)
        layout.addWidget(self.edtDay)
        layout.addWidget(txtDay)
        layout.addStretch()
        self.setLayout(layout)

        self._createConnection()

    def _createConnection(self):
        """Signal-slot connections."""
        self.edtMonth.currentIndexChanged.connect(self._setEdtDayItems)
        self.edtYear.focusOut.connect(self._setEdtDayItems)

    def _setEdtDayItems(self, dontCare=None):
        """While year/month is changed, the items in edtDay must be changed."""
        year = self.edtYear.value()
        month = self.edtMonth.currentIndex()
        day   = self.edtDay.currentIndex()
        self.edtDay.clear()

        days = self.DaysPerMonth[month]
        if days == 28:
            if year==0 or QDate.isLeapYear(TaiwanEra.toCommonEra(year)):
                days = 29

        for idx in range(days+1):
            self.edtDay.addItem(str(idx))
        if day > idx:
            self.edtDay.setCurrentIndex(idx)
        else:
            self.edtDay.setCurrentIndex(day)

    def clear(self):
        self.edtYear.setValue(0)
        self.edtMonth.setCurrentIndex(0)
        self.edtDay.setCurrentIndex(0)

    def date(self):
        year = self.edtYear.value()
        month = self.edtMonth.currentIndex()
        day = self.edtDay.currentIndex()
        if year==0:
            if month==0 and day==0:
                return None
            else:
                year = hg.YearNone
        else:
            year = hg.toCommonYear(year)
        return datetime(year, month, day)

    def dateString(self):
        return hg.toROCDateString(self.date())

    def setDate(self, year=0, month=0, day=0):
        """Set content of this object (year, month, day)

        Args:
            year (int, optional): The (ROC) year. Defaults to 0.
            month (int, optional): The month. Defaults to 0.
            day (int, optional): The day. Defaults to 0.
        """
        self.edtYear.setValue(year)
        self.edtMonth.setCurrentIndex(month)
        self.edtDay.setCurrentIndex(day)

    def setDateString(self, date):
        """Set Date string.
    
        Args:
            date (str): An ROC date string (YYY/MM/DD).
        """
        x = date.split("/")
        if date.count("/") == 1:
            year = hg.YearNone
            month = int(x[0])
            day = int(x[1])
        else:
            year = int(x[0])
            month = int(x[1])
            day = int(x[2])
        self.setDate(year, month, day)

    def setEditMode(self, mode):
        if not hg.EditMode.inRange(mode): raise ValueError('Invalid edit mode ({})'.format(mode))

        for obj in (self.edtYear, self.edtMonth, self.edtDay):
            obj.setEnabled(hg.EditMode.editing[mode])
            obj.lineEdit().setStyleSheet(hg.EditMode.stylesheetQLineEdit(mode))

    def setToday(self):
        today = QDate.currentDate()
        year  = TaiwanEra.toTaiwanEra(today.year())
        month = today.month()
        day   = today.day()
        self.setDate(year, month, day)

###################################################################################################
class MyLineEdit(QLineEdit):
    def __init__(self, *args):
        QLineEdit.__init__(self, *args)

    def event(self, event):
        if event.type()==QEvent.KeyPress and event.key()==Qt.Key_Enter:
            print("Enter key pressed")
            return True

        return QLineEdit.event(self, event)

##############################################################################################################
class MySpinBox(QSpinBox):
    focusOut = Signal()

    def focusOutEvent(self, event):
        QSpinBox.focusOutEvent(self, event)
        self.focusOut.emit()
