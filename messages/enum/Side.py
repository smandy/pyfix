from twisted.spread import pb

class Side(pb.Copyable, pb.RemoteCopy):
    lookup = {}
    byFixID = {}
    
    def __init__(self,name, ordinal, fixID):
        self.name = name
        self.ordinal = ordinal
        self.fixID = fixID
        Side.lookup[name] = self
        Side.byFixID[fixID] = self

    def __int__(self):
        return self.ordinal

    def __repr__(self):
        return self.name
    
BUY  = Side('BUY',  1, 1)
SELL = Side('SELL',-1, 2)

pb.setUnjellyableForClass( Side, Side)

if __name__=='__main__':
    print 10 * int(BUY)
    print Side.lookup


