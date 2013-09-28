from phroms.core.PositionManager import PositionManager
from twisted.spread import pb
#class PortfolioManager:
#    def __init__(self):
#        self.portfolioByName = {}#
#
#    def addPortfolio(self, p):
#        self.portfilioByName[p.name] = p

class Bucketer:
    # A bucketer returns an identifier for a given order
    # idea being that orders are bucketed into meaningful
    # groups.
    def __init__(self, orderFunctor, desc):
        self.orderFunctor = orderFunctor
        self.desc = desc
        self.portfoliosByIdentifier = {}

    def portfolioForOrder(self, factory, order):
        name = self.orderFunctor(order)
        if not self.portfoliosByIdentifier.has_key( name ):
            self.portfoliosByIdentifier[name] = factory.makePortfolio( self.desc, name ) 
        return self.portfoliosByIdentifier[name]

#bySecurity = Discriminator( lambda x: x.security )
byExchange = Bucketer( lambda os: os.order.security.exchange , "EXCHANGE" )
byAccount  = Bucketer( lambda os: os.order.account           , "ACCOUNT"  )
everything = Bucketer( lambda os: "ALL"                      , "ALL"      )
        
defaultAllocators = [ byExchange, byAccount, everything ]

class PortfolioManager(pb.Copyable,pb.RemoteCopy):
    def __init__(self, allocators = defaultAllocators):
        self.allocators = allocators
        self.portfoliosById = {}
        self.nextId = 0

    def makePortfolio(self, desc, name):
        self.nextId += 1
        ret = Portfolio(self.nextId, desc, name)
        self.portfoliosById[self.nextId] = ret
        return ret

    def portfoliosForOrder(self, os):
        ret =  [ x.portfolioForOrder(self, os) for x in self.allocators ]
        return [ x for x in ret if x ]

    def setFillListener(self, fl):
        fl.add(self.onFill)
        print fl.listeners

    def onFill(self, obj, tup):
        orderState, execution = tup
        if orderState:
            for portfolio in orderState.portfolios:
                portfolio.onFill(obj, tup)
    
class Portfolio(pb.Copyable,pb.RemoteCopy):
    def __init__(self, idx, name, desc):
        self.idx = idx
        self.name = name
        self.desc = desc
        self.positionManager = PositionManager()

    def onFill(self, obj, tup):
        self.positionManager.onFill(obj, tup)

class Filterer:
    def __init__(self, criteria, portfolio):
        self.crit = criteria
        self.portfolio

    def portfolioForOrder(self, orderState):
        if self.crit( orderState):
            return self.portolio
        else:
            return None


pb.setUnjellyableForClass(PortfolioManager,PortfolioManager)
pb.setUnjellyableForClass(Portfolio,Portfolio)

