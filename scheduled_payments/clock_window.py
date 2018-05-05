import time
import datetime

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from electroncash.i18n import _
from electroncash_gui.qt.util import MessageBoxMixin


SPEED_FAKE_SECOND_PER_REAL_SECOND = 0
SPEED_FAKE_MINUTE_PER_REAL_SECOND = 1
SPEED_FAKE_HOUR_PER_REAL_SECOND = 2
SPEED_FAKE_DAY_PER_REAL_SECOND = 3

SPEED_SETTING_LABELS = [ _("second/second"), _("minute/second"), _("hour/second"), _("day/second") ]
SPEED_SETTING_VALUES = [
    SPEED_FAKE_SECOND_PER_REAL_SECOND, 
    SPEED_FAKE_MINUTE_PER_REAL_SECOND,
    SPEED_FAKE_HOUR_PER_REAL_SECOND,
    SPEED_FAKE_DAY_PER_REAL_SECOND,
]
SPEED_SETTING_MULTIPLIERS = [
    1,
    60,
    60 * 60,
    24 * 60 * 60,    
]

class ClockWindow(QDockWidget, MessageBoxMixin):
    def __init__(self, plugin, title):
        QDockWidget.__init__(self, title)
        self.setMinimumWidth(350)        
 
        self.plugin = plugin

        widget = QWidget()
        vbox = QVBoxLayout()
        self.clockWidget = ClockWidget(_("Clock"), self.plugin.clock)
        vbox.addWidget(self.clockWidget)
        self.settingsWidget = SettingsWidget(self, _("Settings"), self.plugin.clock)
        vbox.addWidget(self.settingsWidget)
        widget.setLayout(vbox)
        
        self.setWidget(widget)
        
        self.lastThreadTime = None
        
    def closeEvent(self, event):
        if self.plugin.clock.isRealTime() or self.question(_("The real-time clock will be re-enabled when this window is closed."), title=_("Fake clock active")):
            self.plugin.on_clock_window_closed(self)
            event.accept()
        else:
            event.ignore()
            
    def onFakeClockStarted(self, flag, multiplier=1):
        if flag:
            self.lastThreadTime = time.time()
            self.speedMultiplier = multiplier
        else:
            self.lastThreadTime = None
            self.speedMultiplier = None
            
    def onFakeClockSpeedChange(self, multiplier):
        self.speedMultiplier = multiplier
        
    def onTimeChanged(self, threadCurrentTime, clock):
        if not clock.isRealTime() and self.lastThreadTime is not None:
            clock.setTime(clock.getTime() + (threadCurrentTime - self.lastThreadTime) * self.speedMultiplier)
            self.lastThreadTime = threadCurrentTime
        self.clockWidget.updateTime(clock)
        
        
class ClockWidget(QGroupBox):
    def __init__(self, text, clock):
        QGroupBox.__init__(self, text)
        
        vbox = QVBoxLayout()
        self.timeText = QLabel(self.getTimeText(clock.getTime()))
        self.timeText.setTextFormat(Qt.RichText)
        self.timeText.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.timeText)
     
        self.setLayout(vbox)
        
    def getTimeText(self, currentTime):
        return datetime.datetime.fromtimestamp(currentTime).strftime("%c")
     
    def updateTime(self, clock):
        newTime = clock.getTime()
        if clock.isRealTime():
            clockTypeText = "<b>Real-time</b>"
        else:
            clockTypeText = "<b>Fake-time</b>"
        self.timeText.setText(clockTypeText +" = "+ self.getTimeText(newTime))

FAKE_CLOCK_PAUSED = 1
FAKE_CLOCK_RUNNING = 2
        
class SettingsWidget(QGroupBox):
    def __init__(self, window, text, clock):
        self.window = window
        self.fakeClockState = FAKE_CLOCK_PAUSED
        self.requireDurationToRun = False
    
        QGroupBox.__init__(self, text)
        
        vbox = QVBoxLayout()
        self.setLayout(vbox)
        
        self.realTimeCheckBox = QCheckBox(_("Override real-time clock with fake clock"))
        self.realTimeCheckBox.stateChanged.connect(self.onRealTimeStateChange)
        self.realTimeCheckBox.setToolTip(_("The fake clock gives you direct control over the passing of time, whether to pause it, or to make it pass at a faster rate."))
        vbox.addWidget(self.realTimeCheckBox)
        
        fakeControlGroup = QGroupBox(_("Fake clock controls"))
        hbox = QHBoxLayout()

        if self.requireDurationToRun:
            unusedText = _("This is not currently used, just set it to anything to be able to run.")
            
            self.daySpinBox = QSpinBox()
            self.daySpinBox.setMinimum(0)
            self.daySpinBox.setMaximum(356)
            self.daySpinBox.setValue(0)
            self.daySpinBox.setToolTip(unusedText)
            self.daySpinBox.valueChanged.connect(self.onFakeClockDurationChange)
            hbox.addWidget(self.daySpinBox)
            
            self.daysLabel = QLabel(_("days"))
            hbox.addWidget(self.daysLabel)

            self.hourSpinBox = QSpinBox()
            self.hourSpinBox.setMinimum(0)
            self.hourSpinBox.setMaximum(23)
            self.hourSpinBox.setValue(0)
            self.hourSpinBox.setToolTip(unusedText)
            self.hourSpinBox.valueChanged.connect(self.onFakeClockDurationChange)
            hbox.addWidget(self.hourSpinBox)
            
            self.hoursLabel = QLabel(_("hours"))
            hbox.addWidget(self.hoursLabel)

            self.minuteSpinBox = QSpinBox()
            self.minuteSpinBox.setMinimum(0)
            self.minuteSpinBox.setMaximum(59)
            self.minuteSpinBox.setValue(0)
            self.minuteSpinBox.setToolTip(unusedText)
            self.minuteSpinBox.valueChanged.connect(self.onFakeClockDurationChange)
            hbox.addWidget(self.minuteSpinBox)
            
            self.minutesLabel = QLabel(_("minutes"))
            hbox.addWidget(self.minutesLabel)
        
        helpText = _('Fake clock speed.') + '\n\n' +\
            _('How much the fake clock is sped up:') +'\n' +\
            _("s/s = one second of fake time per second of real time.") +'\n' +\
            _("m/s = one minute of fake time per second of real time.") +'\n' +\
            _("h/s = one hour of fake time per second of real time.") +'\n' +\
            _("d/s = one day of fake time per second of real time.") +'\n'
            
        self.speedComboBox = QComboBox()
        self.speedComboBox.addItems(SPEED_SETTING_LABELS)
        self.speedComboBox.setToolTip(helpText)
        self.speedComboBox.currentIndexChanged.connect(self.onSpeedComboBoxChange)
        hbox.addWidget(self.speedComboBox)
        
        self.speedLabel = QLabel(_('speed'))
        hbox.addWidget(self.speedLabel)
                        
        self.runButton = QPushButton("\u25b6")
        self.runButton.setMaximumWidth(30)
        self.runButton.setToolTip(_("Run the fake clock at accelerated speed")) # (not) for the set duration
        self.runButton.pressed.connect(self.onFakeClockRunButtonClicked)
        hbox.addWidget(self.runButton)
        
        self.pauseButton = QPushButton("\u23f8")
        self.pauseButton.setMaximumWidth(30)
        self.pauseButton.setToolTip(_("Pause the fake clock"))
        self.pauseButton.pressed.connect(self.onFakeClockPauseButtonClicked)
        hbox.addWidget(self.pauseButton)
                
        fakeControlGroup.setLayout(hbox)
        vbox.addWidget(fakeControlGroup)

        if not clock.isRealTime():
            self.realTimeCheckBox.setChecked(Qt.Checked)
            self.updateFakeClockControls(True)
        else:
            self.updateFakeClockControls(False)
            
    def onSpeedComboBoxChange(self, newIndex):
        self.window.onFakeClockSpeedChange(self.getFakeClockSpeedMultiplier(newIndex))
            
    def onRealTimeStateChange(self, newState):
        self.fakeClockState = FAKE_CLOCK_PAUSED
        
        if newState == Qt.Checked:
            self.window.plugin.change_clock(real=False)
            self.updateFakeClockControls(True)
        else:
            self.window.plugin.change_clock(real=True)
            self.updateFakeClockControls(False)
            
    def onFakeClockDurationChange(self, newValue):
        self.updateFakeClockControls(True)
            
    def onFakeClockRunButtonClicked(self):
        self.fakeClockState = FAKE_CLOCK_RUNNING
        
        self.updateFakeClockControls(True)
        self.window.onFakeClockStarted(True, self.getFakeClockSpeedMultiplier(self.speedComboBox.currentIndex()))
        
    def onFakeClockPauseButtonClicked(self):
        self.fakeClockState = FAKE_CLOCK_PAUSED
        
        self.updateFakeClockControls(True)
        self.window.onFakeClockStarted(False)
        
    def getFakeClockSpeedMultiplier(self, value):
        return SPEED_SETTING_MULTIPLIERS[value]
            
    def updateFakeClockControls(self, enabled=True):
        if self.requireDurationToRun:
            self.daysLabel.setEnabled(enabled)
            self.daySpinBox.setEnabled(enabled and self.fakeClockState == FAKE_CLOCK_PAUSED)
            
            self.hoursLabel.setEnabled(enabled)
            self.hourSpinBox.setEnabled(enabled and self.fakeClockState == FAKE_CLOCK_PAUSED)
            
            self.minutesLabel.setEnabled(enabled)
            self.minuteSpinBox.setEnabled(enabled and self.fakeClockState == FAKE_CLOCK_PAUSED)
        
        self.speedLabel.setEnabled(enabled)
        self.speedComboBox.setEnabled(enabled)        
        
        runButtonEnabled = enabled and self.fakeClockState == FAKE_CLOCK_PAUSED
        if runButtonEnabled and self.requireDurationToRun:
            runButtonEnabled = self.daySpinBoxdaySpinBox.value() > 0 or self.hourSpinBox.value() > 0 or self.minuteSpinBox.value() > 0
        self.runButton.setEnabled(runButtonEnabled)
        self.pauseButton.setEnabled(enabled and self.fakeClockState == FAKE_CLOCK_RUNNING)

