from time import sleep, sleep_ms, time, gmtime, mktime
from utils import FileManager, log, timeStr, clockStr, roundedStr, dateStr, isLeapYear, timeToDate


class Alarm(FileManager):
    
    alarm_list = [(True, time()+20,  0)]

    def __init__(self, active, time, repeat, weekday="1111111", snooze=1, snoozetime=7, sound=0, rfid=0):
        self.active     = active
        self.time       = time
        self.repeat     = repeat
        self.weekday    = weekday
        self.snooze     = snooze
        self.snoozetime = snoozetime
        self.sound      = sound
        self.rfid       = rfid

    def __str__(self):
        attributes_order = [
            self.active,
            self.time,
            self.repeat,
            self.weekday,
            self.snooze,
            self.snoozetime,
            self.sound,
            self.rfid
        ]
        return ', '.join([f"{value}" for value in attributes_order])

    def check(self):
        if self.repeat == -1 and not self.active:
            return None
        else:
            checkActive  = self.active == True
            checkTime    = self.time <= time() and self.time+120 >= time()
            #checkWeekDay = self.weekday[gmtime()[6]] == "1"
            alarmTrigger = checkActive and checkTime
            return alarmTrigger
        
    def setNextTrigger(self):
        self.active = False if self.repeat == 0 or self.repeat == -1 else self.active
        if self.repeat == 1:
            for i in range(1, 8):
                nextDay = (gmtime()[6] + i) % 7
                if self.weekday[nextDay] =="1":
                    self.time +=i*24*3600
                    #self.time +=20
                    log("ALARM", f"next: {timeToDate(self.time)} at {timeStr(self.time)}")
                    break
        Alarm.setAlarmListtoJson()
    
    @staticmethod
    def _nextActiveDay(current_wday, weekday_str):
        """
        Determine the next active day based on the current weekday and the weekday string.
        """
        for i in range(7):
            next_wday = (current_wday + i) % 7
            if weekday_str[next_wday] == '1':
                return i  # Number of days to add to current day
        return None  # No active days found

    @classmethod
    def addAlarm(cls, hour, minute, repeat, weekday):
        # Current time
        now = gmtime()
        alarm_time = mktime((now[0], now[1], now[2], hour, minute, 0, now[6], now[7]))

        # Check if today is an active day and the time has not passed
        if weekday[now[6]] == '1' and alarm_time > time():
            pass  # Alarm is set for today
        else:
            # Find the next active day
            days_to_add = cls._nextActiveDay(now[6], weekday)
            if days_to_add is not None:
                alarm_time += days_to_add * 86400  # Add the necessary days in seconds

        # Create and add the new alarm
        new_alarm = cls(True, alarm_time, repeat, weekday)
        cls.alarm_list.append(new_alarm)

        # Optional: Update the stored alarm list
        cls.setAlarmListtoJson()

    @classmethod
    def getNextAlarm(cls):
        next_alarm = None
        next_alarm_t = time()+86400  # day in seconds
        for i, alarm in enumerate(cls.alarm_list):
            checkActive = alarm.active # type: ignore
            checkTime   = alarm.time > time() # type: ignore
            checkNext   = alarm.time < next_alarm_t # type: ignore
            if checkActive and checkTime and checkNext:
                next_alarm    = i
                next_alarm_t  = alarm.time # type: ignore
        return next_alarm
    
    @classmethod
    def getAlarmListfromJson(cls):
        cls.alarm_list = cls.from_json()
        return cls.alarm_list
    
    @classmethod
    def setAlarmListtoJson(cls, alarm_list = None):
        if alarm_list is None:
            alarm_list = cls.alarm_list
        cls.to_json(alarm_list)