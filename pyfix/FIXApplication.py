from pyfix.FIXParser import SynchronousParser, ParseException
import cPickle

class RecoveryException(Exception):
    pass

class FIXApplication(object):
    def __init__(self, fix):
        self.state       = None
        self.protocol    = None
        self.session     = None
        self.perspective = None
        self.fix      = fix
        self.dispatchdict = { fix.Heartbeat   : self.noop,
                              fix.TestRequest : self.noop,}
        self.recoveryDict = { fix.Heartbeat   : self.noop }
        self.inRecovery = False
        #self.perspective = None

    def noop(self, *args):
        pass
 
    def setSession(self, session):
        assert self.session is None
        self.session = session

    def setProtocol(self, protocol):
        print "onProtocol %s" % protocol
        assert protocol.session == self.session, "%s vs %s" % (protocol.session, self.session)
        self.protocol = protocol

    def set_state(self, oldState, newState):
        self.state = newState

    def onMessage( self, protocol, msg, seq, possDup):
        assert protocol==self.protocol, "%s vs %s" % ( protocol, self.protocol)
        msgKlazz = msg.__class__
        if self.dispatchdict.has_key( msgKlazz ):
            self.dispatchdict[msgKlazz]( protocol, msg, seq, possDup)
        else:
            print "Warning unmapped message %s" % msgKlazz

    def recoveredMessage(self, msg):
        klazz = msg.__class__
        if self.recoveryDict.has_key( klazz ):
            self.recoveryDict[ klazz ](msg)
        else:
            print "Unmapped recovery message %s" % klazz

    def onRecoveryDone(self):
        pass

    def recover(self):
        assert self.session is not None
        self.inRecovery = True
        sp = SynchronousParser( self.fix )
        c = self.session.persister.ledger.cursor()
        while True:
            d = c.next()
            if not d:
                break
            try:
                msg, _,_ = sp.parse( d[1] )
                self.recoveredMessage( msg )
            except ParseException:
                obj = cPickle.loads( d[1] )
                self.recoveredMessage( msg )
        c.close()
        self.onRecoveryDone()
        self.inRecovery = False
