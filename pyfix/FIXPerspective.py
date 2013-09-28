from twisted.spread   import pb
from twisted.internet import reactor, task
from phroms.alladin.Discovery import Discoverable

class FIXPerspective(pb.Root):
    def __init__(self, sessionManager, description = "FIX Perspective"):
        self.sessionListeners = []
        self.sessionManager = sessionManager
        sessionManager.perspective = self
        addr = reactor.listenTCP(0 , pb.PBServerFactory( self ) )
        # Advertise the perspective on the network
        port = addr.getHost().port
        self.description = description
        data = { 'description' :  self.description,
                 #'domain'      : 'pyfix_perspective',
                 'port'        : port }
        d = Discoverable(data, domain = "pyfix_perspective")

        l = task.LoopingCall( self.updateListeners )
        reactor.callWhenRunning( l.start, 1)

    def remote_getSessionStatus(self):
        ret = []
        for session in self.sessionManager.sessions:
            ret.append( (session.sender, session.target, session.isConnected(), session.inMsgSeqNum, session.outMsgSeqNum) )
        return ret

    getSessionStatus = remote_getSessionStatus

    def remote_addSessionListener(self, listener):
        print "AddSessionListener %s" % listener
        listener.notifyOnDisconnect( lambda x: self.expunge(self.sessionListeners, listener) )
        self.sessionListeners.append( listener )

    def onExecution(self, source, execution):
        toIter = self.sessionListeners[:]
        for x in toIter:
            x.callRemote( 'onExecution', execution.toFix() ).addErrback( self.expunge, self.sessionListeners, x)

    def onOrder(self, source, order):
        toIter = self.sessionListeners[:]
        for x in toIter:
            x.callRemote( 'onOrder', order.toFix() ).addErrback( self.expunge, self.sessionListeners, x)
              
    def updateListeners( self ):
        print "UpdateListeners ( of which there are %s)" % len(self.sessionListeners)
        ss = self.getSessionStatus()
        toIter = self.sessionListeners[:]
        for x in toIter:
            x.callRemote( 'onSessionState', ss ).addErrback( self.expunge, self.sessionListeners, x )
      
    def expunge(self, l, victim):
        print "Expunging %s" % victim
        while victim in l:
            l.remove(victim)
                  
