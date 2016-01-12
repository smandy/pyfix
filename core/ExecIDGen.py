# $Header: /Users/andy/cvs/dev/python/pyfix/core/ExecIDGen.py,v 1.3 2009-01-10 01:55:50 andy Exp $ 

from datetime import datetime

class ExecIDGen(object):
    def __init__(self, prefix="TEST"):
        self.idBase = 0
        self.dt = datetime.now().strftime("%Y%m%d")
        self.prefix = prefix
        self.previousIds = {}

    def makeExecID(self, clOrdID):
        while 1:
            ret =  "%s_%05d_%s" % (self.dt, self.idBase, clOrdID)
            self.idBase += 1
            if not self.previousIds.has_key( ret ):
                break
        self.previousIds[ret] = None
        return ret
    
