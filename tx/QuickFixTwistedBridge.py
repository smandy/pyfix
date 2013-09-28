import quickfix as fix
from twisted.internet import reactor
from pprint import pprint as pp
from phroms.util.attr_setter import attr_setter
import fixConfig
#from phroms.messages.Execution import Execution
from SessionInfo import SessionInfo

class DeferringApplication( fix.Application ):
    """This is a class that will be called directly by quickfix on its own threads.
       not 100% certain this is the case but suspect it's best to squirrel away any data we need from these
       callbacks before the callback exists. i.e. are the pointers going to be valid once the callback
       exits ? Dunno"""
    __metaclass__, attrs = attr_setter, [ 'persister',
                                          'orderManager'
                                          ]
    def deferTo(self, obj):
        self.obj = obj
        
    def onCreate(self, sessionID):
        # This will be a dodgy one - hopefully sessions are only created when the thread is started
        self.checkObj()
        reactor.callFromThread( self.obj.onCreate, sessionID )

    def onLogon( self, sessionID ):
        self.checkObj()
        reactor.callFromThread( self.obj.onLogon, sessionID)

    def onLogout( self, sessionID ):
        self.checkObj()
        reactor.callFromThread( self.obj.on_logout, sessionID)

    def toAdmin(self, message, sessionID):
        pass
        #print "toAdmin"

    def fromAdmin(self, message, sessionID):
        pass

    def fromApp(self, message, sessionID):
        self.checkObj()
        cheekyCopy = fix.Message(message)
        reactor.callFromThread( self.obj.fromApp, cheekyCopy, sessionID)
            
    def toApp(self, message, sessionID):
        pass

    def checkObj(self):
        assert self.obj is not None, "Message recieved and don't have anything to defer to"

# XXX Hmmm.... do I need one of these for each type of session
# Guessnot
# Data pertaining to a session
# Don't know what I'll need so will just slap in everything


def sessionIDTuple(sid):
    return ( sid.getSenderCompID().getString(),
             sid.getTargetCompID().getString(),
             sid.getBeginString().getString()) 


class QuickFixTwistedBridge(object):
    __metaclass__, attrs = attr_setter, [ 'fixConverter',
                                          'accountManager', 
                                          'orderManager' ]
   
    def __init__(self, settings ):
        # bit pants - settings we need so we know if we're an acceptor
        # or initiator, 
        self.settings = settings

        # Rename this method fromYaml takes a dictionary - duh!
        self.config = fixConfig.fromYaml( settings )
        self.sessionsByID = {}
        self.loggedIn     = {}
        self.started      = False
        #self.messagesBySession = {}
        self.dispatchMap = { fix.MsgType_EXECUTION_REPORT  : self.onExecution,
                             fix.MsgType_ORDER_SINGLE      : self.onOrder }
        #self.sessions = {}
        self.orderManager = None
        self.fixConverter = None
        self.initiator = None
        self.started   = False
        #self.tupleToSid = {}
        
        self.initiatorMap = {
            'initiator' : fix.SocketInitiator,
            'acceptor'  : fix.SocketAcceptor
            }

        self.InitiatorKlazz = self.initiatorMap[ settings['default']['ConnectionType'] ]
        self.logFactory   = fix.FileLogFactory( self.config )
        self.storeFactory = fix.FileStoreFactory( self.config)
        self.deferringApplication = DeferringApplication()
        self.deferringApplication.deferTo( self )

    # Get accounts from the account manager
    def onInit(self):
        # At this point account manager etc should have been created
        # we don't have pyfix sessions created yet so need to wait for them to arrive via
        # the onCreate method of pyfix.Application
        print "Bridge account"
        for d in self.settings['sessions']:
            t = ( d['SenderCompID'], d['TargetCompID'], d['BeginString'] )
            assert not self.sessionsByID.has_key(t)
            if d.has_key( 'DefaultAccount'):
                strAccount = d['DefaultAccount']
                account = self.accountManager.getByName( strAccount)
                print "Session account mapping %s -> %s" % (strAccount, account)
                assert account is not None, "Config problem, null account for session %s" % str( d)
            else:
                account = None
            sid = fix.SessionID( d['BeginString'],
                                 d['SenderCompID'],
                                 d['TargetCompID'],
                                 d.get( 'SessionQualifier', '') )
            #session = pyfix.Session.lookupSession( sid )
            self.sessionsByID[ t ] = SessionInfo( self, d, account, sid, None, t )

    def getQuickFixApplication(self):
        return self.deferringApplication

    def makeInitiator(self):
        assert self.initiator is None, "Initiator created already?"
        self.initiator = self.InitiatorKlazz( self.deferringApplication,
                                              self.storeFactory,
                                              self.config,
                                              self.logFactory )
        return self.initiator

    def start(self):
        assert not self.started , "Bridge already started!"
        assert self.initiator is None, "Initiator already created?"
        self.makeInitiator()
        self.initiator.start()

    def __del__(self):
        if self.started:
            self.stop()

    def stop(self):
        assert self.started, "Can't stop before start"
        self.initiator.stop()

    def onOrder(self, message, sessionID):
        # Need to have these gubbins wrappers since we can't process order/executino
        # on one thread and persist on another. Have to persist on the reactor thread
        # unfortunately.
        # if 'orderManager' in self.__dict__:
        #   self.orderManager.onOrder( OrderWrapper( message))
        if self.orderManager:
            sidTuple = sessionIDTuple( sessionID)
            assert self.sessionsByID.has_key( sidTuple )
            defaultAccount = self.sessionsByID[sidTuple].defaultAccount
            order = self.fixConverter.convertForeignOrderToLocal(message, defaultAccount = defaultAccount)
            order.sender = self.sessionsByID[sidTuple]
            self.orderManager.on_order( order )
            
            # functor = MessageFunctor(self.orderManager.onOrder, wrapper, self.persister)

    def onExecution(self, message, sessionID ):
        if self.orderManager:
            execution = self.fixConverter.convertForeignExecutionToLocal(message)
            print "Execution is %s" % execution
            self.orderManager.on_execution( execution )
            # OrderManager should persist ( or not)

    def sendOrder(self, localOrder ):
        # XXX TODO - proper routing - by destination?
        si = [ v for q,v in self.sessionsByID.items() if q[1]=='EXECUTOR' ][0]
        foreignOrder = self.fixConverter.convertLocalOrderToForeign( localOrder, si )
        print "Sending to session %s" % si
        si.session.send(foreignOrder)

    def onCreate(self, sessionID):
        #self.sessionsByID[sessionID] = [ pyfix.Session.lookupSession(sessionID) , None ]
        print "onCreate %s %s" % (sessionID, sessionIDTuple( sessionID) )
        #sidToSession
        # Looks like session ids aren't pyhtonically equal inbetween
        # calls - pull out a sessionid tuple instead
        sidTuple = sessionIDTuple( sessionID )
        assert self.sessionsByID.has_key(sidTuple)
        session = fix.Session.lookupSession( sessionID )
        self.sessionsByID[sidTuple].session = session
        #self.sessionsByID[sidTuple] = session
        #self.loggedIn[sidTuple] = False

    def onLogon(self, sid):
        sidTuple = sessionIDTuple( sid )  
        print "onLogon %s" % str(sidTuple)
        assert self.sessionsByID.has_key( sidTuple )
        self.loggedIn[ self.sessionsByID[sidTuple] ] = True
        #self.sessionsById[sessionID] = (True, pyfix.Session.lookupSession(sessionID) )
	
    def onLogout(self, sid):
        sidTuple = sessionIDTuple( sid )
        pp( self.sessionsByID )
        print "onLogout %s" % str(sidTuple)
        print self.sessionsByID
        assert self.sessionsByID.has_key( sidTuple )
        self.loggedIn[self.sessionsByID[sidTuple] ] = False
	
    def fromAdmin(self, sessionID, message):
        print "noddy fromAdmin : %s %s" % (message,sessionID)
        ts = fix.SendingTime()
        message.getHeader().get_field(ts)
        print "TIMESTAMP IS %s" % ts.getValue()
        msgType =fix.MsgType()
        message.getHeader().get_field( msgType )
        if msgType.getValue()==fix.MsgType_Reject:
            print "REJECT : %s" % message
        else:
            print "Message type is %s" % msgType.getValue()

    def getMsgType(self, message):
        return message.getHeader().get_field( fix.MsgType() ).getString()
        
    def toApp(self, sessionID, message):
        pass
        #print "noddy toApp %s %s" % (sessionID, message)
        #if not self.messagesBySession.has_key(sessionID):
        #    self.messagesBySession[sessionID] = []
        #self.messagesBySession[sessionID].append( message)
	
    def fromApp(self, message, sessionID):
        #self.messagesBySession[sessionID].append( message)
        msgType = self.getMsgType(message)
        if self.dispatchMap.has_key(msgType):
            self.dispatchMap[msgType](message, sessionID)


class MessageFunctor:
    def __init__(self, target, wrapper, persister):
        self.target = target
        self.wrapper = wrapper
        self.persister = persister

    def __call__(self):
        self.target(self.wrapper)
        self.persister.writeObject(self.wrapper)


