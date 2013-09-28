# $Header: /Users/andy/cvs/dev/python/phroms/twisted/fixConverters.py,v 1.10 2009-01-09 22:48:15 andy Exp $

import quickfix as fix
import  phroms.messages.enum.Side as Side
from phroms.messages.enum.ExecType import ExecType

from phroms.messages.Order     import Order
from phroms.messages.Execution import Execution

p2f_side = { Side.BUY  : fix.Side( str(Side.BUY.fixID) ),
             Side.SELL : fix.Side( str(Side.SELL.fixID) ) }

default_handlinst = fix.HandlInst(fix.HandlInst_AUTOMATED_EXECUTION_ORDER_PRIVATE)

fix_Symbol     = fix.Symbol()
fix_ClOrdID    = fix.ClOrdID()
fix_OrderQty   = fix.OrderQty()
fix_Side       = fix.Side()
fix_Price      = fix.Price()
fix_Account    = fix.Account()
fix_ExecType   = fix.ExecType()
fix_ExecID     = fix.ExecID()
fix_ClOrdID    = fix.ClOrdID()
fix_Side       = fix.Side()
fix_LastShares = fix.LastShares()
fix_Symbol     = fix.Symbol()
fix_LastPx     = fix.LastPx()

from phroms.core.SecurityManager import Security

import traceback

class FixConverter:
    def __init__(self):
        pass

    def setSecurityManager(self, sm):
        self.sm = sm

    def setAccountManager(self, am):
        self.accountManager = am

    def setExecIDGen(self, execIDGen):
        self.execIDGen = execIDGen

    def convertForeignOrderToLocal(self, msg, defaultAccount = None):
        clOrdID     = msg.getField( fix_ClOrdID ).getString()
        strSecurity = msg.getField( fix_Symbol ).getString()
        orderQty    = int( msg.getField( fix_OrderQty ).getString() )
        try:
            side     = Side.Side.byFixID[ int(msg.getField( fix_Side ).getString()) ]
        except:
            print "int failed trying ord"
            side     = Side.Side.byFixID[ ord(msg.getField( fix_Side ).getString()) ]

        # TODO - maybe the converter needs to be able to do it's own lookup for dodgy clients -
        # external brokers will quite happily do something wierd.... have a lookupSecurity method or something
        if self.sm:
            sec = self.sm.lookupByFields( ['ticker','ric' ] , strSecurity )
            if not sec:
                print "Security manager failed to lookup : %s" % sec
                return None
        else:
            sec = Security()
            sec.ticker = strSecurity

        strAccount = msg.getField( fix_Account).getString()
        if strAccount is not None and strAccount!='':
            account  = self.accountManager.getByName( strAccount )
        else:
            assert defaultAccount is not None, "Can't resolve account : none specified and no default"
            # responsibility of pyfix engine to tag session-specific default to this account
            account = defaultAccount
        px       = msg.getField( fix_Price ).getValue()
        return Order( clOrdID, sec, orderQty, side, account, px)

    def convertForeignExecutionToLocal( self, msg ):
        try:
            execType   = ExecType.byFixID[ int(msg.getField( fix_ExecType ).getString() )]
            execID     = msg.getField( fix_ExecID ).getString()
            clOrdID    = msg.getField( fix_ClOrdID ).getString()
            side       = Side.Side.byFixID[ int(msg.getField( fix_Side ).getString()) ]
            lastShares = int(msg.getField( fix_LastShares).getString())
            security   = self.sm.getByFields( ['ticker','ric'] ,  msg.getField( fix_Symbol).getString() )
            lastPx     = float( msg.getField( fix_LastPx ).getString() )
            #isFill    = self.lastShares>0
            return Execution( execType, execID, clOrdID, side, lastShares, security,  lastPx )
        except:
            traceback.print_exc()

    def convertLocalExecutionToForeign(self, orderState, execution):
        order = orderState.order
        assert order.sender is not None, "Order context not set on orderstate, can't identify session!"
        sessionInfo = order.sender
        ret = fix.Message()
        senderCompID, targetCompID, strBeginString = sessionInfo.tuple
        beginString = fix.BeginString()
        beginString.setString( strBeginString )
        tsf = fix.TransactTime()
        ret.setField( tsf )
        ret.getHeader().setField( fix.MsgType( fix.MsgType_ExecutionReport ) )
        ret.getHeader().setField( fix.SenderCompID( senderCompID ) )
        ret.getHeader().setField( fix.TargetCompID( targetCompID ) )
        ret.setField( fix.OrderQty( order.orderQty ) )
        ret.setField( fix.Price( order.px ) )
        ret.setField( fix.CumQty( orderState.cumQty ) )
        ret.setField( fix.AvgPx( orderState.avgPx() ) )
        c = orderState.order.clOrdID 
        ret.setField( fix.ClOrdID( c ) )
        ret.setField( fix.ExecID( self.execIDGen.makeExecID( c ) ) )
        ret.setField( fix.LastShares( execution.lastShares       ) )
        ret.setField( fix.LastPx(     execution.lastPx           ) )
        ret.setField( fix.Symbol( order.security.ticker          ) ) # Flavour :-)
        ret.setField( p2f_side[order.side] )
        ret.setField( fix.ExecTransType( fix.ExecTransType_NEW ) )
        if orderState.cumQty==order.orderQty:
            strExecType = fix.ExecType_FILL
        else:
            strExecType = fix.ExecType_PARTIAL_FILL
        ret.setField( fix.ExecType( strExecType ) )
        return ret

    def convertLocalOrderToForeign(self, order, sessionInfo):
        ret = fix.Message()
        beginString = fix.BeginString()
        #msgType     = pyfix.MsgType()
        senderCompID, targetCompID, strBeginString = sessionInfo.tuple
        beginString.setString( strBeginString )
        #transactTime = pyfix.UtcTimeStamp()
        #transactTime.setCurrent()
        sec = order.security
        tsf = fix.TransactTime( )
        ret.setField( tsf) 
        ret.getHeader().setField( beginString)
        ret.getHeader().setField( fix.MsgType( fix.MsgType_NewOrderSingle))
        ret.getHeader().setField( fix.SenderCompID( senderCompID) )
        ret.getHeader().setField( fix.TargetCompID( targetCompID ) ) 
        ret.setField( fix.OrdType(fix.OrdType_LIMIT))
        ret.setField( fix.Price( order.px ))
        ret.setField( fix.Symbol( sec.ticker) )
        ret.setField( fix.OrderQty(order.orderQty))
        ret.setField( fix.Account( order.account.name))
        ret.setField( fix.ClOrdID( order.clOrdID ))
        ret.setField( default_handlinst )
        ret.setField( p2f_side[order.side] )
        return ret        
