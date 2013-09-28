

from datetime import datetime

class Clock:
    """Start as we mean to go on, with iocc hopefully will be able to put
       symclocks etc into this thing. How the &#^%*# can I get this to work with reactors?
       """
    def __init__(self):
        pass

    def getTime(self):
        return datetime.now()
