from twisted.spread import pb

class OrderState(pb.Copyable,pb.RemoteCopy):
    def __init__(self, order ):
        self.order = order
        self.cumQty  = 0
        self.volume  = 0
        self.portfolios = []

    def apply(self, execution):
        assert execution.clOrdID == self.order.clOrdID
        assert int(execution.side)==int(self.order.side)
        if execution.execType.isFill:
            self.cumQty += execution.lastShares
            self.volume += execution.lastShares * execution.lastPx
            self.orderState = execution.execType
        else:
            print "Non fill exec"

    def setPortfolios(self, portfolios):
        #print "OrderState.setPortfolios %s %s" % (self, str(self.portfolios))
        self.portfolios = portfolios

    def getStateToCopy(self):
        #print "GetStateToCopy has been called"
        d = self.__dict__
        #print self.portfolios
        if self.portfolios and type(self.portfolios[0] )==int:
            d['portfolios'] = [ x.idx for x in self.portfolios ]
        return d

    def getStateToCopyFor(self, _):
        #print "GetStateToCopyFor has been called - deferring to getStateToCopy"
        return self.getStateToCopy()

    def isTerminal(self):
        return self.orderState.isTerminal

    def avgPx(self):
        if self.volume==0:
            return 0.0
        else:
            return self.volume / self.cumQty

    def __repr__(self):
        #return "OrderState: %s ( %s @ %s ) portfolios=%s" % (self.order, self.cumQty, self.avgPx(), str(self.portfolios ))
        return "OrderState: %s ( %s @ %s )" % (self.order, self.cumQty, self.avgPx() )

pb.setUnjellyableForClass(OrderState,OrderState)
#pb.setUnjellyableForClass(pyfix.util.OrderState,pyfix.util.OrderState)
