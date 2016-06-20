from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory as RCF, Factory

class AcceptorFactory(Factory, object):
    __slots__ = ['session_manager']

    initiator = False
    def __init__(self, session_manager, sessions):
        self.session_manager = session_manager
        self.sessions = sessions

    def add_session(self, id_tuple, session):
        assert not self.sessions.has_key(id_tuple)
        self.sessions[id_tuple] = session

    def buildProtocol(self, addr):
        acc_prot = self.session_manager.acceptorProtocol
        print "Build Protocol Instance %s %s" % \
            (addr, acc_prot)
        protocol = acc_prot(self.session_manager.fix)
        protocol.factory = self
        return protocol

    def get_session_for_message(self, msg):
        fix = self.session_manager.fix
        # They're sending to us so we flip the usual sender/target
        # only used for logon at the moment
        id_tuple = (msg.get_header_field_value(fix.TargetCompID),
                    msg.get_header_field_value(fix.SenderCompID))
        session = self.sessions.get(id_tuple, None)
        print "Looked up session %s got %s %s" % \
            (str(id_tuple), str(session), self.sessions)
        if not session or not session.want_to_be_logged_in:
            return None
        else:
            return session


class InitiatorFactory(RCF):
    #protocol = InitiatingFIXProtocol
    def __init__(self, session_manager, session, host, port):
        self.session_manager = session_manager
        self.session = session
        self.host = host
        self.port = port

    def logon(self):
        self.session.want_to_be_logged_in = True
        assert self.session.protocol is None
        return reactor.connectTCP(self.host, self.port, self)

    def buildProtocol(self, addr):
        print "Build Protocol Instance %s" % addr
        protocol = self.session_manager.initiatorProtocol(self.session_manager.fix)
        protocol.factory = self
        self.session.bind_protocol(protocol)
        return protocol

    def startedConnecting(self, connector):
        print 'Started to connect.'

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason
        print "Wanttobelogged in %s %s" % \
            (self, self.session.want_to_be_logged_in)
        if not self.session.want_to_be_logged_in:
            self.stopTrying()
        else:
            RCF.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason
        if not self.session.want_to_be_logged_in:
            self.stopTrying()
        else:
            RCF.clientConnectionFailed(self, connector, reason)


class SessionExistsException(Exception):
    pass
