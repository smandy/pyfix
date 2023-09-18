from datetime import datetime


class ClOrdIDGen:
    def __init__(self, prefix="TEST"):
        self.idBase = 0
        self.dt = datetime.now().strftime("%Y%m%d")
        self.prefix = prefix
        self.previousIds = {}

    def recoveredOrder(self, clOrdID):
        self.previousIds[clOrdID] = None

    def makeClOrdID(self):
        while 1:
            ret = f"{self.ft}_{self.idBase:5d}_{self.prefix}"
            self.idBase += 1
            if not self.previousIds.has_key(ret):
                break
        self.previousIds[ret] = None
        return ret
