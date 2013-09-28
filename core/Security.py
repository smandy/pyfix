from twisted.spread import pb

class Security(pb.Copyable, pb.RemoteCopy):
    def __init__(self):
        self.ticker = None
    
    def __repr__(self):
        return "Security(%s)" % self.ticker

pb.setUnjellyableForClass( Security, Security)
