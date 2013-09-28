import string
import random
from datetime import datetime

alpha = string.ascii_uppercase
extensions = [ 'MC','DE','L','OL','PA', 'HE' ]

symbols = []
for i in range( 100):
    sym = [ random.choice(alpha) for i in range(4) ]
    sym += '.'
    sym += random.choice( extensions)
    symbols.append( "".join( sym) )
quantities = [ 100,200,1000,1500,700 ]

clOrdID = 0
orderID = 0

def flipOrder( f, order):
    global orderID
    px = random.normalvariate( 100, 20)
    orderQty = order.getFieldValue( f.OrderQty )
    reply = f.ExecutionReport( fields = [
        f.OrderID('ORDER-%s' % orderID),
        order.getField( f.ClOrdID),
        f.ExecID('EXEC-%s' % orderID),
        f.ExecTransType.NEW,
        f.ExecType.NEW,
        f.OrdStatus.FILLED,
        order.getField( f.Symbol ),
        order.getField( f.Side ),
        f.LeavesQty(0),
        f.CumQty(orderQty),
        f.LastShares( orderQty),
        f.LastPx( px),
        f.AvgPx( px ) ] )
    orderID +=1
    return reply

def makeOrderWithMissingField(f, prefix='Order' ):
    global clOrdID
    side = random.choice( [ f.Side.BUY,
                            f.Side.SELL ] )
    ret = f.OrderSingle(fields = [ f.ClOrdID( "%s%s" % (prefix, clOrdID ) ),
                                   f.HandlInst('3'),
                                   f.Symbol( random.choice( symbols) ),
                                   #side,
                                   f.OrderQty(random.choice( quantities ) ),
                                   f.TransactTime( datetime.now() ),
                                   f.OrdType.MARKET]
                            )
    clOrdID+=1
    return ret

def makeOrderWithIllegalField(f, prefix='Order' ):
    global clOrdID
    side = random.choice( [ f.Side.BUY,
                            f.Side.SELL ] )
    ret = f.OrderSingle(fields = [ f.ClOrdID( "%s%s" % (prefix, clOrdID ) ),
                                   f.HandlInst('3'),
                                   f.Symbol( random.choice( symbols) ),
                                   f.ExecTransType.NEW, # <- THIS IS ILLEGAL
                                   f.OrderQty(random.choice( quantities ) ),
                                   f.TransactTime( datetime.now() ),
                                   f.OrdType.MARKET]
                            )
    clOrdID+=1
    return ret


def makeOrder(f, prefix='Order' ):
    global clOrdID
    side = random.choice( [ f.Side.BUY,
                            f.Side.SELL ] )
    ret = f.OrderSingle(fields = [ f.ClOrdID( "%s%s" % (prefix, clOrdID ) ),
                                   f.HandlInst('3'),
                                   f.Symbol( random.choice( symbols) ),
                                   side,
                                   f.OrderQty(random.choice( quantities ) ),
                                   f.TransactTime( datetime.now() ),
                                   f.OrdType.MARKET]
                            )
    clOrdID+=1
    return ret
