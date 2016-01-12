# $Header: /Users/andy/cvs/dev/python/pyfix/core/ClOrdIDGen.py,v 1.3 2009-01-05 20:44:26 andy Exp $ 

from datetime import datetime

class ClOrdIDGen(object):
    def __init__(self, prefix="TEST"):
        self.idBase = 0
        self.dt = datetime.now().strftime("%Y%m%d")
        self.prefix = prefix
        self.previousIds = {}

    def recoveredOrder( self, clOrdID):
        self.previousIds[clOrdID] = None

    def makeClOrdID(self):
        while 1:
            ret =  "%s_%05d_%s" % (self.dt, self.idBase, self.prefix)
            self.idBase += 1
            if not self.previousIds.has_key( ret ):
                break
        self.previousIds[ret] = None
        return ret
    
