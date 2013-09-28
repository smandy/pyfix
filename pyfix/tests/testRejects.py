#from pyfix.FIXProtocol import NormalMessageProcessing

import unittest
import re

from testFIXSession import SessionTester, fix
from twisted.internet import reactor

from pyfix.util.randomOrders import makeOrder, makeOrderWithMissingField, makeOrderWithIllegalField
from pyfix.tests.util import compileMessageOmitMandatoryHeaderField, \
     compileMessageOmitSequenceNumber, compileMessageNoPersist

from pyfix.FIXProtocol import NormalMessageProcessing, LoggedOut, GapProcessing, AcceptorAwaitingLogon

findCheckSumRe   = re.compile( "(.*10=)(\d+)(.*)" )
findBodyLengthRe = re.compile( "(.*9=)(\d+)(.*)"  )

from types import MethodType

class RejectTester(SessionTester):
    def setUp(self):
        SessionTester.setUp(self)
        self.ac.dispatchDict[ fix.OrderSingle ] = self.onAcceptorOrderSingle
        self.ic.dispatchDict[ fix.Reject ]      = self.onBusinessMessageReject
        self.businessMessageReject = None
        self.squirrelOrder = None
        self.acceptorSession.onIntegrityException = self.onAcceptorIntegrityException
        self.acceptorSession.onBusinessMessageReject = self.onAcceptorBusinessReject
        self.initiatorSession.compile_message = MethodType( compileMessageNoPersist,self.initiatorSession )

    #def onBusinessReject(self, e ):
    #    import random
    #    print "NMP Processing - scheduling logoff"
    ##    challenge = "TEST_%s" % str(str( random.random() )[2:15])
    #    testRequestId = pyfix.TestReqID( challenge )
    #    msg = pyfix.TestRequest( fields = [ testRequestId ] )
    #    strMsg = self.initiatorSession.compileMessage(msg)
    #    msgSeqNum = msg.getHeaderFieldValue( pyfix.MsgSeqNum)
    #    print ">>> %s %s %s" % (msgSeqNum, msg , strMsg)
    #    self.initiatorSession.protocol.transport.write( strMsg )
    #    reactor.callLater( 2, self.ic.protocol.factory.logoff )

    def onAcceptorBusinessReject(self, br):
        pass

    def onAcceptorIntegrityException(self, e):
        print "NMP Processing - scheduling logoff"
        import random
        challenge = "TEST_%s" % str(str( random.random() )[2:15])
        testRequestId = fix.TestReqID( challenge ) 
        msg = fix.TestRequest( fields = [ testRequestId ] )
        strMsg = self.initiatorSession.compile_message(msg)
        msgSeqNum = msg.get_header_field_value( fix.MsgSeqNum)
        print ">>> %s %s %s" % (msgSeqNum, msg , strMsg)
        self.initiatorSession.protocol.transport.write( strMsg )
        #reactor.callLater( 1, self.ic.protocol.factory.logoff )

    def initiatorStateChange(self, oldState, newState):
        print "ISC %s %s"  % (oldState, newState)
        if newState.__class__==NormalMessageProcessing:
            reactor.callLater(0.5, self.sendMyDodgyMessage)
        SessionTester.initiatorStateChange( self, oldState, newState)

    def sendMyDodgyMessage(self):
        self.assertTrue(self.initiatorSession.isConnected() )
        #myOrder = self._makeOrder( )
        #myOrder.dump()
        #trMsg = self.initiatorSession.compileMessage(myOrder, disableValidation = True )
        msg, strMsg = self._makeOrder()
        print "old : %s" % strMsg
        strMsg = self.mutate(strMsg)
        print "new : %s" % strMsg
        self.initiatorSession.protocol.transport.write( strMsg )

    def mutate(self, s):
        # Default -> NOOP
        return s

    def onBusinessMessageReject( self, protocol, msg, seq, possdup):
        print "onBusinessMessageReject %s" % msg.get_field_value( fix.Text )
        msg.dump()
        self.businessMessageReject = msg
        assert self.initiatorSession.isConnected()
        print "Scheduling logff"
        reactor.callLater( 1, self.initiatorSession.logoff )

    def onAcceptorOrderSingle(self, protocol, msg, seq, possdup):
        # Acceptor has received order - *INITIATOR* will now logout
        self.squirrelOrder = msg
        assert self.initiatorSession.isConnected()
        print "Scheduling logff"
        reactor.callLater( 1, self.initiatorSession.logoff )

################################################################################

class IntegrityTester( RejectTester ):
    def setUp(self):
        RejectTester.setUp( self )
        self.acceptorStateChanges = [  ( AcceptorAwaitingLogon, NormalMessageProcessing),
                                       ( NormalMessageProcessing, GapProcessing),
                                       ( GapProcessing, NormalMessageProcessing),
                                       ( NormalMessageProcessing, LoggedOut) ]

    def acceptorStateChange( self, oldState, newState ):
        RejectTester.acceptorStateChange( self, oldState, newState )
        if newState.__class__==NormalMessageProcessing and \
               self.timesAcceptorEnteredNormalMessageProcessing == 2:
            print "ASC Processing - scheduling logoff"
            reactor.callLater( 1, self.initiatorSession.logoff )
    
    def reportStatus(self):
        if self.squirrelOrder is not None:
            self.squirrelOrder.dump()
        print "Acceptor  integrity exception " , self.acceptorSession.lastIntegrityException
        print "Initiator integrity exception " , self.initiatorSession.lastIntegrityException
        self.assertFalse( self.businessMessageReject )
        self.assertTrue( self.acceptorSession.lastIntegrityException )
        self.result.callback( True )

class BusinessRejectTester( RejectTester ):
    def setUp( self ):
        RejectTester.setUp( self )
        self.acceptorStateChanges = [  ( AcceptorAwaitingLogon, NormalMessageProcessing),
                                       ( NormalMessageProcessing, LoggedOut) ]

    def reportStatus(self):
        if self.squirrelOrder is not None:
            self.squirrelOrder.dump()
        self.assertTrue( self.businessMessageReject )
        self.assertFalse( self.acceptorSession.lastIntegrityException )
        self.result.callback( True )

################################################################################

class BadCheckSum( IntegrityTester ):
    def mutate(self, strMsg):
        match = findCheckSumRe.match(strMsg)
        if match:
            print match.groups()
            groups = match.groups()
            newSum =  (int(groups[1])+1) % 256
            strSum = "%03d" % newSum
            strMsg = groups[0] + strSum + groups[2]
        return strMsg

class BadBodyLength( IntegrityTester ):

    def mutate(self, strMsg):
        match = findBodyLengthRe.match( strMsg )
        if match:
            print match.groups()
            groups = match.groups()
            newSum = (int(groups[1])+1) % 256
            strSum = "%d" % newSum
            strMsg = groups[0] + strSum + groups[2]
        return strMsg

class OmitSequenceNumber( IntegrityTester ):
    def setUp(self):
        IntegrityTester.setUp(self)
        #self.initiatorStateChanges = [ ( InitiatorAwaitingLogon, NormalMessageProcessing ),
        #                               ( NormalMessageProcessing, GapProcessing ),
        #                               ( GapProcessing, NormalMessageProcessing ),
        #                               ( NormalMessageProcessing, AwaitingLogout ),
        #                               ( AwaitingLogout, LoggedOut ) ]

        self.acceptorStateChanges = [  ( AcceptorAwaitingLogon, NormalMessageProcessing),
                                       ( NormalMessageProcessing, GapProcessing),
                                       ( GapProcessing, NormalMessageProcessing),
                                       ( NormalMessageProcessing, LoggedOut) ]

        #self.test_login.timeout = 10

    def onAcceptorIntegrityException(self, e):
        print "Acceptor integrity exception"
        e.msg.dump()
        import random
        challenge = "TEST_%s" % str(str( random.random() )[2:15])
        testRequestId = fix.TestReqID( challenge ) 
        msg = fix.TestRequest( fields = [ testRequestId ] )
        strMsg = self.initiatorSession.compile_message(msg)
        msgSeqNum = msg.get_header_field_value( fix.MsgSeqNum)
        print ">>> %s %s %s" % (msgSeqNum, msg , strMsg)
        self.initiatorSession.protocol.transport.write( strMsg )
        #print "Scheduling logoff"
        #reactor.callLater( 1, self.ic.protocol.factory.logoff)
    
    def _makeOrder(self):
        #emsg, asFix = IntegrityTester._makeOrder(self)
        msg = makeOrder(fix)
        import new
        # Slot in a new compile method for one invocation
        oldCompiler = self.initiatorSession.compile_message
        self.initiatorSession.compile_message = new.instancemethod( compileMessageOmitSequenceNumber,
                                                                   self.initiatorSession )
        strMsg = self.initiatorSession.compile_message(msg, disableValidation = True )
        # Return to original state
        self.initiatorSession.compile_message = oldCompiler
        return msg, strMsg
    
class OmitMandatoryField( BusinessRejectTester ):
    def _makeOrder(self):
        msg = makeOrderWithMissingField(fix)
        strMsg = self.initiatorSession.compile_message(msg, disableValidation = True )
        return msg, strMsg

class IncludeIllegalField( BusinessRejectTester ):
    def _makeOrder(self):
        msg =  makeOrderWithIllegalField(fix)
        strMsg = self.initiatorSession.compile_message(msg, disableValidation = True )
        return msg, strMsg

class OmitMandatoryHeaderField( BusinessRejectTester ):
##     def setUp(self):
##         BusinessRejectTester.setUp(self)
##         self.acceptorStateChanges = [  ( AcceptorAwaitingLogon, NormalMessageProcessing),
##                                        ( NormalMessageProcessing, LoggedOut) ]
##     def acceptorStateChange( self, oldState, newState ):
##         BusinessRejectTester.acceptorStateChange( self, oldState, newState )
##         if newState.__class__==NormalMessageProcessing and \
##                self.timesAcceptorEnteredNormalMessageProcessing == 2:
##             print "NMP Processing - scheduling logoff"
##             reactor.callLater( 1, self.ic.protocol.factory.logoff )
    
    def _makeOrder(self):
        msg, asFix = BusinessRejectTester._makeOrder(self)
        import new
        # Slot in a new compile method for one invocation
        oldCompiler = self.initiatorSession.compile_message
        self.initiatorSession.compile_message = new.instancemethod( compileMessageOmitMandatoryHeaderField,
                                                                   self.initiatorSession )
        strMsg = self.initiatorSession.compile_message(msg, disableValidation = True )
        self.initiatorSession.compile_message = oldCompiler
        return msg, strMsg

def test_suite():
    def s(test_class):
        return unittest.makeSuite( test_class)
    suite = unittest.TestSuite()
    testClasses = [ 
        BadBodyLength,
        BadCheckSum,
        OmitSequenceNumber,
        OmitMandatoryField,
        OmitMandatoryHeaderField,
        IncludeIllegalField,
        ]

##     testClasses = [ 
##         OmitMandatoryField
##         ]

    suite.addTests( [ s(x) for x in testClasses ] )
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite' )
    
    
        

        
    

      


