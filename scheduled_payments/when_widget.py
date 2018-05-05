import time
import datetime

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from electroncash.i18n import _

from .when import When
from . import scheduler

# This is aligned with QDate days of the week, but note that it's 1-based.
DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

class WhenWidget(QGroupBox):
    def __init__(self, text):
        QGroupBox.__init__(self, text)
        
        self.estimatedTime = None
        
        topRadioLayout = QVBoxLayout()

        self.weeklyRadioButton = QRadioButton(_("Weekly"))
        self.weeklyRadioButton.setChecked(True)
        def fw(is_checked):
            if is_checked:
                self.activateWeeklySection(is_checked)
            else:
                self.activateMonthlySection(is_checked)
        self.weeklyRadioButton.clicked.connect(fw)
        topRadioLayout.addWidget(self.weeklyRadioButton)

        def onDayToggled(isChecked):
            if isChecked:
                self.updateEstimatedTime()
        def onSpinBoxChanged(newValue):
            self.updateEstimatedTime()
        
        self.weeklyGroupBox = QGroupBox()
        weeklyRadioLayout = QHBoxLayout()
        self.weeklyDaysLabel = QLabel(_("On"))
        weeklyRadioLayout.addWidget(self.weeklyDaysLabel)
        self.dayRadioButtons = []
        for i, dayName in enumerate(DAY_NAMES):
            radioButton = QRadioButton(_(dayName))
            if i == 0:
                radioButton.setChecked(True)
            weeklyRadioLayout.addWidget(radioButton)
            self.dayRadioButtons.append(radioButton)
            radioButton.toggled.connect(onDayToggled)
        self.weeklyGroupBox.setLayout(weeklyRadioLayout)
        def wf(*args):
            print("wg", args)
        self.weeklyGroupBox.toggled.connect(wf)

        topRadioLayout.addWidget(self.weeklyGroupBox)
                
        self.monthlyRadioButton = QRadioButton(_("Monthly"))
        def fm(is_checked):
            if is_checked:
                self.activateMonthlySection(is_checked)
            else:
                self.activateWeeklySection(is_checked)
        self.monthlyRadioButton.clicked.connect(fm)
        topRadioLayout.addWidget(self.monthlyRadioButton)
        monthlyGroupBox = QGroupBox()
        monthlyGroupLayout = QHBoxLayout()
        self.monthlyDayCombo = QSpinBox()
        self.monthlyDayCombo.setMaximumWidth(40)
        self.monthlyDayCombo.setMinimum(1)
        self.monthlyDayCombo.setMaximum(31)
        self.monthlyDayCombo.setValue(1)
        self.monthlyDayCombo.valueChanged.connect(onSpinBoxChanged)
        self.monthlyDayLabel = QLabel(_('On day'))
        monthlyGroupLayout.addWidget(self.monthlyDayLabel)
        monthlyGroupLayout.addWidget(self.monthlyDayCombo)
        monthlyGroupBox.setLayout(monthlyGroupLayout)
        topRadioLayout.addWidget(monthlyGroupBox)

        timeGroupBox = QGroupBox()
        timeGroupLayout = QHBoxLayout()
        self.timeLabel = QLabel(_('At time'))
        timeGroupLayout.addWidget(self.timeLabel)
        self.timeHourCombo = QSpinBox()
        self.timeHourCombo.setMinimum(0)
        self.timeHourCombo.setMaximum(23)
        self.timeHourCombo.setValue(0)
        self.timeHourCombo.setMaximumWidth(40)
        self.timeHourCombo.valueChanged.connect(onSpinBoxChanged)
        timeGroupLayout.addWidget(self.timeHourCombo)
        self.timeMinuteCombo = QSpinBox()
        self.timeMinuteCombo.setMinimum(0)
        self.timeMinuteCombo.setMaximum(59)
        self.timeMinuteCombo.setValue(0)
        self.timeMinuteCombo.setMaximumWidth(40)
        self.timeMinuteCombo.valueChanged.connect(onSpinBoxChanged)
        timeGroupLayout.addWidget(self.timeMinuteCombo)
        timeGroupBox.setLayout(timeGroupLayout)
        topRadioLayout.addWidget(timeGroupBox)
        
        projectionGroupBox = QGroupBox()
        projectionGroupLayout = QHBoxLayout()
        self.projectionLabel = QLabel(_('Next matching date'))
        projectionGroupLayout.addWidget(self.projectionLabel)
        projectionGroupLayout.addStretch(1)
        self.projectionEstimateLabel = QLabel("...")
        projectionGroupLayout.addWidget(self.projectionEstimateLabel)
        projectionGroupBox.setLayout(projectionGroupLayout)
        topRadioLayout.addWidget(projectionGroupBox)
                
        self.setLayout(topRadioLayout)
        
    def activateWeeklySection(self, isActive):
        if isActive:
            self.monthlyRadioButton.setChecked(False)
        else:
            self.weeklyRadioButton.setChecked(True)

        self.weeklyDaysLabel.setDisabled(False)
        for button in self.dayRadioButtons:
            button.setDisabled(False)
            
        self.monthlyDayLabel.setDisabled(True)
        self.monthlyDayCombo.setDisabled(True)

        self.updateEstimatedTime()
        
    def activateMonthlySection(self, isActive):
        if isActive:
            self.weeklyRadioButton.setChecked(False)
        else:
            self.monthlyRadioButton.setChecked(True)
            
        self.weeklyDaysLabel.setDisabled(True)
        for button in self.dayRadioButtons:
            button.setDisabled(True)

        self.monthlyDayLabel.setDisabled(False)
        self.monthlyDayCombo.setDisabled(False)

        self.updateEstimatedTime()
        
    def getWhen(self):
        when = When()

        if self.weeklyRadioButton.isChecked():
            for i, v in enumerate(self.dayRadioButtons):
                if v.isChecked():
                    when.setWeekDay(i+1)
                    break
        elif self.monthlyRadioButton.isChecked():
            when.setMonthDay(self.monthlyDayCombo.value())
            
        hour = self.timeHourCombo.value()
        minute = self.timeMinuteCombo.value()
        when.setTime(hour, minute)
        
        return when
        
    def setWhen(self, when):
        if type(when) is str:
            when = When.fromText(when)        

        if when is not None and when.weekDay is not None:
            self.weeklyRadioButton.setChecked(True)
            self.activateWeeklySection(False)
            self.dayRadioButtons[when.weekDay-1].setChecked(True)
        elif when is not None and when.monthDay is not None:
            self.monthlyRadioButton.setChecked(True)
            self.activateMonthlySection(False)
            self.monthlyDayCombo.setValue(when.monthDay)
        else:
            self.weeklyRadioButton.setChecked(True)
            self.activateWeeklySection(False)
            when = self.getWhen()
        
        self.timeHourCombo.setValue(when.hour)
        self.timeMinuteCombo.setValue(when.minute)

        self.updateEstimatedTime(when)
    
    def updateEstimatedTime(self, when=None, currentTime=None):
        if when is None:
            when = self.getWhen()
        if currentTime is None:
            currentTime = time.time()
        p = scheduler.WhenEstimator(currentTime, when)
        matches = p.getNextOccurrences(1)
        newEstimatedTime = matches[0]
        if newEstimatedTime != self.estimatedTime:
            self.estimatedTime = newEstimatedTime
            self.projectionEstimateLabel.setText(datetime.datetime.fromtimestamp(self.estimatedTime).strftime("%c"))
            return True
        return False

    def getEstimatedTime(self):
        return self.estimatedTime

