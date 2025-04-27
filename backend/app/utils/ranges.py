from datetime import datetime
from typing import Optional

__all__ = 'TimeRange'

class TimeRange:
    __slots__ = 'start', 'end'

    def __init__(self, start: Optional[datetime] = None, end: Optional[datetime] = None):
        self.start = start
        self.end = end

    def has(self, timestamp: datetime):
        """
        Check if a timestamp present inside a time range.
        """

        if self.start and self.start > timestamp:
            return False
        if self.end and self.end < timestamp:
            return False
        return True
    
    def bake_query(self, rule):
        """
        Dumps filter rules.
        """

        if self.start and self.end:
            return rule >= self.start, rule <= self.end
        elif self.start:
            return rule >= self.start,
        elif self.end:
            return rule <= self.end,
        else:
            return ()
        
AnyTime = TimeRange()