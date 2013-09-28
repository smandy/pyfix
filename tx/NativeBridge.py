from datetime import datetime
from phroms.core.SecurityManager import Security

from phroms.messages.Order     import Order
from phroms.messages.Execution import Execution
from phroms.messages.enum.ExecType import ExecType
import  phroms.messages.enum.Side as Side

#from phroms.pyfix.FIXProtocol import FIXProtocol
from phroms.tx.SessionInfo import SessionInfo

class NativeConverter(object):
    def setFixSpec(self, fix):
        self.fixSpec = fix
        self.p2f_side = { Side.BUY  : fix.Side.BUY ,
                          Side.SELL : fix.Side.SELL }


    def convertLocalOrderToForeign(self, order, sessionInfo):
        f = self.fixSpec
        sec = order.security
        self.fix.OrderSingle( fields = [ f.ClOrdID( order.ClOrdID ),
                                                   f.HandlInst('3'),
                                                   f.Symbol( sec.ticker ),
                                                   self.p2f_side[ order.side ],
                                                   f.OrderQty( order.orderQty ),
                                                   f.TransactTime( datetime.now() ),
                                                   f.OrdType.MARKET ] )
        
    def convertLocalExecutionToForeign(self, orderState, execution):
        order = orderState.order
        #assert order.sender is not None
        c = order.clOrdID
        fix = self.fixSpec
        ret = self.fix.ExecutionReport(fields = [ fix.OrderID( order.clOrdID ), # XXX Proper orderID
                                                  fix.ExecID( self.execIDGen.makeExecID(c) ),
                                                  fix.ExecTransType.NEW,
                                                  fix.ExecType.NEW,
                                                  fix.OrdStatus.FILLED,
                                                  fix.Symbol( order.security.ticker ),
                                                  fix.Side( self.p2f_side[ order.side ] ),
                                                  fix.LeavesQty( 0 ),
                                                  fix.CumQty( orderState.cumQty ),
                                                  fix.LastShares( execution.lastShares ),
                                                  fix.LastPx( execution.lastPx ),
                                                  fix.AvgPx( orderState.avgPx() ) ] )

    def convertForeignOrderToLocal( self, msg, defaultAccount = None):
        f = self.fixSpec
        clOrdID     = msg.get_field_value( f.ClOrdID)
        strSecurity = msg.get_field_value( f.Symbol)
        orderQty    = msg.get_field_value( f.OrderQty)
        side = Side.byFixID[int( msg.get_field( f.Side ) )]
        if self.sm:
            sec = self.sm.lookupByFields( ['ticker','ric'], strSecurity)
            if not sec:
                print "Security Manager failed to lookup : %s" % sec
            else:
                sec = Security()
                sec.ticker = strSecurity
    
        strAccount = msg.get_field_value( f.Account)
        if strAccount is not None and strAccount!='':
            account  = self.accountManager.getByName( strAccount )
        else:
            assert defaultAccount is not None, "Can't resolve account : none specified and no default"
            # responsibility of pyfix engine to tag session-specific default to this account
            account = defaultAccount
        px = msg.get_field_value( f.Price )
        return Order( clOrdID, sec, orderQty, side, account, px)

    def convertForeignExecutionToLocal(self, msg):
        f = self.fixSpec
        execType = ExecType.byFixID[ int( msg.get_field_value( f.ExecType ) ) ]
        execID   = msg.get_field_value( f.ExecID )
        clOrdID  = msg.get_field_value( f.ClOrdID )
        side     = Side.Side.byFixID[ int( msg.get_field_value( f.Side ) ) ]
        lastShares = msg.get_field_value( f.LastShares)
        lastPx     = msg.get_field_value( f.LastPx )
        security = self.sm.getByFields( [ 'ticker','ric' ], msg.get_field_value( f.Symbol ) )
        return Execution( execType, execID, clOrdID, side, lastShares, security, lastPx)
        
class NativeBridge(object):
    def __init__(self, settings):
        self.settings = settings
        self.sessionsByID = {}
        pass

    def setOrderManager(self, om):
        self.om = om

    def setFixConverter(self, fc):
        self.fixConverter = fc

    def setSecurityManager(self, sm):
        self.securityManager = sm

    def setFixSpec(self, fix):
        self.fix = fix

    def setAccountManager(self, am):
        self.accountManager = am

    def onInit(self):
        assert self.om is not None
        assert self.fixConverter is not None
        assert self.fix      is not None
        
        for d in self.settings.all:
            t = ( d['SenderCompID'], d['TargetCompID'], d['BeginString'] )
            assert not self.sessionsByID.has_key(t)
            if d.has_key( 'DefaultAccount'):
                strAccount = d['DefaultAccount']
                account = self.accountManager.getByName( strAccount)
                print "Session account mapping %s -> %s" % (strAccount, account)
                assert account is not None, "Config problem, null account for session %s" % str( d)
            else:
                account = None

            # NB for quickfix we needed an explicit sesson id
            # for this guy we'll just use a tuple
            sid = ( d['BeginString'],
                    d['SenderCompID'],
                    d['TargetCompID'],
                    d.get( 'SessionQualifier', '') )
            #session = pyfix.Session.lookupSession( sid )
            self.sessionsByID[ t ] = SessionInfo( self, d, account, sid, None, t )

    def sendOrder(self, localOrder, sessionInfo ):
        foreignOrder = self.fixConverter.convertLocalOrderToForeign( localOrder, sessionInfo )
        strMsg = self.factory.compile_message( foreignOrder )
        msgSeqNum = localOrder.get_header_field_value( self.fix.MsgSeqNum)
        print "NB>> %s %s %s" % (msgSeqNum, foreignOrder, strMsg)
        self.transport.write( strMsg )
        
    def sendExecution(self, orderState, execution):
        assert execution.__class__==Execution
        foreignEx = self.fixConverter.convertLocalExecutionToForeign( orderState, execution )
        strMsg = self.factory.compile_message( foreignEx )
        #msgSeqNum = localOrder.getHeaderFieldValue( self.pyfix.MsgSeqNum)
        print "NB>> %s %s" % (foreignEx, strMsg)
        self.session.send( foreignEx )
                     

                                                              

        
        

            

