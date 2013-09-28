# Don't know if this was particularly wise.
# One sessino manager which manages incoming and outgoing sessions
from collections import defaultdict
from twisted.internet import reactor
from pyfix.FIXParser import SynchronousParser
from pyfix.FIXProtocol import InitiatorFIXProtocol, FIXProtocol, AcceptorFIXProtocol
from pyfix.Factories import AcceptorFactory, SessionExistsException, InitiatorFactory
from pyfix.Session import Session

class SessionManager(object):
    protocolKlazz = FIXProtocol

    def __init__(self,
                 spec,
                 config,
                 initiatorProtocol=InitiatorFIXProtocol,
                 acceptorProtocol=AcceptorFIXProtocol):
    #senderCompID,
    #targetCompID):
        self.fix = spec
        self.config = config
        self.sessionLookup = {}

        self.initiatorProtocol = initiatorProtocol
        self.acceptorProtocol = acceptorProtocol

        self.beginString = self.fix.BeginString(self.fix.version)

        self.sessionByTuple = {}
        self.acceptorsByTuple = {}
        self.initiatorsByTuple = {}

        self.acceptorsByPort = defaultdict(lambda: {})
        self.initiatorFactories = []
        self.acceptorFactories = {}
        self.sessions = []

        self.perspective = None

        for s in config:
            idTuple = ( s.sender, s.target )
            session = Session(self, spec, s)
            self.sessions.append(session)
            self.sessionByTuple[idTuple] = idTuple
            if s.connectionType == 'initiator':
                #session.host = s.host
                #session.port = s.port
                f = InitiatorFactory(self, session, s.host, s.port)
                session.factory = f
                self.initiatorFactories.append(f)
                self.initiatorsByTuple[idTuple] = session
            else:
                assert s.connectionType == 'acceptor', "Must be acceptor or initiator"
                self.acceptorsByPort[s.port][idTuple] = session
                self.acceptorsByTuple[idTuple] = session
            self.sessionByTuple[idTuple] = session

        for port, sessionMap in self.acceptorsByPort.items():
            af = AcceptorFactory(self, sessionMap)
            self.acceptorFactories[port] = af
        self.sp = SynchronousParser(self.fix)

    def addSession(self, sessionConfig, initiateImmediately=True):
        ### FIXME XXX Untested - i.e. UN*RUN* - check this works
        idTuple = ( sessionConfig.sender, sessionConfig.target)
        if self.sessionByTuple.has_key(idTuple):
            raise SessionExistsException()
        session = Session(self, self.fix, sessionConfig)
        if sessionConfig.connectionType == 'initiator':
            f = InitiatorFactory(self, session, sessionConfig.host, sessionConfig.port)
            session.factory = f
            self.initiatorFactories.append(f)
            self.initiatorsByTuple[idTuple] = session

            if initiateImmediately:
                f.logon()
        else:
            assert sessionConfig.connectionType == 'acceptor', "Must be acceptor or initiator"
            # XXX Note to self. I'm populating these structures so as to keep them consistent
            # but might make sense to figure out which structures are 'scaffolding' for the
            # initial session creation and which need to be 'maintained'
            self.acceptorsByPort[sessionConfig.port][idTuple] = session
            self.acceptorsByTuple[idTuple] = session

            # If we're adding an acceptor to a port that's already listeneing
            # it's enough to just add it to the config.. when someone asks to logon
            # the structure will be there :-)
            if not self.acceptorsByPort.has_key(sessionConfig.port):
                sessionMap = {idTuple: session}
                af = AcceptorFactory(self, sessionMap)
                self.acceptorFactories[sessionConfig.port] = af
            else:
                self.acceptorFactories[sessionConfig.port].add_session(session)

        self.sessionByTuple[idTuple] = session

        for port, sessionMap in self.acceptorsByPort.items():
            af = AcceptorFactory(self, sessionMap)
            self.acceptorFactories[port] = af

    def getConnected(self):
        for port, factory in self.acceptorFactories.items():
            print "Starting acceptor %s" % port
            port = reactor.listenTCP(port, factory)
            print "Port is %s" % port.getHost().port

        for f in self.initiatorFactories:
            print "Startign initiator %s %s %s" % ( f.host, f.port, f)
            f.logon()
            #reactor.connectTCP( f.host, f.port, f)

    # Utility for the remote interfaces
    def dump(self):
        print "INITIATORS"
        print "========="
        for x in self.initiatorsByTuple.items():
            print x

        print "ACCEPTORS"
        print "========="
        for x in self.acceptorsByTuple.items():
            print x

