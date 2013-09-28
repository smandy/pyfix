import unittest

from twisted.internet import reactor
from pyfix.FIXProtocol import NormalMessageProcessing, LoggedOut
import pyfix.util.randomOrders as randomOrders

from testFIXSession import SessionTester, fix

from twisted.internet.base import DelayedCall
DelayedCall.debug = True
from pprint import pprint as pp

# NOddy Change

class IntermittentGap( SessionTester ):
    gapFrequency = 10
    maxOrders = 100
    delay = 0.02

    def test_login(self):
        return SessionTester.test_login(self)
    test_login.timeout = 40
    
    def setUp(self):
        SessionTester.setUp(self)
        self.sendingOrders = False
        self.ac.dispatchDict[ fix.OrderSingle ] = self.onAcceptorOrder
        self.orders = []
        self.ordersByClOrdID = {}
        randomOrders.orderID = 0
        randomOrders.clOrdID = 0
        self.acceptorStateChanges = []
        self.lastID = None

    def onAcceptorOrder(self, *args):
        msg = args[1]
        clOrdID = msg.getFieldValue( fix.ClOrdID )
        print "OnAcceptorOrder : %s %s" % (clOrdID, str(args) )
        idNum = int( clOrdID[5:] ) # i.e. OrderXXX strip out the xxx
        self.assertFalse( self.ordersByClOrdID.has_key( idNum) )
        self.checkIDValid( idNum)
        self.lastID = idNum
        self.ordersByClOrdID[idNum] = ( msg, self.acceptorState)

    def checkIDValid(self, idNum):
        self.assertTrue( self.lastID==None or idNum==self.lastID+1, "%s vs %s" % (self.lastID, idNum) )

    def initiatorStateChange(self, oldState, newState):
        print "Initiator state %s->%s" % (oldState, newState)
        if newState.__class__==NormalMessageProcessing and not self.sendingOrders:
            self.sendingOrders = True
            reactor.callLater( 0, self.doOrder, 0)
        else:
            self.initiatorState = newState.__class__
            self.checkIfDone()

    def acceptorStateChange(self, oldState, newState):
        print "Acceptor state %s->%s" % (oldState, newState)
        self.acceptorState = newState.__class__
        self.acceptorStateChanges.append( (oldState, newState) )
        self.checkIfDone()

    def shouldPersist(self, counter):
        return True

    def shouldSend( self, counter):
        return counter % self.gapFrequency != 0
                
    def doOrder(self, counter):
        s = "DoOrder seq=%s" % self.initiatorSession.outMsgSeqNum
        print s,
        myOrder = randomOrders.makeOrder(fix)
        fixMsg = self.initiatorSession.compileMessage( myOrder, persist = self.shouldPersist(counter) )
        if self.shouldSend(counter):
            self.initiatorSession.protocol.transport.write(fixMsg)
            print "...sent"
        else:
            print "Persisted but not sending ( should cause a gap )"

        if counter>=self.maxOrders:
            reactor.callLater( 1, self.logoffInitiator )
        else:
            reactor.callLater( self.delay, self.doOrder, counter + 1 )

    def logoffInitiator(self):
         self.initiatorSession.logoff()
         
    def checkIfDone(self):
        # Check we're done and that all the required state trnasitions
        # have taken place
        if not self.result.called:
            print "Check if done %s %s" % ( self.initiatorState, self.acceptorState)
            if self.initiatorState==LoggedOut and self.acceptorState==LoggedOut:
                #pp(self.ordersByClOrdID)
                print "Acceptor states"
                for x in self.acceptorStateChanges:
                    print x
                self.reportStatus()

class GapTwo( IntermittentGap ):
    maxOrders    = 100
    gapFrequency = 2

class HugeGap( IntermittentGap ):
    maxOrders = 100
    def shouldSend( self, counter):
        return counter>100 and counter<150

class AnotherGap( IntermittentGap ):
    maxOrders = 100
    def shouldSend( self, counter):
        return counter>100 and counter<150

class BadPersistence(IntermittentGap):
    maxOrders = 100
    def setUp(self):
        IntermittentGap.setUp(self)
        self.droppedIds = {}

    def shouldSend(self, counter):
        return counter % 4 == 0 
        #return self.shouldPersist(counter)

    def checkIDValid(self, idNum):
        print self.droppedIds
        #while self.droppedIds.has_key(idNum):
        #    del self.droppedIds[idNum]
        #    idNum += 1
        #self.assertTrue( self.lastID==None or ( self.droppedIds.has_key(idNum-1) or idNum==self.lastID+1), "%s vs %s %s" % (self.lastID, idNum, str(self.droppedIds) ) )

    def shouldPersist(self, counter):
        ret = (counter % 2 == 0)
        if not ret:
            self.droppedIds[counter] = None
        return ret
    
    def reportStatus(self):
        print "Dropped : "
        pp(self.droppedIds)
        for i in range( 1, self.maxOrders):
            self.assertTrue( self.ordersByClOrdID.has_key( i ) or self.droppedIds.has_key( i ) , "Bad value %s" % i )
        IntermittentGap.reportStatus(self)
            
import random

class RandomDropper( IntermittentGap ):
    maxOrders = 100
    def shouldSend( self, count):
        return random.choice( [ True, True, True , False  ] )

class DutyCycleDropper( IntermittentGap ):
    period = 10
    halfPeriod = 5
    maxOrders = 200
    def sholdSend(self, count):
        return divmod( count , self.period )[1]/self.halfPeriod>0

class DutyCycleDropper2( DutyCycleDropper ):
    period = 10
    halfPeriod = 2

class DutyCycleDropper3( DutyCycleDropper ):
    period = 10
    halfPeriod = 8

class DutyCycleDropper4( DutyCycleDropper ):
    maxOrders = 300
    delay = 0.0001
    period = 10
    halfPeriod = 5

class VeryBadConnection( IntermittentGap ):
    delay = 0.002
    """Only send every fifth order - this should never happen but we should be able to recover"""
    maxOrders = 200
    def shouldSend( self, count):
        return random.choice( [ False, False, False, False, True  ] )

class BadConnection( IntermittentGap ):
    delay = 0.005
    """Only send every fifth order - this should never happen but we should be able to recover"""
    maxOrders = 100
    def shouldSend( self, count):
        return random.choice( [ False, True  ] )

def test_suite():
    def s(test_class):
        return unittest.makeSuite( test_class)
    suite = unittest.TestSuite()
    
    testClasses = [ VeryBadConnection,
                    BadConnection,
                    RandomDropper,
                    IntermittentGap,
                    DutyCycleDropper,
                    DutyCycleDropper2,
                    DutyCycleDropper3,
                    DutyCycleDropper4,
                    GapTwo,
                    HugeGap,
                    BadPersistence ]
    
    #testClasses = [ BadPersistence ]
    suite.addTests( [ s(x) for x in testClasses ] )
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite' )
    
