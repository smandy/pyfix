from twisted.spread import pb

class OrderState(pb.Copyable,pb.RemoteCopy):
    def __init__(self, order):
        self.order = order
        self.cumQty = 0
        self.volume = 0
        self.portfolios = []

    def apply(self, execution):
        assert execution.clOrdID == self.order.clOrdID
        assert int(execution.side) == int(self.order.side)
        if execution.execType.isFill:
            self.cumQty += execution.lastShares
            self.volume += execution.lastShares * execution.lastPx
            self.orderState = execution.execType
        else:
            print("Non fill exec")

    def setPortfolios(self, portfolios):
        self.portfolios = portfolios

    def getStateToCopy(self):
        d = self.__dict__
        if self.portfolios and isinstance(self.portfolios[0], int):
            d['portfolios'] = [x.idx for x in self.portfolios]
        return d

    def getStateToCopyFor(self, _):
        return self.getStateToCopy()

    def isTerminal(self):
        return self.orderState.isTerminal

    def avgPx(self):
        if self.volume == 0:
            return 0.0
        return self.volume / self.cumQty

    def __repr__(self):
        return f"OrderState: {self.order} ( {self.cumQty} @ {self.avgPx()}"

pb.setUnjellyableForClass(OrderState, OrderState)
