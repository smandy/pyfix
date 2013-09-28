from twisted.internet import reactor
import quickfix as fix
import threading

import fixConverters

class MessageFunctor:
    def __init__(self, target, wrapper, persister):
        self.target = target
        self.wrapper = wrapper
        self.persister = persister

    def __call__(self):
        self.target(self.wrapper)
        self.persister.writeObject(self.wrapper)

class DeferringApplication(fix.Application):
    """This is a class that will be called directly by quickfix on its own threads.
       not 100% certain this is the case but suspect it's best to squirrel away any data we need from these
       callbacks before the callback exists. i.e. are the pointers going to be valid once the callback
       exits ? Dunno"""

    def deferTo(self, obj):
        self.obj = obj
        self.msgType = fix.MsgType()
    
        # Moved to recoverymanager
        #self.recoveryMap = { Order      : self.onRecoveredOrder,
        #                     Execution  : self.onRecoveredExecution }
        
    def onCreate(self, sessionID):
        if self.obj:
            reactor.callFromThread( self.obj.onCreate, sessionID )

    def setPersister( self, persister):
        self.persister = persister

    def getMsgType(self, message):
        return message.getHeader().getField( self.msgType).getString()

    def onOrder(self, message, sessionID):
        # Need to have these gubbins wrappers since we can't process order/executino
        # on one thread and persist on another. Have to persist on the reactor thread
        # unfortunately.
        # if 'orderManager' in self.__dict__:
        #   self.orderManager.onOrder( OrderWrapper( message))
        if 'orderManager' in self.__dict__:
            wrapper = fixConverters.convertFixOrder(message)
            functor = MessageFunctor(self.orderManager.on_order, wrapper, self.persister)
            reactor.callFromThread(functor)

    def setOrderManager(self, om):
        self.orderManager = om

    def onExecution(self, message, sessionID ):
        if 'orderManager' in self.__dict__:
            wrapper = fixConverters.convertFixExecution(message)
            functor = MessageFunctor( self.orderManager.onExecution, wrapper, self.persister)
            reactor.callFromThread(functor)

    def onLogon( self, sessionID ):
        if self.obj:
            reactor.callFromThread( self.obj.onLogon, sessionID)

    def onLogout( self, sessionID ):
        if self.obj:
            reactor.callFromThread( self.obj.onLogout, sessionID)

    def toAdmin(self, message, sessionID):
        print "toAdmin"
        print message
        #reactor.callFromThread( self.obj.toAdmin, sessionID, pyfix.Message( message) )

    def fromAdmin(self, message, sessionID):
        pass

    def fromApp(self, message, sessionID):
        if self.obj:
            cheekyCopy = fix.Message(message)
            reactor.callFromThread( self.obj.fromApp, message.sessionID)
            
    def toApp(self, message, sessionID):
        pass
