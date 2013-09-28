import traceback
import quickfix as fix

from twisted.spread import pb
from phroms.messages.enum.Side import Side
from phroms.messages.enum.ExecType import ExecType
from phroms.messages.BusinessObject import BusinessObject

fix_ExecType   = fix.ExecType()
fix_ExecID     = fix.ExecID()
fix_ClOrdID    = fix.ClOrdID()
fix_Side       = fix.Side()
fix_LastShares = fix.LastShares()
fix_Symbol     = fix.Symbol()
fix_LastPx     = fix.LastPx()

class ExecutionWrapper(pb.Copyable, pb.RemoteCopy, BusinessObject):
    version = 1
    
    def __init__(self, msg=None):
        if msg: # Need no-arg ctor for persistence
            try:
                self.execType   = ExecType.byFixID[ int(msg.getField( fix_ExecType ).getString() )]
                self.clOrdID    = msg.getField( fix_ClOrdID ).getString()
                self.execID     = msg.getField( fix_ExecID ).getString()
                self.side       = Side.byFixID[ int(msg.getField( fix_Side ).getString()) ]
                self.lastShares = int(msg.getField( fix_LastShares).getString())
                self.security   = msg.getField( fix_Symbol).getString()
                self.lastPx     = float( msg.getField( fix_LastPx ).getString() )
                self.isFill = self.lastShares>0
            except:
                print "Dodgy message : %s" % msg
                traceback.print_exc()
                raise Exception()

    def __repr__(self):
        return "ExecutionWrapper : " + " ".join( [ str(x) for x in [self.execType, self.clOrdID,self.execID, self.side, self.lastShares, self.security, self.lastPx ] ])
    
pb.setUnjellyableForClass(ExecutionWrapper, ExecutionWrapper)

    
