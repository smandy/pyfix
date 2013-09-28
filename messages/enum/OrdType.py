class OrdType:
    lookup = {}
    
    def __init__(self, name, isMarket):
        self.name  = name
        self.isMarket = isMarket
        OrdType.lookup[name] = self

MARKET = OrdType( 'MARKET', True  )
LIMIT  = OrdType( 'LIMIT' , False )
