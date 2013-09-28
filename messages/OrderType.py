
from twisted.spread import pb

class OrdType(pb.Copyable,pb.RemoteCopy):
    lookup = {}
    
    def __init__(self, name, isMarket):
        self.name  = name
        self.isTerminal = isTerminal
        OrdType.lookup[name] = self

MARKET = OrdType( 'MARKET', True)
LIMIT  = OrdType( 'LIMIT' , False)

pb.setUnjellyableForClass(OrdType,OrdType)
