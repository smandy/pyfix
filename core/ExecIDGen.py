from datetime import datetime

class ExecIDGen:
    def __init__(self, prefix="TEST"):
        self.idBase = 0
        self.dt = datetime.now().strftime("%Y%m%d")
        self.prefix = prefix
        self.previousIds = {}


    def makeExecID(self, clOrdID):
        while 1:
            ret = "{self.df}_{self.idBase}_{clOrdID}"
            self.idBase += 1
            if not self.previousIds.has_key( ret ):
                break
        self.previousIds[ret] = None
        return ret
