from phroms.messages.enum  import Side
from phroms.messages.enum import ExecType 
from phroms.messages.Execution     import Execution
from phroms.util.OrderState        import OrderState
from twisted.spread                import pb

class Order(pb.Copyable, pb.RemoteCopy):
    version = 1
    def __init__(self,
                 clOrdID  = None,
                 security = None,
                 orderQty = None,
                 side     = None,
                 account  = None,
                 broker   = None,
                 px = 0.0,
                 sender   = None ):
        self.clOrdID   = clOrdID
        self.security  = security
        self.orderQty  = orderQty
        self.side      = side
        self.account   = account
        self.broker    = broker
        self.px        = px
        self.sender    = sender
        #self.volume    = 0.0

    def getCopyableState(self):
        d = self.__dict__
        d['security'] = d['security'].ric
        d['account']  = d['account'].name
        d['broker']   = d['broker'].name

    def __repr__(self):
        return "Order: %s %s %s %s %s %s" % ( self.clOrdID, self.side.name, self.orderQty, self.security, self.px, self.account)

if __name__=='__main__':
    o1 = Order( 'order1', 'MSFT', 100, Side.BUY)
    o2 = Order( 'order2', 'MSFT', 200, Side.SELL)
    os1 = OrderState(o1)
    os2 = OrderState(o2)
    
    e1 = Execution( ExecType.PARTIAL_FILL, 'exec1', 'order1', Side.BUY,  50, 'MSFT', 40.25)
    e2 = Execution( ExecType.FILL,         'exec2', 'order1', Side.BUY,  50, 'MSFT', 41.0)
    e3 = Execution( ExecType.FILL,         'exec3', 'order2', Side.SELL, 100, 'MSFT', 41.0)
    e4 = Execution( ExecType.FILL,         'exec4', 'order2', Side.SELL, 50, 'MSFT',  40.5)
    e5 = Execution( ExecType.FILL,         'exec5', 'order2', Side.SELL, 50, 'MSFT',  41.5)

    #e6 = Execution()
    os1.apply(e1)
    os1.apply(e2)
    os2.apply(e3)
    os2.apply(e4)
    os2.apply(e5)

    #om = OrderManager()
    #a = Execution(
    #o = Order('wayhey', dwdw, qty, side, account, px)
    #o.__init__('waye, security, qty, side, account, px)
    #a = Execution()
    #a.
    #for o in [ o1, o2]:
    #    om.onOrder(o)
    #for e in [ e1, e2, e3, e4, e5]:
    #    om.onExecution(e)
    #
    #om.dump()

pb.setUnjellyableForClass( Order, Order)
