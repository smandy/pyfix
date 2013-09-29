from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory, Factory


class AcceptorFactory(Factory):
    initiator = False

    def __init__(self, sm, sessions):
        self.sm = sm
        self.sessions = sessions

    def add_session(self, id_tuple, session):
        assert not self.sessions.has_key(id_tuple)
        self.sessions[id_tuple] = session

    def buildProtocol(self, addr):
        print "Build Protocol Instance %s %s" % (addr, self.sm.acceptorProtocol)
        p = self.sm.acceptorProtocol(self.sm.fix)
        p.factory = self
        return p

    def get_session_for_message(self, msg):
        f = self.sm.fix
        # They're sending to us so we flip the usual sender/target
        # only used for logon at the moment
        id_tuple = ( msg.get_header_field_value(f.TargetCompID),
                     msg.get_header_field_value(f.SenderCompID) )
        session = self.sessions.get(id_tuple, None)
        print "Looked up session %s got %s %s" % (str(id_tuple), str(session), self.sessions )
        if not session or not session.want_to_be_logged_in:
            return None
        else:
            return session


class InitiatorFactory(ReconnectingClientFactory):
    #protocol = InitiatingFIXProtocol
    def __init__(self, sm, session, host, port):
        self.sm = sm
        self.session = session
        self.host = host
        self.port = port

    def logon(self):
        self.session.want_to_be_logged_in = True
        assert self.session.protocol is None
        return reactor.connectTCP(self.host, self.port, self)

    def buildProtocol(self, addr):
        print "Build Protocol Instance %s" % addr
        p = self.sm.initiatorProtocol(self.sm.fix)
        p.factory = self
        self.session.bind_protocol(p)
        return p

    def startedConnecting(self, connector):
        print 'Started to connect.'

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason
        print "Wanttobelogged in %s %s" % (self, self.session.want_to_be_logged_in)
        if not self.session.want_to_be_logged_in:
            self.stopTrying()
        else:
            ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason
        if not self.session.wantToBeLoggedOn:
            self.stopTrying()
        else:
            ReconnectingClientFactory.clientConnectionFailed(self, connector,
                                                             reason)


class SessionExistsException(Exception):
    pass
