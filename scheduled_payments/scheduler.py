import time
import datetime

from PyQt5.QtCore import *

# Work around stupid Python packaging import limitations for standalone testing.
try:
    from . import when as when_module
except:
    import when as when_module


class ClockInterface:
    def __init__(self):
        pass
        
    def isRealTime(self):
        return False

    def getTime(self) -> float:
        raise NotImplementedError
        
    def setTime(self, value: float):
        raise NotImplementedError
        
class RealClock(ClockInterface):
    def isRealTime(self):
        return True
        
    def getTime(self) -> float:
        return time.time()

class FakeClock(ClockInterface):
    def __init__(self, currentTime):
        self.currentTime = currentTime
        
    def setTime(self, value: float):
        self.currentTime = value

    def getTime(self) -> float:
        return self.currentTime


class WhenEstimator:
    """
    Given a point in time to work from, this estimates the next times after that initial point in time, that the abstract when will occur.
    """

    def __init__(self, startTime, when):
        self.startSecsSinceEpoch = int(startTime)
        # print("WhenEstimator", self.startSecsSinceEpoch, when)
        self.when = when

    def getNextOccurrences(self, maxMatches=1, maxTime=None):
        startDateTime = QDateTime()
        startDateTime.setSecsSinceEpoch(self.startSecsSinceEpoch)
        
        # When checking is the first date is correct, if it that day (weekday or monthday) then skip if time has passed.
        # When checking for subsequent dates, just need to search forward.
        # That's the difference between finding the first date, and finding the next date, as the time is only relevant on the first 
        
        matches = []
        whenTime = QTime(self.when.hour, self.when.minute)
        fixedTime = startDateTime.time()
        lastPythonTime = self.startSecsSinceEpoch
        while maxMatches is None or maxMatches > len(matches):
            workingDate = startDateTime.date()
            if self.when.weekDay is not None:
                currentDayOfWeek = workingDate.dayOfWeek()
                if currentDayOfWeek == self.when.weekDay:
                    # If the time on the start date has passed, then it will be a week later.
                    if len(matches) or fixedTime.hour() > self.when.hour or fixedTime.hour() == self.when.hour and fixedTime.minute() >= self.when.minute:
                        workingDate = workingDate.addDays(7)
                # Lazily work out where the next matching day of the week falls.
                while workingDate.dayOfWeek() != self.when.weekDay:
                    workingDate = workingDate.addDays(1)
            elif self.when.monthDay is not None:
                if workingDate.day() == self.when.monthDay:
                    # If the time on the start date has passed, then it will be a week later.
                    if len(matches) or fixedTime.hour() > self.when.hour or fixedTime.hour() == self.when.hour and fixedTime.minute() >= self.when.minute:
                        workingDate = workingDate.addMonths(1)
                # Lazily work out where the next matching month day falls.  This will work correctly in skipping a month, if there are not enough days in that month.
                while workingDate.day() != self.when.monthDay:
                    workingDate = workingDate.addDays(1)
        
            newDateTime = QDateTime(startDateTime)
            newDateTime.setDate(workingDate)
            newDateTime.setTime(whenTime)
            lastPythonTime = newDateTime.toSecsSinceEpoch()
            if maxTime is not None and lastPythonTime > maxTime:
                break            
            matches.append(lastPythonTime)
            startDateTime = newDateTime
            
        return matches
        
def roundTimeSeconds(secondsSinceEpoch):
    startDateTime = QDateTime()
    startDateTime.setSecsSinceEpoch(secondsSinceEpoch)
    
    startTime = startDateTime.time()
    startTime.setHMS(startTime.hour(), startTime.minute(), 1, 0)
    
    startDateTime.setTime(startTime)
    return startDateTime.toSecsSinceEpoch()
    
    
        
if __name__ == "__main__":
    # Unit tests
    # - If it is the same day and the when time is before, then stay on same day.
    # - If it is the same day and the when time is after, then skip this day and move to the next suitable one.
    # - If the month day does not exist in all months, this will mean that those non-matching months are skipped.

    startTime = time.time()

    when = when_module.When()
    when.weekDay = 4 # Monday, 10:20 AM
    when.hour = 10
    when.minute = 20

    wp = WhenEstimator(startTime, when)
    l = wp.getNextOccurrences(5)

    for v in l:
        print(datetime.datetime.fromtimestamp(v).strftime("%c"))
        
    print()

    when = when_module.When()
    when.monthDay = 31 # 3rd, 10:20 AM
    when.hour = 10
    when.minute = 20

    wp = WhenEstimator(startTime, when)
    l = wp.getNextOccurrences(5)

    for v in l:
        print(datetime.datetime.fromtimestamp(v).strftime("%c"))

    roundStartTime = roundTimeSeconds(startTime)
    print(roundStartTime, datetime.datetime.fromtimestamp(roundStartTime).strftime("%c"))
    
