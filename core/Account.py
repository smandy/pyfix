from twisted.spread import pb

class Account(pb.Copyable, pb.RemoteCopy):

    def __init__(self):
        self.name = None
    
    def __repr__(self):
        return "Account(%s)" % self.name

pb.setUnjellyableForClass( Account, Account ) 
