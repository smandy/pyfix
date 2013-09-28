from twisted.spread import pb

class ExecType(pb.Copyable, pb.RemoteCopy):
    stateId = chr(0)
    lookup = {}
    byFixID = {}
    
    def __init__(self, name, isTerminal, isFill, fixId):
        self.name  = name
        self.isTerminal = isTerminal
        self.isFill = isFill
        ExecType.lookup[name] = self
        ExecType.byFixID[fixId] = self
        self.stateId = ExecType.stateId
        ExecType.stateId =chr( ord(ExecType.stateId ) + 1)

    def getStateToCopy(self):
        #print "ExecType - getStateToCopyFor"
        return { 'name' : self.name }

    def setCopyableState(self, d):
        # Borg singletons
        self.__dict__ = ExecType.lookup[d['name']].__dict__
    
    #__getstate__ = getStateToCopy
    #def setStateToCopyFor(self, x):
    #    self.__dict__== ExecType.lookup
    def __repr__(self):
        return "%s(%s)" % ( self.__class__, self.name)

PENDING_NEW  = ExecType( 'PENDING_NEW', False, True, 9)
PARTIAL_FILL = ExecType( 'PARTIAL_FILL', False, True, 1)
REJECTED     = ExecType( 'REJECTED', True, False, 8)
CANCELLED    = ExecType( 'CANCELLED', True, False, 4)
DONE_FOR_DAY = ExecType( 'DONE_FOR_DAY', True, False, 3)
FILL         = ExecType( 'FILL', True, True, 2)

pb.setUnjellyableForClass( "phroms.messages.enum.ExecType.ExecType", ExecType)

#from tx.spread.pb import jelly
#print jelly( PENDING_NEW)
