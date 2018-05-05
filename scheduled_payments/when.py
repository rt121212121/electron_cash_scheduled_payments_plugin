


class When:
    def __init__(self):
        self.monthDay = None
        self.weekDay = None
        self.hour = 0
        self.minute = 0
        
    def __repr__(self):
        if self.monthDay is None and self.weekDay is None:
            import traceback
            traceback.print_stack()
        return "<When monthDay=%s weekDay=%s hour=%d minute=%d>" % (self.monthDay, self.weekDay, self.hour, self.minute)
        
    def setMonthDay(self, value):
        self.monthDay = value
        
    def setWeekDay(self, value):
        self.weekDay = value
        
    def setTime(self, hour, minute):
        self.hour, self.minute = hour, minute
        
    def isSame(self, otherWhen):
        return otherWhen is not None and self.monthDay == otherWhen.monthDay and self.weekDay == otherWhen.weekDay and self.hour == otherWhen.hour and self.minute == otherWhen.minute
 
    def toText(self):
        whenText = ""
        if self.weekDay is not None:
            whenText = "WEEKDAY-"+ str(self.weekDay)
        elif self.monthDay is not None:
            whenText = "MONTHDAY-"+ str(self.monthDay)
            
        if len(whenText):
            whenText += " TIME-%02d:%02d" % (self.hour, self.minute)        
        return whenText

    @classmethod
    def fromText(class_, whenText):
        when = class_()

        if whenText:
            sections = whenText.split(" ")
            for section in sections:
                if section.startswith("WEEKDAY-"):
                    day = int(section[8:])
                    when.setWeekDay(day)
                elif section.startswith("MONTHDAY-"):
                    day = int(section[9:])
                    when.setMonthDay(day)
                elif section.startswith("TIME-"):
                    time_string = section[5:]
                    time_values = [ int(v) for v in time_string.split(":") ]
                    if len(time_values) == 2:
                        when.setTime(*time_values)
    
        return when
