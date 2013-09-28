from twisted.spread import pb

class PositionManager(pb.Copyable, pb.RemoteCopy):
    def __init__(self):
        self.positionsByTicker = {}

    def getStateToCopyFor(self, _): # Copying for who?
        #print "GetStateToCopyFor passed %s" % str(x)
        return { 'positionsByTicker'  : self.positionsByTicker }

    #def setCopyableState(self, x):
    # TODO - fill this in!!

    def setOrderManager(self,om):
        self.om = om
        
    def setFillListener(self, fl):
        print "Pm setfilllistener %s" % fl
        fl.add( self.onFill)
        print fl.listeners

    # Ignore sender
    def onFill(self, _, tup): 
        #print "pm OnFill %s %s" % (obj, tup)
        orderState, execution = tup
        if not self.positionsByTicker.has_key(execution.security):
            pos = Position(execution.security)
            self.positionsByTicker[execution.security]=pos
        else:
            pos = self.positionsByTicker[execution.security]
        pos.apply(execution)
        #self.dumpPositions()

    def dumpPositions(self):
        for q,v in self.positionsByTicker.items():
            print "Pos : %s %s %s" % (v.security, v.qty, v.avgPx() )
 
class Position(pb.Copyable,pb.RemoteCopy):
    def __init__(self, security):
        self.security = security
        self.qty = 0
        self.volume = 0.0

    def apply(self, execution):
        assert execution.lastShares!=0
        absQty = execution.side.ordinal * execution.lastShares
        self.qty    += absQty
        self.volume += absQty * execution.lastPx

    def avgPx(self):
        if self.qty==0:
            return 0.0
        else:
            return self.volume / self.qty

    def __repr__(self):
        ret = "Position(%s,%s @ %s)" % (self.qty, self.security, self.avgPx())
        return ret
        
pb.setUnjellyableForClass(PositionManager,PositionManager)
pb.setUnjellyableForClass(Position,Position)


        
        

        

        
        
    
