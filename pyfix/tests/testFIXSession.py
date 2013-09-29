import unittest
import tempfile
import os, shutil

from twisted.internet import reactor
from pyfix.FIXSpec     import parse_specification
from pyfix.FIXConfig import SessionConfig
from pyfix.FIXProtocol import InitiatorAwaitingLogon, AcceptorAwaitingLogon, \
     NormalMessageProcessing, AwaitingLogout, LoggedOut, GapProcessing
from pyfix.FIXApplication import FIXApplication
from pyfix.SessionFactory import SessionManager
from pyfix.util.randomOrders import makeOrder

fix = parse_specification( version= "FIX.4.2" )

from twisted.internet.defer import Deferred
from twisted.trial.unittest import TestCase

class InitiatorClient(FIXApplication):
    def __init__(self, onHeartbeat, onStateChange):
        FIXApplication.__init__(self, fix)
        self.dispatchDict = { fix.Heartbeat : self.onHeartbeat }
        self.heartBeatDelegate = onHeartbeat
        self.stateDelegate = onStateChange

    def onHeartbeat(self, *args):
        print "Heartbeat args : %s" % str(args)
        self.heartBeatDelegate(*args)

    def set_state(self, *args):
        self.stateDelegate(*args)

class SessionTester( TestCase ):
    #makeOrder = makeOrder

    def _makeOrder(self):
        msg =  makeOrder(fix)
        strMsg = self.initiatorSession.compile_message(msg, disableValidation = True )
        return msg, strMsg

    def setUp(self):
        for i in range(10):
            print 
        print "Setup"
        self.persistDir = tempfile.mktemp()
        os.mkdir(self.persistDir)

        self.initiatorState = None
        self.acceptorState  = None

        self.storedInitiatorStates = []
        self.storedAcceptorStates  = []

        self.ic = InitiatorClient( self.initiatorHeartbeat, self.initiatorStateChange)
        self.ac = InitiatorClient( self.acceptorHeartbeat,  self.acceptorStateChange)

        self.timesInitiatorEnteredNormalMessageProcessing = 0
        self.timesAcceptorEnteredNormalMessageProcessing  = 0

        self.sendConfig = SessionConfig( 'initiator',
                                         0,
                                         'localhost',
                                         'INITIATOR',
                                         'ACCEPTOR',
                                         os.path.join( self.persistDir, "sender" ), # Will be tempfile
                                         60,
                                         self.ic
                                          )
                                         
        self.receiveConfig = SessionConfig( 'acceptor',
                                            0,
                                            None,
                                            'ACCEPTOR',
                                            'INITIATOR',
                                            os.path.join(self.persistDir, "receiver" ),
                                            60,
                                            self.ac, 
                                            )
        
        config = [ self.sendConfig, self.receiveConfig ]
        self.sm = SessionManager( fix,
                                  config )

        # These are the series of state transitions the acceptor and initiator
        # will go through during test lifecycle
        self.acceptorStateChanges = [  ( AcceptorAwaitingLogon, NormalMessageProcessing),
                                       ( NormalMessageProcessing, LoggedOut) ]

        self.initiatorStateChanges = [ ( InitiatorAwaitingLogon, NormalMessageProcessing),
                                       ( NormalMessageProcessing, AwaitingLogout ),
                                       ( AwaitingLogout, LoggedOut) ]

        self.acceptorSession = self.sm.acceptorsByTuple.values()[0]
        self.initiatorSession = self.sm.initiatorsByTuple.values()[0]


    def initiatorHeartbeat(self, protocol, msg, seq, possdup):
        pass

    def acceptorHeartbeat(self, state, msg, seq, possdup):
        pass

    def initiatorStateChange(self, oldState, newState):
        if newState.__class__==NormalMessageProcessing:
            self.timesInitiatorEnteredNormalMessageProcessing +=1
        tup = ( oldState.__class__, newState.__class__ )
        print "Initiator state change %s->%s" % tup
        self.assertEqual(self.initiatorStateChanges[0],tup , "Got state change %s expected %s" % (str(tup), str(self.initiatorStateChanges[0] ) ) )
        self.storedInitiatorStates.append(tup)
        self.initiatorStateChanges = self.initiatorStateChanges[1:]
        self.initiatorState = newState.__class__
        self.checkIfDone()
        
    def acceptorStateChange(self, oldState, newState):
        if newState.__class__==NormalMessageProcessing:
            self.timesAcceptorEnteredNormalMessageProcessing +=1
        tup = ( oldState.__class__, newState.__class__ )
        self.storedAcceptorStates.append(tup)
        print "Acceptor state change %s->%s" % tup
        assert self.acceptorStateChanges[0]==tup, "Got state change %s expected %s" % (str(tup), str(self.acceptorStateChanges[0] ) )
        self.acceptorStateChanges = self.acceptorStateChanges[1:]
        self.acceptorState = newState.__class__
        self.checkIfDone()

    def checkIfDone(self):
        # Check we're done and that all the required state trnasitions
        # have taken place
        if not self.result.called:
            print "Check if done %s %s" % ( self.initiatorState, self.acceptorState)
            if self.initiatorState==LoggedOut and self.acceptorState==LoggedOut:
                assert len(self.initiatorStateChanges)==0, "Inititor state changes not complete"
                assert len(self.acceptorStateChanges)==0, "Acceptor state changes not complete"
                self.reportStatus()
                
    def reportStatus(self):
        self.assertFalse( self.acceptorSession.lastIntegrityException )
        self.result.callback( True )
        
    #def timeOut(self):
    #    if not self.result.called:
    #        print "Calling errback - haven't returned yet"
    #        self.result.errBack(False)
    def test_login(self):
        assert len( self.sm.acceptorFactories )==1
        assert len( self.sm.initiatorFactories ) == 1
        port, factory = self.sm.acceptorFactories.items()[0]
        self.listenPort = reactor.listenTCP(0, factory)
        portOpened = self.listenPort.getHost().port
        print "Port %s was opened by the acceptor - will connect to this" % self.listenPort
        factory = self.sm.initiatorFactories[0]
        factory.port = portOpened
        self.connectPort = factory.logon()
        self.result = Deferred()
        #self.timeOutCheck = reactor.callLater(5, self.timeOut)
        return self.result
    test_login.timeout = 10
    
    def tearDown(self):
        print "Teardown"
        self.listenPort.stopListening()
        #self.connectPort.stopConnecting()
        self.connectPort.disconnect()
        shutil.rmtree( self.persistDir)

class LoginLogoutTester(SessionTester):
    def initiatorHeartbeat(self, protocol, msg, seq, possdup):
        print "Getting logged off"
        self.initiatorSession.logoff()

class AcceptorGap(LoginLogoutTester):
    def setUp(self):
        SessionTester.setUp(self)
        p = self.acceptorSession.persister
        self.initiatorStateChanges = [ ( InitiatorAwaitingLogon, GapProcessing),
                                       ( GapProcessing, NormalMessageProcessing),
                                       ( NormalMessageProcessing, AwaitingLogout ),
                                       ( AwaitingLogout, LoggedOut ) ]
        myOrder = makeOrder(fix)
        self.acceptorSession.compile_message( myOrder )

    def initiatorStateChange(self, oldState, newState):
        SessionTester.initiatorStateChange( self, oldState, newState)
        if newState.__class__==NormalMessageProcessing:
            print "Scheduling logoff"
            reactor.callLater( 1, self.initiatorSession.logoff)

class InitiatorGap(LoginLogoutTester):
    def initiatorStateChange(self, oldState, newState):
        SessionTester.initiatorStateChange( self, oldState, newState)
        if newState.__class__==NormalMessageProcessing:
            print "Scheduling logoff"
            reactor.callLater( 1, self.initiatorSession.logoff)

    def initiatorHeartbeat(self, protocol, msg, seq, possdup):
        print "Getting logged off"
        #protocol.factory.logoff()

    def acceptorHeartbeat(self, protocol, msg, seq, possdup):
        pass

    def setUp(self):
        SessionTester.setUp(self)
        assert len(self.sm.initiatorsByTuple)==1
        p = self.initiatorSession.persister
        self.acceptorStateChanges = [ ( AcceptorAwaitingLogon, GapProcessing),
                                      ( GapProcessing, NormalMessageProcessing),
                                      ( NormalMessageProcessing, LoggedOut) ]

        myOrder = makeOrder(fix)
        self.initiatorSession.compile_message( myOrder )


def test_suite():
    def s(test_class):
        return unittest.makeSuite( test_class)
    suite = unittest.TestSuite()

    testClasses = [ AcceptorGap, InitiatorGap, LoginLogoutTester ]
    #testClasses = [ LoginLogoutTester ]
    #testClasses = [ AcceptorGap ]
    #testClasses = [ InitiatorGap ]

    suite.addTests( [ s(x) for x in testClasses ] )
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite' )
    
