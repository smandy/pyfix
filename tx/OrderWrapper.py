import traceback
import quickfix as fix

from twisted.spread import pb
from phroms.messages.enum.Side import Side
from phroms.messages.enum.ExecType import ExecType
from phroms.messages.BusinessObject import BusinessObject

from phroms.messages.Order import Order
#import phroms.messages.enum.ExecType as ExecType

fix_Symbol   = fix.Symbol()
fix_ClOrdID  = fix.ClOrdID()
fix_OrderQty = fix.OrderQty()
fix_Side     = fix.Side()
fix_Price    = fix.Price()
fix_Account  = fix.Account()

def convertFixOrder(self, msg):
    clOrdID  = msg.getField( fix_ClOrdID ).getString()
    security = msg.getField( fix_Symbol ).getString()
    orderQty = int( msg.getField( fix_OrderQty ).getString() )
    side     = Side.byFixID[ int(msg.getField( fix_Side ).getString()) ]
    account  = msg.getField( fix_Account).getString()
    px       = msg.getField( fix_Price ).getValue()
    return Order( clOrdID, security, orderQty, side, account, px)

def convertFixExecution(self, msg):
    execType   = ExecType.byFixID[ int(msg.getField( fix.fix_ExecType ).getString() )]
    execID     = msg.getField( fix.fix_ExecID ).getString()
    clOrdID    = msg.getField( fix_ClOrdID ).getString()
    side       = Side.byFixID[ int(msg.getField( fix_Side ).getString()) ]
    lastShares = int(msg.getField( fix_LastShares).getString())
    security   = msg.getField( fix_Symbol).getString()
    lastPx     = float( msg.getField( fix_LastPx ).getString() )
    #isFill    = self.lastShares>0
    return Execution( execType, execID, clOrdID, side, lastShares, security. lastPx)

class OrderWrapper(pb.Copyable, pb.RemoteCopy, BusinessObject):
    version = 1
    def __init__(self,msg=None):
        self.px = 0.0
        if msg: # Need zero arg constructor for persistence
            try:
                # WTF Came here?
                pass
            except:
                print "bad msg %s" % msg
                traceback.print_exc()
                raise Exception()
            #self.account = account    

    def __repr__(self):
        return "OrderWrapper : " + " ".join( str(x) for x in [self.security, self.clOrdID,self.orderQty , self.side , self.px  ] )
        
pb.setUnjellyableForClass(OrderWrapper, OrderWrapper)
