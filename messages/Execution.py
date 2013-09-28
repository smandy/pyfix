from twisted.spread import pb, jelly

class Execution(pb.Copyable, pb.RemoteCopy ):
    version = 1
    def __init__(self,
                 execType    = None,
                 execID      = None,
                 clOrdID     = None,
                 side        = None,
                 lastShares  = None,
                 security    = None,
                 lastPx      = None):
        self.execType = execType
        self.clOrdID  = clOrdID
        self.execID   = execID
        self.side     = side
        self.lastShares      = lastShares
        self.security = security
        self.lastPx       = lastPx

    def __repr__(self):
        return "Execution: %s %s %s@%s" % ( self.clOrdID, self.security, self.lastShares, self.lastPx)

jelly.setUnjellyableForClass( 'phroms.messages.Execution.Execution', Execution)
pb.setCopierForClass( 'phroms.messages.Execution.Execution', Execution)

